import BaymaxChat from "./components/BaymaxChat";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Nav from "./Nav";
import Team from "./Team/Team";
import Home from "./Home";
import Footer from "./Footer/Footer";
import Upload from "./Upload/Upload";
import Export from "./Export/Export";
import Graph from "./Graph/Graph";
import Log from "./Log/Log";

function App() {
  return (
    <Router>
      <div className="App">
        <Nav />
        <div className="app-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/baymax" element={<BaymaxChat />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/export" element={<Export />} />
            <Route path="/graph" element={<Graph />} />
            <Route path="/log" element={<Log />} />
            <Route path="/team" element={<Team />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
