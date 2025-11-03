from pathlib import Path

from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph.state import CompiledGraph


def save_graph_as_png(app: CompiledGraph, output_file_path) -> None:
    """Save the compiled graph as a PNG image."""
    png_image = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    file_path = output_file_path if len(output_file_path) > 0 else "graph.png"
    with Path(file_path).open("wb") as f:
        f.write(png_image)
