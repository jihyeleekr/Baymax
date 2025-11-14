import React from "react";
import "./Team.css";

function Team() {
  return (
    <div className="team-container">
      <h1 className="team-title">Our Team</h1>

      <div className="team-grid">
        {/* Adbullah */}
        <div className="team-card">
          <div className="team-avatar">A</div>
          <h3 className="team-name">Abdullah Alwazan</h3>
          <p className="team-roll">File Upload & PDF Processing Engineer</p>
        </div>

        {/* Hari */}
        <div className="team-card">
          <div className="team-avatar">B</div>
          <h3 className="team-name">Hari Amin</h3>
          <p className="team-roll">Chatbot Integration & AI Engineer</p>
        </div>

        {/* Can */}
        <div className="team-card">
          <div className="team-avatar">C</div>
          <h3 className="team-name">Can Gokmen</h3>
          <p className="team-roll">Report Generation & Export Features Developer</p>
        </div>

        {/* Jihye */}
        <div className="team-card">
          <div className="team-avatar">D</div>
          <h3 className="team-name">Jihye Lee</h3>
          <p className="team-roll">Frontend Developer & UI/UX Lead</p>
        </div>
      </div>
    </div>
  )
}

export default Team;