import React, { useState, useEffect } from 'react';
import './Export.css';

function Export() {
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [dateRange, setDateRange] = useState({
    type: 'last30', // 'last30', 'last90', 'custom'
    startDate: '',
    endDate: ''
  });
  const [exportFormat, setExportFormat] = useState('csv');
  const [previewData, setPreviewData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState('');

  const categories = [
    { id: 'sleep', name: 'Sleep Data', description: 'Hours of sleep per night' },
    { id: 'symptoms', name: 'Symptoms', description: 'Daily symptom tracking' },
    { id: 'mood', name: 'Mood', description: 'Daily mood ratings (1-5 scale)' },
    { id: 'vital_signs', name: 'Vital Signs', description: 'Heart rate and other vitals' }
  ];

  // Handle category selection
  const handleCategoryChange = (categoryId) => {
    setSelectedCategories(prev => {
      if (prev.includes(categoryId)) {
        return prev.filter(id => id !== categoryId);
      } else {
        return [...prev, categoryId];
      }
    });
  };

  // Handle date range changes
  const handleDateRangeChange = (type, value) => {
    if (type === 'type') {
      setDateRange(prev => ({ ...prev, type: value }));
      
      // Auto-set dates for preset ranges
      if (value === 'last30') {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 30);
        setDateRange(prev => ({
          ...prev,
          startDate: start.toISOString().split('T')[0],
          endDate: end.toISOString().split('T')[0]
        }));
      } else if (value === 'last90') {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 90);
        setDateRange(prev => ({
          ...prev,
          startDate: start.toISOString().split('T')[0],
          endDate: end.toISOString().split('T')[0]
        }));
      }
    } else {
      setDateRange(prev => ({ ...prev, [type]: value }));
    }
  };

  // Preview export data
  const handlePreview = async () => {
    if (selectedCategories.length === 0) {
      setExportStatus('Please select at least one category to preview.');
      return;
    }

    setIsLoading(true);
    setExportStatus('');
    setPreviewData(null); // Clear previous preview

    try {
      const response = await fetch('http://localhost:5001/api/export/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categories: selectedCategories,
          start_date: dateRange.startDate || null,
          end_date: dateRange.endDate || null
        })
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
        setExportStatus(`✅ Preview loaded: ${data.total_records} records found.`);
      } else {
        const error = await response.json();
        setExportStatus(`Error: ${error.error || 'Failed to load preview'}`);
        setPreviewData(null);
      }
    } catch (error) {
      setExportStatus(`Error: ${error.message || 'Failed to connect to server'}`);
      setPreviewData(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Download export file
  const handleExport = async () => {
    if (selectedCategories.length === 0) {
      setExportStatus('Please select at least one category to export.');
      return;
    }

    setIsLoading(true);
    setExportStatus('Preparing export...');

    try {
      const response = await fetch('http://localhost:5001/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categories: selectedCategories,
          start_date: dateRange.startDate || null,
          end_date: dateRange.endDate || null,
          format: exportFormat
        })
      });

      if (response.ok) {
        // Get filename from response headers
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition 
          ? contentDisposition.split('filename=')[1].replace(/"/g, '')
          : `health_data_export.${exportFormat}`;

        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setExportStatus('✅ File downloaded successfully!');
        
        // Log export event (for auditing)
        console.log('Export completed:', {
          categories: selectedCategories,
          dateRange,
          format: exportFormat,
          timestamp: new Date().toISOString()
        });
      } else {
        const error = await response.json();
        setExportStatus(`Error: ${error.error}`);
      }
    } catch (error) {
      setExportStatus(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize with last 30 days
  useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setDateRange(prev => ({
      ...prev,
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0]
    }));
  }, []);

  return (
    <div className="export-container">
      <div className="export-header">
        <h1>Data Export</h1>
        <p>Export your health data for analysis, backup, or sharing with healthcare providers.</p>
      </div>

      <div className="export-content">
        {/* Category Selection */}
        <div className="export-section">
          <h2>1. Select Data Categories</h2>
          <div className="category-grid">
            {categories.map(category => (
              <div 
                key={category.id}
                className={`category-card ${selectedCategories.includes(category.id) ? 'selected' : ''}`}
                onClick={() => handleCategoryChange(category.id)}
              >
                <div className="category-checkbox">
                  <input 
                    type="checkbox"
                    checked={selectedCategories.includes(category.id)}
                    onChange={() => handleCategoryChange(category.id)}
                  />
                </div>
                <div className="category-info">
                  <h3>{category.name}</h3>
                  <p>{category.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Date Range Selection */}
        <div className="export-section">
          <h2>2. Choose Time Window</h2>
          <div className="date-range-options">
            <div className="preset-options">
              <label>
                <input 
                  type="radio"
                  name="dateRange"
                  value="last30"
                  checked={dateRange.type === 'last30'}
                  onChange={(e) => handleDateRangeChange('type', e.target.value)}
                />
                Last 30 days
              </label>
              <label>
                <input 
                  type="radio"
                  name="dateRange"
                  value="last90"
                  checked={dateRange.type === 'last90'}
                  onChange={(e) => handleDateRangeChange('type', e.target.value)}
                />
                Last 90 days
              </label>
              <label>
                <input 
                  type="radio"
                  name="dateRange"
                  value="custom"
                  checked={dateRange.type === 'custom'}
                  onChange={(e) => handleDateRangeChange('type', e.target.value)}
                />
                Custom range
              </label>
            </div>

            {dateRange.type === 'custom' && (
              <div className="custom-date-inputs">
                <div className="date-input">
                  <label>Start Date:</label>
                  <input 
                    type="date"
                    value={dateRange.startDate}
                    onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
                  />
                </div>
                <div className="date-input">
                  <label>End Date:</label>
                  <input 
                    type="date"
                    value={dateRange.endDate}
                    onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Export Format */}
        <div className="export-section">
          <h2>3. Select Export Format</h2>
          <div className="format-options">
            <label>
              <input 
                type="radio"
                name="format"
                value="csv"
                checked={exportFormat === 'csv'}
                onChange={(e) => setExportFormat(e.target.value)}
              />
              CSV (Excel compatible)
            </label>
            <label>
              <input 
                type="radio"
                name="format"
                value="pdf"
                checked={exportFormat === 'pdf'}
                onChange={(e) => setExportFormat(e.target.value)}
              />
              PDF (Printable report)
            </label>
          </div>
        </div>

        {/* Preview and Export Actions */}
        <div className="export-section">
          <h2>4. Preview & Export</h2>
          <div className="action-buttons">
            <button 
              className="preview-btn"
              onClick={handlePreview}
              disabled={isLoading || selectedCategories.length === 0}
            >
              {isLoading ? 'Loading...' : 'Preview Data'}
            </button>
            <button 
              className="export-btn"
              onClick={handleExport}
              disabled={isLoading || selectedCategories.length === 0}
            >
              {isLoading ? 'Exporting...' : 'Download Export'}
            </button>
          </div>

          {exportStatus && (
            <div className={`status-message ${exportStatus.includes('✅') ? 'success' : exportStatus.includes('Error') ? 'error' : 'info'}`}>
              {exportStatus}
            </div>
          )}
        </div>

        {/* Data Preview */}
        {previewData && (
          <div className="export-section">
            <h2>Data Preview</h2>
            <div className="preview-info">
              <p><strong>Total Records:</strong> {previewData.total_records}</p>
              <p><strong>Categories:</strong> {
                Array.isArray(previewData.categories_included) 
                  ? previewData.categories_included.join(', ')
                  : previewData.categories_included
              }</p>
              <p><strong>Date Range:</strong> {previewData.date_range.start} to {previewData.date_range.end}</p>
            </div>
            
            {previewData.preview.length > 0 && (
              <div className="preview-table-container">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {Object.keys(previewData.preview[0])
                        .filter(key => key !== '_id' && key !== 'note') // Hide MongoDB ID and notes
                        .map(key => (
                          <th key={key}>{key.replace(/_/g, ' ').toUpperCase()}</th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.preview.map((row, index) => (
                      <tr key={index}>
                        {Object.entries(row)
                          .filter(([key]) => key !== '_id' && key !== 'note') // Hide MongoDB ID and notes
                          .map(([key, value], i) => (
                            <td key={i}>
                              {value === null || value === undefined 
                                ? 'N/A' 
                                : typeof value === 'boolean'
                                  ? (value ? 'Yes' : 'No')
                                  : value.toString()}
                            </td>
                          ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {previewData.total_records > 10 && (
                  <p className="preview-note">
                    Showing first 10 of {previewData.total_records} records
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Export;
