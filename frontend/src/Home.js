import React, { useEffect, useState } from "react";
import { supabase } from "./SupabaseClient";

function Home() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data, error }) => {
      if (error) console.log(error);
      setUser(data?.user || null);
      console.log("Mounted:", data?.user);
    });
    const { data: { subscription } = {} } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      console.log("State changed:", session?.user);
    });
    return () => { subscription && subscription.unsubscribe(); };
  }, []);

  // --- Inserted sign-in handler here ---
  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin }
    });
  };

  return (
    <div>
      <pre>User state: {JSON.stringify(user, null, 2)}</pre>
      {user ? (
        <button onClick={() => supabase.auth.signOut()}>Sign Out</button>
      ) : (
        <button onClick={signInWithGoogle}>Sign in with Google</button>
      )}
    </div>
  );
}
export default Home;
