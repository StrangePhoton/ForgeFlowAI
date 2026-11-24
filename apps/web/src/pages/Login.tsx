import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";

export function LoginPage() {
  const { me, loading, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("engineer");
  const [password, setPassword] = useState("engineer-dev");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && me) {
    const from = (location.state as { from?: string } | null)?.from ?? "/";
    return <Navigate to={from} replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="panel login-card">
        <h1>Sign in</h1>
        <p className="muted">Local demo accounts. Sign in as engineer to start CNC-042, then manager to approve.</p>
        <ul className="muted">
          <li>engineer / engineer-dev — start investigations</li>
          <li>manager / manager-dev — approve work orders</li>
          <li>viewer / viewer-dev — read only</li>
        </ul>
        <form className="stack" onSubmit={onSubmit}>
          <label>
            <span>Username</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
