import asyncio
import logging
from typing import List
from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import StateGraph

from src.filters.text_filter import filter_candidates_by_text
from src.scraper.schemas import Candidate
from src.scraper.schemas import FinalResult
from src.scraper.schemas import VisionResult
from src.scraper.service import scrape_candidates
from src.selector.selector import select_best_clip
from src.vision.analyzer import analyze_video_for_clip

logger = logging.getLogger(__name__)


# Define the state that will be passed between nodes in the graph
class GraphState(TypedDict):
    description: str
    duration_seconds: int
    max_candidates: int
    candidates: List[Candidate]
    filtered_candidates: List[Candidate]
    vision_results: List[VisionResult]
    final_result: FinalResult
    trace_info: dict


# These are the nodes of our graph. Each node is a function that performs an action.
async def scrape_node(state: GraphState) -> GraphState:
    """Scrapes Twitter for initial candidate videos."""
    logger.info("--- Starting Scrape Node ---")
    candidates = await scrape_candidates(state["description"], state["max_candidates"])
    state["trace_info"]["scraped_count"] = len(candidates)
    return {**state, "candidates": candidates}


async def filter_node(state: GraphState) -> GraphState:
    """Filters candidates based on tweet text relevance."""
    logger.info("--- Starting Text Filter Node ---")
    filtered_candidates = await filter_candidates_by_text(
        state["candidates"], state["description"]
    )
    state["trace_info"]["text_filtered_count"] = len(filtered_candidates)
    return {**state, "filtered_candidates": filtered_candidates}


async def vision_node(state: GraphState) -> GraphState:
    """Performs vision analysis on filtered candidates to find clips."""
    logger.info("--- Starting Vision Analysis Node ---")
    tasks = [
        analyze_video_for_clip(c, state["description"], state["duration_seconds"])
        for c in state["filtered_candidates"]
    ]
    vision_results = await asyncio.gather(*tasks)
    successful_results = [res for res in vision_results if res and res.findings]
    state["trace_info"]["vision_analysis_count"] = len(successful_results)
    return {**state, "vision_results": successful_results}


async def select_node(state: GraphState) -> GraphState:
    """Selects the best clip from the vision analysis results."""
    logger.info("--- Starting Select Best Clip Node ---")
    final_result = select_best_clip(state["vision_results"], state["trace_info"])
    return {**state, "final_result": final_result}


# --- FIX START ---
# We now have two separate conditional edges to check the state at the correct time.


def decide_after_filter(state: GraphState) -> str:
    """
    Checks if any candidates survived the text filter.
    If not, the graph ends. Otherwise, it proceeds to vision analysis.
    """
    if not state["filtered_candidates"]:
        logger.warning("No candidates left after text filtering. Ending graph.")
        return "end"
    return "continue"


def decide_after_vision(state: GraphState) -> str:
    """
    Checks if the vision analysis found any relevant clips.
    If not, the graph ends. Otherwise, it proceeds to the final selection.
    """
    if not state["vision_results"]:
        logger.warning("No clips found after vision analysis. Ending graph.")
        return "end"
    return "continue"


# --- FIX END ---


# Now, we define the graph structure
def build_graph():
    workflow = StateGraph(GraphState)

    # Add the nodes
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("select", select_node)

    # Set the entry point
    workflow.set_entry_point("scrape")

    # --- FIX START ---
    # The graph flow is now controlled by our new conditional edges.
    workflow.add_edge("scrape", "filter")

    workflow.add_conditional_edges(
        "filter",
        decide_after_filter,
        {
            "continue": "vision",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "vision",
        decide_after_vision,
        {
            "continue": "select",
            "end": END,
        },
    )

    workflow.add_edge("select", END)
    # --- FIX END ---

    # Compile the graph into a runnable application
    return workflow.compile()


# Create the runnable app
app = build_graph()
