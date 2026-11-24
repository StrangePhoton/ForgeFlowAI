import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, decideApproval, listApprovals } from "../api";
import { useAuth } from "../auth";
import type { PendingApproval } from "../types";

export function ApprovalsPage() {
  const { can } = useAuth();
  const [items, setItems] = useState<PendingApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const canDecide = can("approvals:decide");

  function refresh() {
    listApprovals()
      .then(setItems)
      .catch((err: Error) => setError(err.message));
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <>
      <h1>Approval queue</h1>
      {error ? <p className="error">{error}</p> : null}
      {items.length === 0 ? <p className="muted">No pending write actions.</p> : null}
      {items.map((item) => (
        <ApprovalCard key={item.investigation_id} item={item} canDecide={canDecide} onDone={refresh} />
      ))}
    </>
  );
}

function ApprovalCard({
  item,
  canDecide,
  onDone,
}: {
  item: PendingApproval;
  canDecide: boolean;
  onDone: () => void;
}) {
  const proposal = item.proposal;
  const [title, setTitle] = useState(String(proposal.title ?? ""));
  const [description, setDescription] = useState(String(proposal.description ?? ""));
  const [priority, setPriority] = useState(String(proposal.priority ?? "high"));
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent, decision: "approve" | "reject") {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      await decideApproval(item.investigation_id, decision, {
        title,
        description,
        priority,
        reason,
      });
      onDone();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Decision failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>
        {item.risk.toUpperCase()} · {item.tool_name}
      </h2>
      <p>
        Equipment {String(proposal.equipment_id ?? "unknown")} ·{" "}
        <Link to={`/investigations/${item.investigation_id}`}>investigation</Link>
      </p>
      <form className="stack">
        <label>
          <span>Title</span>
          <input value={title} onChange={(event) => setTitle(event.target.value)} disabled={!canDecide} />
        </label>
        <label>
          <span>Description</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} disabled={!canDecide} />
        </label>
        <label>
          <span>Priority</span>
          <input value={priority} onChange={(event) => setPriority(event.target.value)} disabled={!canDecide} />
        </label>
        <label>
          <span>Reason</span>
          <input value={reason} onChange={(event) => setReason(event.target.value)} disabled={!canDecide} />
        </label>
        {message ? <p className="error">{message}</p> : null}
        {canDecide ? (
          <div className="nav">
            <button type="button" disabled={busy} onClick={(event) => submit(event, "approve")}>
              Approve
            </button>
            <button className="danger" type="button" disabled={busy} onClick={(event) => submit(event, "reject")}>
              Reject
            </button>
          </div>
        ) : (
          <p className="muted">Your role can view this queue but cannot decide.</p>
        )}
      </form>
    </section>
  );
}
