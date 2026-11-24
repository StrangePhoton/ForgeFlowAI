import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, createInvestigation } from "../api";

const EXAMPLE = "Investigate overheating on CNC-042";

export function NewInvestigationPage() {
  const navigate = useNavigate();
  const [request, setRequest] = useState(EXAMPLE);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await createInvestigation(request);
      if (result.investigation_id) {
        navigate(`/investigations/${result.investigation_id}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Investigation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h1>New investigation</h1>
      <form className="stack" onSubmit={onSubmit}>
        <label>
          <span>Operational request</span>
          <textarea value={request} onChange={(event) => setRequest(event.target.value)} required />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Running…" : "Run investigation"}
        </button>
      </form>
    </section>
  );
}
