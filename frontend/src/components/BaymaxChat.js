import React, { useState, useEffect, useRef } from "react";
import { supabase } from '../SupabaseClient';

import "./BaymaxChat.css";


 function getFormattedTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
  const displayHours = now.getHours() % 12 || 12;
  return `${displayHours}:${minutes} ${ampm}`;
}

function BaymaxChat() {
  // Initialize messages from localStorage or use defaults
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('baymax_chat_history');
    if (saved) {
      return JSON.parse(saved);
    }

   



    return [
      {
        id: 1,
        sender: "bot",
        text: "Hi, I'm Baymax. How can I help with your health today?",
        time: getFormattedTime(),
      },
      {
        id: 2,
        sender: "user",
        text: "Show me a summary of my recent logs.",
        time: getFormattedTime(),
      },
    ];
  });

  const [input, setInput] = useState("");
  const chatWindowRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // Save messages to localStorage
  useEffect(() => {
    localStorage.setItem('baymax_chat_history', JSON.stringify(messages));
  }, [messages]);

  // Handle sending messages
 const handleSend = async (e) => {
  e.preventDefault();
  if (!input.trim()) return;

  const userInput = input.trim();

  setMessages((prev) => [...prev, {
    id: Date.now(),
    sender: "user",
    text: userInput,
    time: "Now",
  }]);
  setInput("");

  try {
    // Get Supabase user
    const userResult = await supabase.auth.getUser();
    const user = userResult.data?.user;
    const userId = user ? user.id : "anonymous";

    // API CALL WITH USER ID
    const response = await fetch('http://localhost:5001/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userInput, user_id: userId })
    });

    const data = await response.json();

    if (response.ok) {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: "bot",
        text: data.response,
        time: "Now"
      }]);
    } else {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: "bot",
        text: "Error: " + (data.error || 'Failed to get response'),
        time: "Now"
      }]);
    }
  } catch (error) {
    setMessages((prev) => [...prev, {
      id: Date.now() + 1,
      sender: "bot",
      text: "Connection error: " + error.message,
      time: "Now"
    }]);
  }
};

  return (
    <div className="chat-page">
      <div className="chat-layout">
        {/* Left: Chat Section */}
        <section className="chat-panel">
          <header className="chat-header">
            <div>
              <h1 className="chat-title">Baymax Chatbot</h1>
              <p className="chat-subtitle">
                Ask questions about your health logs, uploads, and reports in natural language.
              </p>
            </div>
          </header>

          <div className="chat-window" ref={chatWindowRef}>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message-row ${msg.sender === "user" ? "message-row-user" : "message-row-bot"}`}
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

        {/* Right: Info/Tips Panel */}
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
              <li>"Summarize my last 3 blood test results."</li>
              <li>"Are there any worrying trends in my heart rate logs?"</li>
              <li>"Create a short summary I can share with my doctor."</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default BaymaxChat;
