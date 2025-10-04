import asyncio
import logging
from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import StateGraph

from src.filters.text_filter import filter_candidates_by_text
from src.schemas import Candidate
from src.schemas import FinalResult
from src.schemas import VisionResult
from src.scraper.scraper import scrape_candidates
from src.selector.selector import select_best_clip
from src.vision.analyzer import analyze_video_for_clip

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """
    Represents the state of the application's execution graph.
    """

    description: str
    duration_seconds: int
    max_candidates: int
    candidates: list[Candidate]
    filtered_candidates: list[Candidate]
    vision_results: list[VisionResult]
    final_result: FinalResult | None
    trace_info: dict


async def scrape_node(state: GraphState) -> dict:
    """
    Node that scrapes Twitter for initial candidates videos.
    """
    logger.info("--- SCRAPE NODE ---")
    candidates = await scrape_candidates(
        query=state["description"],
        max_candidates=state["max_candidates"],
    )
    state["trace_info"]["scraped_count"] = len(candidates)
    return {"candidates": candidates}


async def filter_node(state: GraphState) -> dict:
    """
    Node that filters candidates based on tweet text relevance.
    """
    logger.info("--- FILTER NODE ---")
    filtered = await filter_candidates_by_text(
        candidates=state["candidates"],
        description=state["description"],
        score_threshold=0.5,
    )
    state["trace_info"]["text_filtered_count"] = len(filtered)
    return {"filtered_candidates": filtered}


async def vision_node(state: GraphState) -> dict:
    """
    Node that performs vision analysis on filtered candidates.
    """
    logger.info("--- VISION NODE ---")
    tasks = [
        analyze_video_for_clip(
            candidate=candidate,
            description=state["description"],
            duration_seconds=state["duration_seconds"],
        )
        for candidate in state["filtered_candidates"]
    ]
    results = await asyncio.gather(*tasks)
    successful_results = [r for r in results if r and r.findings]
    state["trace_info"]["vision_analysis_count"] = len(successful_results)
    return {"vision_results": successful_results}


async def select_node(state: GraphState) -> dict:
    """
    Node that selects the best clip from the vision analysis results.
    """
    logger.info("--- SELECT NODE ---")
    final_result = select_best_clip(
        state["vision_results"],
        state["trace_info"],
    )
    return {"final_result": final_result}


async def decide_after_filter(state: GraphState) -> str:
    """
    Conditional edge that checks if any candidates survived the text filter.
    If not, it ends the graph execution.
    """
    if not state["filtered_candidates"]:
        logger.warning("No candidates left after text filtering. Ending graph.")
        return "end"
    return "continue"


async def decide_after_vision(state: GraphState) -> str:
    """
    Conditional edge that checks if the vision analysis found any clips.
    If not, it ends the graph execution.
    """
    if not state["vision_results"]:
        logger.warning("No clips found in vision analysis. Ending graph.")
        return "end"
    return "continue"


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("scrape", scrape_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("select", select_node)

    workflow.set_entry_point("scrape")

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

    return workflow.compile()


app = build_graph()
