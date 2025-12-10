import React from "react";
import { Link } from "react-router-dom";
import "./Nav.css";

function Nav() {
  return (
    <nav className="navbar">
      <div className="nav-logo">Baymax</div>

      <ul className="nav-links">
        <li><Link to="/">Home</Link></li>
        <li><Link to="/baymax">Baymax</Link></li>
        <li><Link to="/graph">Graph</Link></li>
        <li><Link to="/log">Log</Link></li>
        <li><Link to="/upload">Upload</Link></li>
        <li><Link to="/export">Export</Link></li>
        <li><Link to="/team">Team</Link></li>
      </ul>
    </nav>
  );
}

export default Nav;
