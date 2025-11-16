// src/Home/Home.js
import React from "react";
import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home-hero">
      <div className="home-left">
        <p className="home-tagline">Your Personal Health Companion</p>
        <h1 className="home-title">Meet Baymax</h1>
        <p className="home-subtitle">
          Baymax helps you stay on top of your health by chatting with you,
          organizing your logs, visualizing trends, and turning your data into
          clear, shareable reports.
        </p>

        <div className="home-buttons">
          <Link to="/baymax" className="home-btn primary">
            Try Baymax Chatbot
          </Link>

          <Link to="/graph" className="home-btn secondary">
            View Health Insights
          </Link>
        </div>

        <div className="home-highlights">
          <span>🩺 Smart Q&A</span>
          <span>📊 Visual Trends</span>
          <span>📁 Easy File Uploads</span>
        </div>
      </div>

      <div className="home-right">
        <div className="home-card">
          <h3>How Baymax Works</h3>
          <ul>
            <li>Upload your health documents and files.</li>
            <li>Chat with Baymax to ask questions in natural language.</li>
            <li>View graphs and logs to track your progress over time.</li>
            <li>Export a clean report to share with doctors or caregivers.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Home;
