import Baymax from "./pages/Baymax";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Nav from "./Nav";
import Team from "./Team/Team";

function App() {
  return (
    <Router>
      <Nav />
      <Routes>
        <Route path="/" element={<h1>Home Page</h1>} />
        <Route path="/baymax" element={<Baymax />} />
        <Route path="/graph" element={<h1>Graph Page</h1>} />
        <Route path="/log" element={<h1>Log Page</h1>} />
        <Route path="/upload" element={<h1>Upload Page</h1>} />
        <Route path="/export" element={<h1>Export Page</h1>} />
        <Route path="/team" element={<Team />} />
      </Routes>
    </Router>
  );
}

export default App;
