import React, { useEffect, useState } from "react";
import { supabase } from "./SupabaseClient";
import "./Home.css";

function Home() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Handle OAuth tokens in URL hash
    const hash = window.location.hash;
    if (hash && hash.includes("access_token")) {
      const params = new URLSearchParams(hash.substring(1));
      const access_token = params.get("access_token");
      const refresh_token = params.get("refresh_token");

      if (access_token && refresh_token) {
        supabase.auth
          .setSession({ access_token, refresh_token })
          .then(({ data }) => {
            setUser(data.session?.user ?? null);
            window.history.replaceState({}, document.title, window.location.pathname);
          });
      } else {
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
    supabase.auth.getUser().then(({ data }) => setUser(data?.user || null));
    const { data: { subscription } = {} } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => { subscription && subscription.unsubscribe(); };
  }, []);

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
        queryParams: {
          prompt: "consent select_account",
        },
      },
    });
  };


  return (
    <div className="home-hero">
      {/* Left hero/main content */}
      <div className="home-left">
        <div className="home-tagline">YOUR PERSONAL HEALTH COMPANION</div>
        <div className="home-title">Meet Baymax</div>
        <div className="home-subtitle">
          Baymax helps you stay on top of your health by chatting with you, organizing your logs, visualizing trends, and turning your data into clear, shareable reports.
        </div>
        <div className="home-buttons">
          <button className="home-btn primary">Try Baymax Chatbot</button>
          <button className="home-btn secondary">View Health Insights</button>
        </div>
        <div className="home-highlights">
          <span>Smart Q&amp;A</span>
          <span>Visual Trends</span>
          <span>Easy File Uploads</span>
        </div>

        {/* Auth block (sign in / show account) */}
        <div style={{ marginTop: 30 }}>
          {!user ? (
            <button className="home-btn primary" style={{ background: "#4285F4", color: "white", display: "flex", alignItems: "center", gap: 10 }} onClick={signInWithGoogle}>
              <svg className="google-icon" style={{ width: 20, height: 20 }} viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Sign in with Google
            </button>
          ) : (
            <div style={{ marginTop: "15px", marginBottom: "8px" }}>
              <span style={{ color: "#76abae", fontWeight: 600 }}>
                Welcome, {user.user_metadata?.full_name || user.email}!
              </span>
              <button
                className="home-btn secondary"
                style={{ marginLeft: 16 }}
                onClick={() => supabase.auth.signOut()}
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Right: Card showing "How Baymax Works" */}
      <div className="home-right">
        <div className="home-card">
          <h3>How Baymax Works</h3>
          <ul>
            <li>Upload your health documents and files.</li>
            <li>Chat with Baymax to ask questions in natural language.</li>
            <li>View graphs and logs to track your progress over time.</li>
            <li>Export a clean report to share with doctors or caregivers.</li>
          </ul>
        </div>
      </div>
    </div >
  );
}

export default Home;
