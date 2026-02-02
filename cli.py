"""Terminal User Interface for the anime/manga recommendation system."""

from typing import List, Dict, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.text import Text
from rich import box
from rich.prompt import Prompt

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt

from engine.recommender import Recommender
from db.mongo import get_all_titles

console = Console(force_terminal=True)


def create_header() -> Panel:
    """Create the application header panel."""
    return Panel(
        Align.center(Text("🎌 Anime & Manga AI Recommender", style="bold cyan")),
        box=box.ROUNDED,
    )


def create_menu_panel() -> Panel:
    """Create the menu options panel."""
    content = (
        "[bold green]1[/] Search by description\n\n"
        "[bold green]2[/] Recommend by title\n\n"
        "[bold red]Q[/] Quit"
    )
    return Panel(content, title="Menu", box=box.ROUNDED)


def create_result_card(doc: Dict) -> Panel:
    """Create a result card for a single document."""
    title = doc.get("title_romaji") or doc.get("title_english", "Unknown Title")
    description = (doc.get("description") or "")[:140]
    return Panel(f"[bold magenta]{title}[/]\n{description}", box=box.ROUNDED)


def create_results_panel(results: List[Tuple[float, Dict]]) -> Panel:
    """Create the results panel with recommendation cards."""
    if not results:
        return Panel("No results found. Try a different query.", title="Results", box=box.ROUNDED)

    cards = [create_result_card(doc) for _, doc in results]
    return Panel(Columns(cards, equal=True), title="Results", box=box.ROUNDED)


def handle_text_search(engine: Recommender) -> List[Tuple[float, Dict]]:
    """Handle text-based search input."""
    try:
        query = Prompt.ask("Describe what you want").strip()
        if not query:
            console.print("[yellow]Please enter a description.[/yellow]")
            return []
        return engine.by_text(query, 8)
    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        return []


def handle_title_search(engine: Recommender, completer: WordCompleter) -> List[Tuple[float, Dict]]:
    """Handle title-based search input."""
    try:
        title = prompt("Start typing title: ", completer=completer).strip()
        if not title:
            console.print("[yellow]Please enter a title.[/yellow]")
            return []
        return engine.by_title(title, 8)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        return []


def main() -> None:
    """Main application loop."""
    try:
        engine = Recommender()
        titles = get_all_titles()
        completer = WordCompleter(titles, ignore_case=True)

        results = None

        while True:
            console.clear()
            console.print(create_header())

            layout = Columns(
                [
                    create_menu_panel(),
                    create_results_panel(results),
                ],
                expand=True,
            )

            console.print(layout)

            choice = Prompt.ask("\nChoose option").lower().strip()

            if choice == "1":
                results = handle_text_search(engine)
            elif choice == "2":
                results = handle_title_search(engine, completer)
            elif choice == "q":
                break
            else:
                console.print("[yellow]Invalid option. Please choose 1, 2, or Q.[/yellow]")
                continue

    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
