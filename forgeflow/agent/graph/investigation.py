"""Explicit LangGraph investigation workflow."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from forgeflow.agent.nodes.investigation import (
    InvestigationNodes,
    route_after_equipment,
    route_after_proposal,
)
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.state import InvestigationState
from forgeflow.mcp.runtime import McpToolGateway


def build_investigation_graph(
    *,
    tools: McpToolGateway,
    llm: LLMProvider,
    approval_gate: ApprovalGate | None = None,
    checkpointer: Any = None,
) -> Any:
    nodes = InvestigationNodes(tools=tools, llm=llm, approval_gate=approval_gate)
    graph: StateGraph[InvestigationState] = StateGraph(InvestigationState)
    graph.add_node("analyze_request", nodes.analyze_request)
    graph.add_node("create_plan", nodes.create_plan)
    graph.add_node("resolve_equipment", nodes.resolve_equipment)
    graph.add_node("retrieve_telemetry", nodes.retrieve_telemetry)
    graph.add_node("retrieve_alarms", nodes.retrieve_alarms)
    graph.add_node("retrieve_maintenance", nodes.retrieve_maintenance)
    graph.add_node("retrieve_documentation", nodes.retrieve_documentation)
    graph.add_node("evaluate_evidence", nodes.evaluate_evidence_node)
    graph.add_node("generate_report", nodes.generate_report)
    graph.add_node("propose_action", nodes.propose_action)
    graph.add_node("request_approval", nodes.request_approval)
    graph.add_node("execute_action", nodes.execute_action)

    graph.add_edge(START, "analyze_request")
    graph.add_edge("analyze_request", "create_plan")
    graph.add_edge("create_plan", "resolve_equipment")
    graph.add_conditional_edges(
        "resolve_equipment",
        route_after_equipment,
        {
            "retrieve_telemetry": "retrieve_telemetry",
            "evaluate_evidence": "evaluate_evidence",
        },
    )
    graph.add_edge("retrieve_telemetry", "retrieve_alarms")
    graph.add_edge("retrieve_alarms", "retrieve_maintenance")
    graph.add_edge("retrieve_maintenance", "retrieve_documentation")
    graph.add_edge("retrieve_documentation", "evaluate_evidence")
    graph.add_edge("evaluate_evidence", "generate_report")
    graph.add_edge("generate_report", "propose_action")
    graph.add_conditional_edges(
        "propose_action",
        route_after_proposal,
        {
            "request_approval": "request_approval",
            "end": END,
        },
    )
    graph.add_edge("request_approval", "execute_action")
    graph.add_edge("execute_action", END)
    return graph.compile(checkpointer=checkpointer)
