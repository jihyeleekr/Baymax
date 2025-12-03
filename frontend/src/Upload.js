import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "./SupabaseClient";
import "./Upload.css";

function Upload() {
  const [file, setFile] = useState(null);
  const [prescription, setPrescription] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (selectedFile && !allowedTypes.includes(selectedFile.type)) {
      setError("Invalid file type. Please upload PDF, PNG, or JPG.");
      setFile(null);
      return;
    }

    // Validate file size (5MB max)
    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      setError("File too large. Maximum size is 5MB.");
      setFile(null);
      return;
    }

    setError(null);
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      const userId = user ? user.id : "anonymous";

      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      // Upload to backend
      const response = await fetch('http://localhost:5001/api/prescription/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setPrescription(data);
      } else {
        setError(data.error || "Upload failed");
      }
    } catch (err) {
      setError("Connection error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAskBaymax = () => {
    navigate(`/baymax?prescription_id=${prescription.prescription_id}`);
  };

  const handleReset = () => {
    setFile(null);
    setPrescription(null);
    setError(null);
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <header className="upload-header">
          <h1>Upload Prescription</h1>
          <p>Upload your prescription (PDF, PNG, or JPG) to get a plain-language explanation</p>
        </header>

        {!prescription ? (
          <div className="upload-section">
            <div className="file-upload-box">
              <input
                type="file"
                id="file-input"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="file-upload-label">
                <div className="upload-icon">📄</div>
                <p>{file ? file.name : "Click to select a file"}</p>
                <span className="upload-hint">PDF, PNG, or JPG • Max 5MB</span>
              </label>
            </div>

            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            {file && !loading && (
              <button className="upload-btn" onClick={handleUpload}>
                Upload & Process
              </button>
            )}

            {loading && (
              <div className="loading-section">
                <div className="spinner"></div>
                <p>Processing your prescription...</p>
                <span className="loading-hint">Extracting text and analyzing...</span>
              </div>
            )}
          </div>
        ) : (
          <div className="results-section">
            <div className="success-banner">
              ✅ Prescription processed successfully!
            </div>

            {/* Medications */}
            <div className="result-card">
              <h2>💊 Medications</h2>
              {prescription.medications && prescription.medications.length > 0 ? (
                <ul className="medication-list">
                  {prescription.medications.map((med, index) => (
                    <li key={index}>
                      <strong>{med.name}</strong> - {med.dosage}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No medications detected</p>
              )}
            </div>

            {/* Warnings */}
            {prescription.warnings && prescription.warnings.length > 0 && (
              <div className="result-card warnings-card">
                <h2>⚠️ Important Warnings</h2>
                <ul className="warnings-list">
                  {prescription.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Explanation */}
            <div className="result-card explanation-card">
              <h2>📝 Plain Language Summary</h2>
              <p className="explanation-text">{prescription.explanation}</p>
            </div>

            {/* Action Buttons */}
            <div className="action-buttons">
              <button className="ask-baymax-btn" onClick={handleAskBaymax}>
                💬 Ask Baymax Questions
              </button>
              <button className="reset-btn" onClick={handleReset}>
                Upload Another Prescription
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;
