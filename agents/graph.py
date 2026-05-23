from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    planner_node,
    retriever_node,
    generator_node,
    critic_node,
)
import logging

log = logging.getLogger(__name__)


def _route_critic(state: AgentState) -> str:
    """
    Conditional edge from critic node.
    Routes to END if grounded or max retries reached.
    Routes back to retriever if not grounded and retries remain.
    """
    if state.get('grounded', True):
        log.info('Critic: grounded → END')
        return END
    if state.get('retry_count', 0) >= 3:
        log.info('Critic: max retries → END')
        return END
    log.info(f'Critic: not grounded → retry retrieval (attempt {state.get("retry_count", 0)})')
    return 'retriever'


def build_graph():
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node('planner',   planner_node)
    graph.add_node('retriever', retriever_node)
    graph.add_node('generator', generator_node)
    graph.add_node('critic',    critic_node)

    # Linear edges: planner → retriever → generator → critic
    graph.add_edge('planner',   'retriever')
    graph.add_edge('retriever', 'generator')
    graph.add_edge('generator', 'critic')

    # Conditional edge from critic: END or back to retriever
    graph.add_conditional_edges('critic', _route_critic)

    # Set the entry point
    graph.set_entry_point('planner')

    return graph.compile()


# Module-level singleton — compiled once, reused for all queries
rag_agent = build_graph()


def run_agent(query: str, language: str = 'all') -> dict:
    """
    Run the full agentic RAG pipeline for a single query.

    Args:
        query:    The user's question
        language: Language filter ('all', 'sin', 'tam', 'eng')

    Returns:
        Final agent state dict containing answer, retrieved_chunks,
        sub_questions, grounded, critique, retry_count
    """
    initial_state = AgentState(
        query            = query,
        language         = language,
        chat_history     = [],
        sub_questions    = [],
        retrieved_chunks = [],
        answer           = '',
        grounded         = False,
        critique         = '',
        missing          = '',
        retry_count      = 0,
    )
    final_state = rag_agent.invoke(initial_state)
    return final_state
