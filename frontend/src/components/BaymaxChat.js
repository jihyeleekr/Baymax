import React, { useState, useEffect, useRef } from "react";
import { supabase } from '../SupabaseClient';
import "./BaymaxChat.css";

// Utility: get personalized LS key
function getChatStorageKey(user) {
  return user?.email ? `baymax_chat_history_${user.email}` : "baymax_chat_history_guest";
}

function getFormattedTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
  const displayHours = now.getHours() % 12 || 12;
  return `${displayHours}:${minutes} ${ampm}`;
}

function BaymaxChat() {
  // Store current user (for personalization)
  const [user, setUser] = useState(null);

  // Load initial messages according to user
  const [messages, setMessages] = useState(() => {
    // Temporarily load top-level guest data before true user known
    const saved = localStorage.getItem("baymax_chat_history_guest");
    if (saved) return JSON.parse(saved);
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

  // Get user on mount and listen for log in/out
  useEffect(() => {
    // Initial check
    supabase.auth.getUser().then(({ data }) => {
      setUser(data?.user || null);
    });
    // Listen for auth state changes
    const { data: { subscription } = {} } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => { subscription && subscription.unsubscribe(); };
  }, []);

  // When user changes, load their personal chat history
  useEffect(() => {
    const key = getChatStorageKey(user);
    const saved = localStorage.getItem(key);
    if (saved) {
      setMessages(JSON.parse(saved));
    } else {
      setMessages([
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
      ]);
    }
  }, [user]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // Save messages to personal localStorage key
  useEffect(() => {
    const key = getChatStorageKey(user);
    localStorage.setItem(key, JSON.stringify(messages));
  }, [messages, user]);

  // Handle sending messages
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userInput = input.trim();

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        sender: "user",
        text: userInput,
        time: "Now",
      },
    ]);
    setInput("");

    try {
      // If user is logged in, get full user object (for id or email)
      const userResult = await supabase.auth.getUser();
      const currentUser = userResult.data?.user;
      const userId = currentUser ? currentUser.id : "anonymous";

      // API CALL WITH USER ID
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput, user_id: userId })
      });

      const data = await response.json();

      if (response.ok) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            sender: "bot",
            text: data.response,
            time: "Now"
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            sender: "bot",
            text: "Error: " + (data.error || 'Failed to get response'),
            time: "Now"
          }
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "bot",
          text: "Connection error: " + error.message,
          time: "Now"
        }
      ]);
    }
  };

  // ...return (...) stays the same


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
