import React, { useState } from "react";
import "./BaymaxChat.css";

function BaymaxChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "bot",
      text: "Hi, I’m Baymax. How can I help with your health today?",
      time: "10:30 AM",
    },
    {
      id: 2,
      sender: "user",
      text: "Show me a summary of my recent logs.",
      time: "10:31 AM",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // 프론트용 더미 전송 처리 (나중에 백엔드 연결)
    const newMessage = {
      id: Date.now(),
      sender: "user",
      text: input.trim(),
      time: "Now",
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput("");
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
