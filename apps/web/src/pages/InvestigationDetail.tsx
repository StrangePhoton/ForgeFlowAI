import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getInvestigation } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import { toolCallsFromInvestigation, workflowTimeline } from "../timeline";
import type { EvidenceItem, InvestigationResult } from "../types";

export function InvestigationDetailPage() {
  const { id } = useParams();
  const [item, setItem] = useState<InvestigationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      return;
    }
    let cancelled = false;
    setError(null);
    setItem(null);
    getInvestigation(id)
      .then((value) => {
        if (!cancelled) {
          setItem(value);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return <p className="error">{error}</p>;
  }
  if (!item) {
    return <p className="muted">Loading…</p>;
  }

  const timeline = workflowTimeline(item);
  const tools = toolCallsFromInvestigation(item);

  return (
    <>
      <p className="muted">
        <Link to="/">Dashboard</Link>
      </p>
      <section className="panel">
        <h1>{item.report.title}</h1>
        <p>
          <StatusBadge status={item.status} /> {item.equipment_code ?? "unresolved equipment"}
        </p>
        <p>{item.report.summary}</p>
        {item.report.likely_cause ? (
          <p>
            <strong>Likely cause:</strong> {item.report.likely_cause}
          </p>
        ) : null}
        {item.status === "awaiting_approval" ? (
          <p>
            <Link to="/approvals">Open approval queue</Link>
          </p>
        ) : null}
        {item.work_order ? (
          <p>
            Work order <strong>{item.work_order.number}</strong>: {item.work_order.title}
          </p>
        ) : null}
      </section>

      <section className="panel">
        <h2>Workflow timeline</h2>
        <ol className="timeline">
          {timeline.map((step) => (
            <li key={step.id}>
              <span className={`dot${step.done ? " done" : ""}${step.current ? " current" : ""}`} />
              <div>
                <strong>{step.label}</strong>
                {step.detail ? <div className="muted">{step.detail}</div> : null}
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Evidence</h2>
        <EvidenceGroup title="Facts" items={item.evidence.facts} />
        <EvidenceGroup title="Inferences" items={item.evidence.inferences} />
        <EvidenceGroup title="Recommendations" items={item.evidence.recommendations} />
      </section>

      <section className="panel">
        <h2>Tool calls</h2>
        <p className="muted">
          Derived from evidence sources and write outcomes. The graph does not store hidden chain-of-thought.
        </p>
        <table>
          <thead>
            <tr>
              <th>Tool / source</th>
              <th>Status</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((tool) => (
              <tr key={`${tool.name}-${tool.status}`}>
                <td>
                  <code>{tool.name}</code>
                </td>
                <td>{tool.status}</td>
                <td>{tool.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function EvidenceGroup({
  title,
  items,
}: {
  title: string;
  items: EvidenceItem[];
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <details open>
      <summary>
        {title} ({items.length})
      </summary>
      {items.map((item) => (
        <p key={`${item.source}-${item.statement.slice(0, 40)}`}>
          <span className={`badge ${item.kind}`}>{item.kind}</span> {item.statement}{" "}
          <span className="muted">({item.source})</span>
        </p>
      ))}
    </details>
  );
}
