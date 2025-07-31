"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from src.review.graph_create import create_review_graph

# Define the graph
graph = (
    create_review_graph()
)
