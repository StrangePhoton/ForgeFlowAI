import { useEffect, useState } from "react";
import { listAudit } from "../api";
import type { AuditEvent } from "../types";

export function AuditPage() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [eventType, setEventType] = useState("");
  const [toolName, setToolName] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAudit({
      event_type: eventType || undefined,
      tool_name: toolName || undefined,
      status: status || undefined,
    })
      .then(setItems)
      .catch((err: Error) => setError(err.message));
  }, [eventType, toolName, status]);

  return (
    <>
      <h1>Audit log</h1>
      <section className="panel">
        <div className="filters">
          <label>
            <span>Event</span>
            <input value={eventType} onChange={(event) => setEventType(event.target.value)} placeholder="login_failure" />
          </label>
          <label>
            <span>Tool</span>
            <input value={toolName} onChange={(event) => setToolName(event.target.value)} placeholder="create_work_order" />
          </label>
          <label>
            <span>Status</span>
            <input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="denied" />
          </label>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Event</th>
              <th>User</th>
              <th>Tool</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.occurred_at.replace("T", " ").slice(0, 19)}</td>
                <td>{item.event_type}</td>
                <td>
                  {item.username ?? "—"} {item.role ? `(${item.role})` : ""}
                </td>
                <td>{item.tool_name ?? "—"}</td>
                <td>{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
