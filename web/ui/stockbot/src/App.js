import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";

import Home from "./components/Home";
// import placeholders for your future pages
import Search from "./components/Search"; 
import Chat from "./components/Chat";

export default function App() {
  return (
    <Router>
      <header style={{ padding: "1rem", borderBottom: "1px solid #ccc" }}>
        <NavLink 
          to="/" 
          end 
          style={({ isActive }) => ({
            marginRight: 16,
            textDecoration: isActive ? "underline" : "none"
          })}
        >
          Home
        </NavLink>
        <NavLink 
          to="/search" 
          style={({ isActive }) => ({
            marginRight: 16,
            textDecoration: isActive ? "underline" : "none"
          })}
        >
          Search
        </NavLink>
        <NavLink 
          to="/chat" 
          style={({ isActive }) => ({
            textDecoration: isActive ? "underline" : "none"
          })}
        >
          Chat
        </NavLink>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </Router>
  );
}
