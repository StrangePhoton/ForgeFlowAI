import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHealth, fetchReady, listApprovals, listInvestigations } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import type { InvestigationResult, PendingApproval } from "../types";

export function DashboardPage() {
  const [investigations, setInvestigations] = useState<InvestigationResult[]>([]);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [health, setHealth] = useState("unknown");
  const [ready, setReady] = useState("unknown");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listInvestigations(), listApprovals(), fetchHealth(), fetchReady()])
      .then(([items, pending, healthBody, readyBody]) => {
        setInvestigations([...items].reverse());
        setApprovals(pending);
        setHealth(healthBody.status);
        setReady(readyBody.status);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const waiting = investigations.filter((item) => item.status === "awaiting_approval").length;
  const failed = investigations.filter((item) => item.status === "rejected").length;

  return (
    <>
      <h1>Operations</h1>
      {error ? <p className="error">{error}</p> : null}
      <section className="grid">
        <div className="stat">
          Recent investigations
          <b>{investigations.length}</b>
        </div>
        <div className="stat">
          Waiting for approval
          <b>{waiting}</b>
        </div>
        <div className="stat">
          Rejected
          <b>{failed}</b>
        </div>
        <div className="stat">
          API
          <b>
            {health} / {ready}
          </b>
        </div>
      </section>
      <section className="panel">
        <h2>Investigations</h2>
        {investigations.length === 0 ? (
          <p className="muted">No investigations in this API process yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Equipment</th>
                <th>Request</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((item) => (
                <tr key={item.investigation_id}>
                  <td>{item.equipment_code ?? "—"}</td>
                  <td>
                    <Link to={`/investigations/${item.investigation_id}`}>{item.request}</Link>
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {approvals.length > 0 ? (
          <p>
            <Link to="/approvals">{approvals.length} item(s) in the approval queue</Link>
          </p>
        ) : null}
      </section>
    </>
  );
}
