import React, { useState, useEffect } from "react";
import "./BaymaxChat.css";

function BaymaxChat() {
  // 🔧 CHANGE THIS - Load from localStorage on startup
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('baymax_chat_history');
    if (saved) {
      return JSON.parse(saved);
    }
    // Only use these if localStorage is empty
    return [
      {
        id: 1,
        sender: "bot",
        text: "Hi, I'm Baymax. How can I help with your health today?",
        time: "10:30 AM",
      },
      {
        id: 2,
        sender: "user",
        text: "Show me a summary of my recent logs.",
        time: "10:31 AM",
      },
    ];
  });
  
  const [input, setInput] = useState("");

  // Save to localStorage whenever messages change
  useEffect(() => {
    localStorage.setItem('baymax_chat_history', JSON.stringify(messages));
  }, [messages]);

 const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userInput = input.trim();
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      sender: "user",
      text: userInput,
      time: "Now",
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Call Gemini API
    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
      });

      const data = await response.json();
      
      if (response.ok) {
        const botMessage = {
          id: Date.now() + 1,
          sender: "bot",
          text: data.response,
          time: "Now"
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          sender: "bot",
          text: "Error: " + (data.error || 'Failed to get response'),
          time: "Now"
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        sender: "bot",
        text: "Connection error: " + error.message,
        time: "Now"
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };


  return (
    <div className="chat-page">
      <div className="chat-layout">
        {/* 왼쪽: Chat 영역 */}
        <section className="chat-panel">
          <header className="chat-header">
            <div>
              <h1 className="chat-title">Baymax Chatbot</h1>
              <p className="chat-subtitle">
                Ask questions about your health logs, uploads, and reports in natural language.
              </p>
            </div>
          </header>

          <div className="chat-window">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message-row ${msg.sender === "user" ? "message-row-user" : "message-row-bot"
                  }`}
              >
                <div className={`message-bubble message-${msg.sender}`}>
                  <p className="message-text">{msg.text}</p>
                  <span className="message-meta">
                    {msg.sender === "user" ? "You · " : "Baymax · "}
                    {msg.time}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <form className="chat-input-bar" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              placeholder="Ask Baymax anything about your health data…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" className="chat-send-btn">
              Send
            </button>
          </form>
        </section>

        {/* 오른쪽: 정보 / 힌트 패널 */}
        <aside className="chat-sidebar">
          <div className="sidebar-card">
            <h2>How to use Baymax</h2>
            <ul>
              <li>Ask follow-up questions about your uploaded documents.</li>
              <li>Request summaries of your recent logs and trends.</li>
              <li>Prepare questions to discuss with your doctor.</li>
              <li>Generate a report before exporting it.</li>
            </ul>
          </div>

          <div className="sidebar-card secondary">
            <h3>Example prompts</h3>
            <ul>
              <li>“Summarize my last 3 blood test results.”</li>
              <li>“Are there any worrying trends in my heart rate logs?”</li>
              <li>“Create a short summary I can share with my doctor.”</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default BaymaxChat;
