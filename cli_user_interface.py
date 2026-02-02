"""Modern Terminal Dashboard for Anime & Manga AI Recommender."""

from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
import time
import threading
import sys
import msvcrt
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.prompt import Prompt
from rich.status import Status

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout as PTLayout
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea

from engine.recommender import Recommender
from db.mongo import get_all_titles, get_collection
import config


class ViewState(Enum):
    """Dashboard view states."""
    DASHBOARD = "dashboard"
    SEARCH_TEXT = "search_text"
    SEARCH_TITLE = "search_title"
    RESULTS = "results"
    HELP = "help"


@dataclass
class AppState:
    """Application state container."""
    current_view: ViewState = ViewState.DASHBOARD  # Start with dashboard
    search_query: str = ""
    search_input_buffer: str = ""  # For collecting search input character by character
    search_results: List[Tuple[float, Dict]] = None
    selected_result: int = 0
    is_loading: bool = False
    error_message: str = ""
    last_update: float = time.time()

    # Title search completion
    title_matches: List[str] = None
    selected_title_index: int = 0

    # Cached data
    total_titles: int = 0
    engine_status: str = "Initializing..."
    db_status: str = "Connecting..."


class DashboardUI:
    """Modern terminal dashboard for the recommendation system."""

    def __init__(self):
        self.console = Console(force_terminal=True)
        self.state = AppState()
        self.engine: Optional[Recommender] = None
        self.titles: List[str] = []
        self.completer: Optional[WordCompleter] = None

        # Initialize components
        self._initialize_app()

    def _initialize_app(self) -> None:
        """Initialize application components."""
        try:
            # Initialize database connection and get stats
            collection = get_collection()
            self.state.total_titles = collection.count_documents({})
            self.state.db_status = f"Connected ({self.state.total_titles} titles)"

            # Initialize recommendation engine
            self.state.engine_status = "Loading engine..."
            self.engine = Recommender()
            self.state.engine_status = "Ready"

            # Load titles for autocomplete
            self.titles = get_all_titles()
            self.completer = WordCompleter(self.titles, ignore_case=True)

        except Exception as e:
            self.state.error_message = f"Initialization failed: {e}"
            self.state.db_status = "Failed"
            self.state.engine_status = "Failed"

    def _create_header(self) -> Panel:
        """Create application header with title and status."""
        header_text = Text()
        header_text.append("🎌 Anime & Manga AI Recommender\n", style="bold cyan")
        header_text.append(f"v1.0 | {self.state.db_status} | {self.state.engine_status}", style="dim cyan")

        return Panel(Align.center(header_text), box=box.ROUNDED, border_style="cyan")

    def _create_dashboard_view(self) -> Panel:
        """Create main dashboard view with key metrics."""
        # Create table content as Rich Text object
        table_text = Text()
        table_text.append("Metric                    Value                    Status\n", style="bold magenta")
        table_text.append("─" * 60 + "\n")
        table_text.append(f"Total Titles            {self.state.total_titles:,}                    ✅\n")
        table_text.append(f"Engine Status           {self.state.engine_status}                    {'✅' if self.engine else '❌'}\n")
        table_text.append(f"Database                {self.state.db_status}                    {'✅' if 'Connected' in self.state.db_status else '❌'}\n")
        table_text.append(f"Search Types            Text & Title              ✅\n")

        welcome_text = Text("\nWelcome to the AI Recommendation System!\n\n")
        welcome_text.append("Use the keyboard shortcuts below to navigate.\n")
        welcome_text.append("Press 'h' for detailed help.", style="dim")

        # Combine texts
        combined_text = Text()
        combined_text.append(table_text)
        combined_text.append(welcome_text)

        return Panel(combined_text, title="Dashboard", box=box.ROUNDED)

    def _create_search_view(self) -> Panel:
        """Create search input view."""
        if self.state.current_view == ViewState.SEARCH_TEXT:
            prompt_text = "Describe what you want to watch:"
            placeholder = "e.g., 'action-packed adventure with magic'"

            input_display = self.state.search_input_buffer
            if not input_display:
                input_display = placeholder
                is_placeholder = True
            else:
                is_placeholder = False

            content = Text()
            content.append(f"{prompt_text}\n\n", style="bold cyan")
            if is_placeholder:
                content.append(f"{input_display}\n\n", style="dim white on blue")
            else:
                content.append(f"{input_display}\n\n", style="white on blue")
            content.append("Type to search, Enter to submit, Esc to cancel", style="dim")

        else:  # SEARCH_TITLE
            prompt_text = "Start typing a title:"
            placeholder = "e.g., 'Attack on Titan'"

            input_display = self.state.search_input_buffer
            if not input_display:
                input_display = placeholder
                is_placeholder = True
            else:
                is_placeholder = False

            content = Text()
            content.append(f"{prompt_text}\n\n", style="bold cyan")
            if is_placeholder:
                content.append(f"{input_display}\n\n", style="dim white on blue")
            else:
                content.append(f"{input_display}\n\n", style="white on blue")

            # Show matching titles if we have input
            if self.state.search_input_buffer and self.state.title_matches:
                content.append("\nMatching titles:\n", style="bold yellow")

                # Show up to 10 matches
                start_idx = max(0, self.state.selected_title_index - 5)
                end_idx = min(len(self.state.title_matches), start_idx + 10)

                for i in range(start_idx, end_idx):
                    title = self.state.title_matches[i]
                    if i == self.state.selected_title_index:
                        content.append(f"▶ {title}\n", style="bold white on blue")
                    else:
                        content.append(f"  {title}\n", style="dim white")

                if len(self.state.title_matches) > 10:
                    content.append(f"\n... and {len(self.state.title_matches) - 10} more matches", style="dim")

            content.append("\nType to search, ↑↓ to navigate, Enter to select, Esc to cancel", style="dim")

        return Panel(content, title="Search", box=box.ROUNDED)

    def _create_results_view(self) -> Panel:
        """Create results list view."""
        if not self.state.search_results:
            return Panel("No results found", title="Results", box=box.ROUNDED)

        # Create table for results
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Title", style="bold cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Score", style="green", justify="right")

        for i, (score, item) in enumerate(self.state.search_results):
            if not item:
                continue

            title = item.get("title_romaji") or item.get("title_english") or "Unknown"
            item_type = item.get("type", "Unknown")
            display_score = ".3f"

            if i == self.state.selected_result:
                table.add_row(f"▶ {title}", item_type, display_score, style="bold white on blue")
            else:
                table.add_row(title, item_type, display_score)

        return Panel(table, title="Results", box=box.ROUNDED)

    def _create_detail_view(self) -> Panel:
        """Create detail view for selected result."""
        if not self.state.search_results or self.state.selected_result >= len(self.state.search_results):
            return Panel("No selection", title="Details", box=box.ROUNDED)

        score, item = self.state.search_results[self.state.selected_result]

        details = Text()
        details.append(f"Title: {item.get('title_romaji') or item.get('title_english') or 'Unknown'}\n", style="bold cyan")
        details.append(f"Type: {item.get('type', 'Unknown')}\n", style="magenta")
        details.append(f"Score: {score:.3f}\n\n", style="green")

        if item.get("genres"):
            details.append(f"Genres: {', '.join(item['genres'])}\n", style="yellow")

        if item.get("description"):
            desc = item["description"][:200] + "..." if len(item["description"]) > 200 else item["description"]
            details.append(f"\nDescription: {desc}", style="dim")

        return Panel(details, title="Details", box=box.ROUNDED)

    def _update_title_matches(self) -> None:
        """Update the list of matching titles based on current input buffer."""
        if not self.state.search_input_buffer:
            self.state.title_matches = []
            self.state.selected_title_index = 0
            return

        # Find titles that start with the input (case insensitive)
        query = self.state.search_input_buffer.lower()
        matches = [title for title in self.titles if title.lower().startswith(query)]

        # If no exact starts, find titles that contain the input
        if not matches:
            matches = [title for title in self.titles if query in title.lower()]

        # Sort by relevance (exact matches first, then by length)
        matches.sort(key=lambda x: (not x.lower().startswith(query), len(x)))

        # Limit to reasonable number
        self.state.title_matches = matches[:50]  # Show up to 50 matches
        self.state.selected_title_index = 0

    def _create_results_view(self) -> Panel:
        """Create search results view."""
        if not self.state.search_results:
            return Panel("[dim]No results to display[/dim]",
                        title="[bold]Results[/bold]", box=box.ROUNDED)

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold green")
        table.add_column("#", style="cyan", width=3, no_wrap=True)
        table.add_column("Title", style="white", max_width=30)
        table.add_column("Score", style="yellow", width=6, justify="right")
        table.add_column("Type", style="magenta", width=8)

        for i, (score, doc) in enumerate(self.state.search_results[:10]):
            title = doc.get("title_romaji") or doc.get("title_english", "Unknown")
            title = title[:27] + "..." if len(title) > 30 else title
            item_type = doc.get("type", "Unknown")

            style = "bold white" if i == self.state.selected_result else "white"
            table.add_row(str(i + 1), title, f"{score:.2f}", item_type, style=style)

        if len(self.state.search_results) > 10:
            table.add_row("", f"[dim]+{len(self.state.search_results) - 10} more...[/dim]", "", "")

        return Panel(table, title=f"[bold]Results ({len(self.state.search_results)})[/bold]",
                    box=box.ROUNDED)

    def _create_detail_view(self) -> Panel:
        """Create detailed view for selected result."""
        if not self.state.search_results or self.state.selected_result >= len(self.state.search_results):
            return Panel("No selection", title="Details", box=box.ROUNDED)

        score, doc = self.state.search_results[self.state.selected_result]

        if not doc:
            return Panel("No details available", title="Details", box=box.ROUNDED)

        title = doc.get("title_romaji") or doc.get("title_english") or "Unknown Title"
        description = doc.get("description") or "No description available"
        if description and len(description) > 300:
            description = description[:300] + "..."
        genres = ", ".join(doc.get("genres", []))
        rating = doc.get("average_score")
        popularity = doc.get("popularity")

        details = Text()
        details.append(f"{title}\n\n", style="bold cyan")
        details.append("Description:\n", style="bold")
        details.append(f"{description}\n\n", style="dim")
        if genres:
            details.append(f"Genres: {genres}\n", style="yellow")
        if rating:
            details.append(f"Rating: {rating}/100\n", style="green")
        if popularity:
            details.append(f"Popularity: {popularity:,}\n", style="magenta")

        return Panel(details, title="Details", box=box.ROUNDED)

    def _get_key_non_blocking(self) -> Optional[str]:
        """Get a key press without blocking. Returns None if no key is pressed."""
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch()
                # Handle special keys
                if key == b'\xe0':  # Special key prefix
                    key = msvcrt.getch()
                    if key == b'H':  # Up arrow
                        return "up"
                    elif key == b'P':  # Down arrow
                        return "down"
                    elif key == b'K':  # Left arrow
                        return "left"
                    elif key == b'M':  # Right arrow
                        return "right"
                elif key == b'\r':  # Enter
                    return "\r"
                else:
                    return key.decode('utf-8', errors='ignore')
            except:
                return None
        return None

    def _create_help_view(self) -> Panel:
        """Create help view with keyboard shortcuts."""
        # Create table content as Rich Text
        table_text = Text()
        table_text.append("Key    Action\n", style="bold blue")
        table_text.append("─" * 25 + "\n")

        shortcuts = [
            ("d", "Dashboard"),
            ("t", "Text Search"),
            ("s", "Title Search"),
            ("↑/↓", "Navigate Results/Matches"),
            ("m", "Find More Similar (Results)"),
            ("Enter", "Select Item/Details"),
            ("h", "Help"),
            ("q", "Quit"),
            ("Esc", "Back/Cancel"),
        ]

        for key, action in shortcuts:
            table_text.append(f"{key:<6} {action}\n")

        content_text = Text()
        content_text.append("Keyboard Shortcuts\n\n", style="bold")
        content_text.append("Navigate using the keys shown. Most actions are single-keypress.\n\n")
        content_text.append("• Text Search: Type a description of what you want to watch\n")
        content_text.append("• Title Search: Type a title name, see matching titles, navigate with arrows, select with Enter\n")
        content_text.append("• Results: Use ↑↓ to navigate, 'm' to find more similar titles to the selected one\n")
        content_text.append(table_text)

        return Panel(content_text, title="Help", box=box.ROUNDED)

    def _create_status_bar(self) -> Panel:
        """Create status bar with current state info."""
        view_name = self.state.current_view.value.replace("_", " ").title()
        status_parts = [
            f"View: {view_name}",
            f"Time: {time.strftime('%H:%M:%S')}",
        ]

        if self.state.search_results:
            status_parts.append(f"Results: {len(self.state.search_results)}")

        status_text = Text(" | ".join(status_parts), style="dim")

        if self.state.error_message:
            status_text.append(f" | Error: {self.state.error_message}", style="red")

        return Panel(status_text, box=box.SIMPLE, border_style="dim")

    def _create_footer(self) -> Panel:
        """Create footer with key hints."""
        hints = {
            ViewState.DASHBOARD: "[t] Text Search | [s] Title Search | [h] Help | [q] Quit",
            ViewState.SEARCH_TEXT: "[Type to search] [Enter] Submit | [Esc] Cancel",
            ViewState.SEARCH_TITLE: "[Type to search] [↑↓] Navigate matches | [Enter] Select | [Esc] Cancel",
            ViewState.RESULTS: "[↑↓] Navigate | [m] More similar | [d] Dashboard | [q] Quit",
            ViewState.HELP: "[d] Dashboard | [q] Quit",
        }

        hint_text = hints.get(self.state.current_view, "[q] Quit")
        return Panel(Text(hint_text, style="dim"), box=box.SIMPLE, border_style="dim")

    def _render_layout(self) -> Layout:
        """Render the current layout based on view state."""
        layout = Layout()

        # Header always visible
        layout.split_column(
            Layout(self._create_header(), size=5),
            Layout(name="main", ratio=1),
            Layout(self._create_footer(), size=3)
        )

        main_layout = layout["main"]

        if self.state.current_view == ViewState.DASHBOARD:
            main_layout.update(self._create_dashboard_view())
        elif self.state.current_view in (ViewState.SEARCH_TEXT, ViewState.SEARCH_TITLE):
            main_layout.update(self._create_search_view())
        elif self.state.current_view == ViewState.RESULTS:
            main_layout.split_row(
                Layout(self._create_results_view(), ratio=2),
                Layout(self._create_detail_view(), ratio=1)
            )
        elif self.state.current_view == ViewState.HELP:
            main_layout.update(self._create_help_view())

        return layout

    def _handle_search(self, search_type: str) -> None:
        """Handle search operation."""
        self.state.is_loading = True
        self.state.error_message = ""

        try:
            if search_type == "text":
                if not self.state.search_query.strip():
                    self.state.error_message = "Please enter a search query"
                    return
                self.state.search_results = self.engine.by_text(
                    self.state.search_query, config.DEFAULT_RESULTS_N
                )
            else:  # title search
                if not self.state.search_query.strip():
                    self.state.error_message = "Please enter a title"
                    return
                self.state.search_results = self.engine.by_title(
                    self.state.search_query, config.DEFAULT_RESULTS_N
                )

            if self.state.search_results:
                self.state.current_view = ViewState.RESULTS
                self.state.selected_result = 0
            else:
                self.state.error_message = "No results found"

        except Exception as e:
            self.state.error_message = f"Search failed: {e}"
        finally:
            self.state.is_loading = False

    def _get_search_input(self) -> Optional[str]:
        """Get search input from user."""
        try:
            if self.state.current_view == ViewState.SEARCH_TEXT:
                return Prompt.ask("Describe what you want").strip()
            else:  # SEARCH_TITLE
                return prompt("Start typing title: ", completer=self.completer).strip()
        except KeyboardInterrupt:
            return None

    def run(self) -> None:
        """Main application loop."""
        try:
            with Live(self._render_layout(), console=self.console, refresh_per_second=20) as live:
                last_refresh = time.time()

                while True:
                    current_time = time.time()

                    # Handle input (non-blocking)
                    key = self._get_key_non_blocking()

                    if key:
                        # Debug: show what key was pressed
                        # print(f"Key pressed: {key!r}, view: {self.state.current_view}, has_matches: {bool(self.state.title_matches)}")  # Uncomment for debugging

                        state_changed = False

                        try:
                            if self.state.current_view in (ViewState.SEARCH_TEXT, ViewState.SEARCH_TITLE):
                                # Handle character-by-character input for search
                                if key == "\r":  # Enter key
                                    if self.state.current_view == ViewState.SEARCH_TITLE and self.state.title_matches:
                                        # Use selected title for title search
                                        selected_title = self.state.title_matches[self.state.selected_title_index]
                                        self.state.search_query = selected_title
                                        self._handle_search("title")
                                        self.state.search_input_buffer = ""  # Clear buffer
                                        self.state.title_matches = []  # Clear matches
                                        # Force immediate display update
                                        live.update(self._render_layout())
                                    elif self.state.search_input_buffer.strip():
                                        self.state.search_query = self.state.search_input_buffer
                                        search_type = "text" if self.state.current_view == ViewState.SEARCH_TEXT else "title"
                                        self._handle_search(search_type)
                                        self.state.search_input_buffer = ""  # Clear buffer
                                        if self.state.current_view == ViewState.SEARCH_TITLE:
                                            self.state.title_matches = []  # Clear matches
                                        # Force immediate display update
                                        live.update(self._render_layout())
                                    else:
                                        self.state.error_message = "Please enter a search query"
                                        state_changed = True
                                elif key == "\x1b":  # Escape key
                                    self.state.current_view = ViewState.DASHBOARD
                                    self.state.search_input_buffer = ""
                                    self.state.title_matches = []
                                    state_changed = True
                                elif key == "\x08" or key == "\x7f":  # Backspace/Delete
                                    self.state.search_input_buffer = self.state.search_input_buffer[:-1]
                                    if self.state.current_view == ViewState.SEARCH_TITLE:
                                        self._update_title_matches()
                                    state_changed = True
                                elif key in ("up", "k") and self.state.current_view == ViewState.SEARCH_TITLE and self.state.title_matches:
                                    # Navigate title matches
                                    self.state.selected_title_index = max(0, self.state.selected_title_index - 1)
                                    state_changed = True
                                elif key in ("down", "j") and self.state.current_view == ViewState.SEARCH_TITLE and self.state.title_matches:
                                    # Navigate title matches
                                    self.state.selected_title_index = min(len(self.state.title_matches) - 1, self.state.selected_title_index + 1)
                                    state_changed = True
                                elif len(key) == 1 and key.isprintable():  # Regular character
                                    self.state.search_input_buffer += key
                                    if self.state.current_view == ViewState.SEARCH_TITLE:
                                        self._update_title_matches()
                                    state_changed = True
                                # Ignore other keys
                            else:
                                # Regular key input
                                if key == "q":
                                    break
                                elif key == "d":
                                    self.state.current_view = ViewState.DASHBOARD
                                    self.state.error_message = ""
                                    state_changed = True
                                elif key == "t":
                                    self.state.current_view = ViewState.SEARCH_TEXT
                                    state_changed = True
                                elif key == "s":
                                    self.state.current_view = ViewState.SEARCH_TITLE
                                    self.state.search_input_buffer = ""
                                    self.state.title_matches = []
                                    self.state.selected_title_index = 0
                                    state_changed = True
                                elif key == "h":
                                    self.state.current_view = ViewState.HELP
                                    state_changed = True
                                elif key in ("up", "k") and self.state.current_view == ViewState.RESULTS:
                                    self.state.selected_result = max(0, self.state.selected_result - 1)
                                    state_changed = True
                                elif key in ("down", "j") and self.state.current_view == ViewState.RESULTS:
                                    self.state.selected_result = min(
                                        len(self.state.search_results) - 1 if self.state.search_results else 0,
                                        self.state.selected_result + 1
                                    )
                                    state_changed = True
                                elif key == "\r" and self.state.current_view == ViewState.RESULTS:
                                    # Enter key - could expand details or take action
                                    pass
                                elif key == "m" and self.state.current_view == ViewState.RESULTS and self.state.search_results:
                                    # Find more similar titles based on selected result
                                    if self.state.selected_result < len(self.state.search_results):
                                        _, selected_item = self.state.search_results[self.state.selected_result]
                                        if selected_item:
                                            selected_title = selected_item.get("title_romaji") or selected_item.get("title_english")
                                            if selected_title:
                                                self.state.search_query = selected_title
                                                self._handle_search("title")
                                                # Force immediate display update
                                                live.update(self._render_layout())
                                # else:
                                #     self.state.error_message = f"Unknown key: {key!r}"  # Uncomment for debugging

                        except Exception as e:
                            self.state.error_message = f"Input error: {e}"
                            state_changed = True

                        # Update display immediately if state changed
                        if state_changed:
                            live.update(self._render_layout())
                            continue

                    # Small sleep to prevent CPU hogging
                    time.sleep(0.01)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Application interrupted by user.[/yellow]")
        except Exception as e:
            error_str = str(e).replace("[", "\\[")  # Escape brackets in error message
            self.console.print(f"[red]Fatal error: {error_str}[/red]")
            raise


def main() -> None:
    """Entry point for the dashboard application."""
    dashboard = DashboardUI()
    dashboard.run()


if __name__ == "__main__":
    main()