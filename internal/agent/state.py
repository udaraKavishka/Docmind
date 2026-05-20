from typing import TypedDict


class AgentState(TypedDict):
    # Input
    query:            str          # Original user question
    language:         str          # Language filter: 'all', 'sin', 'tam', 'eng'
    chat_history:     list[dict]   # Multi-turn conversation history

    # Planner output
    sub_questions:    list[str]    # Decomposed sub-questions

    # Retriever output
    retrieved_chunks: list[dict]   # Top-N chunks after reranking

    # Generator output
    answer:           str          # Generated answer with citations

    # Critic output
    grounded:         bool         # True if answer is supported by context
    critique:         str          # Critic's explanation
    missing:          str          # What information is missing (if not grounded)

    # Loop control
    retry_count:      int          # Number of retrieval retries so far