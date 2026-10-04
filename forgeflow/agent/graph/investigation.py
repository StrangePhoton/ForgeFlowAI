"""Explicit LangGraph investigation workflow."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from forgeflow.agent.nodes.investigation import InvestigationNodes, route_after_equipment
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.state import InvestigationState
from forgeflow.mcp.runtime import McpToolGateway


def build_investigation_graph(
    *,
    tools: McpToolGateway,
    llm: LLMProvider,
) -> Any:
    nodes = InvestigationNodes(tools=tools, llm=llm)
    graph: StateGraph[InvestigationState] = StateGraph(InvestigationState)
    graph.add_node("analyze_request", nodes.analyze_request)
    graph.add_node("create_plan", nodes.create_plan)
    graph.add_node("resolve_equipment", nodes.resolve_equipment)
    graph.add_node("retrieve_telemetry", nodes.retrieve_telemetry)
    graph.add_node("retrieve_alarms", nodes.retrieve_alarms)
    graph.add_node("retrieve_maintenance", nodes.retrieve_maintenance)
    graph.add_node("evaluate_evidence", nodes.evaluate_evidence_node)
    graph.add_node("generate_report", nodes.generate_report)

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
    graph.add_edge("retrieve_maintenance", "evaluate_evidence")
    graph.add_edge("evaluate_evidence", "generate_report")
    graph.add_edge("generate_report", END)
    return graph.compile()
