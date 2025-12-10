import BaymaxChat from "./components/Chatbot/BaymaxChat";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Nav from "./components/Nav/Nav";
import Team from "./components/Team/Team";
import Home from "./components/Home/Home";
import Footer from "./components/Footer/Footer";
import Upload from "./components/Upload/Upload";
import Export from "./components/Export/Export";
import Graph from "./components/Graph/Graph";
import Log from "./components/Log/Log";


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
