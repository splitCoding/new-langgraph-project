"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph


class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    message: str = "example"


async def call_model(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]
    return {
        "message": "[agent2] call_model invoked successfully. "
                   f'Configured with {configuration.get("my_configurable_param")}'
    }


async def message_invert(state: State) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    return {
        "message": "[agent2] message_invert invoked successfully. "
    }


# Define the graph
graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node(call_model)
    .add_node(message_invert)
    .add_edge("__start__", "call_model")
    .add_edge("call_model", "message_invert")
    .compile(name="Agent2 Graph")
)
