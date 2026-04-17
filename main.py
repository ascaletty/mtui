"""
cal_app.py — Textual port of the Rust ratatui Cal app.

Layout
------
  ┌─ Search ──────────────────────────────────────────┐
  │ (press / to activate, Esc to leave, Enter submit) │
  └───────────────────────────────────────────────────┘
  ┌─ Left (70%) ──────────────┬─ Top-Right    (30%) ──┐
  │                           │ (image preview)        │
  │                           ├───────────────────────┤
  │                           │ Bottom-Right           │
  └───────────────────────────┴───────────────────────┘

Focus cycling: Tab / Shift-Tab
Quit: q (while not editing)
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, Static, ListView, ListItem
from textual_image.widget import Image
from parse_decklist import parse_decklist
from parse_decklist import parse_response


class Pane(Static):
    """A bordered, focusable pane that highlights when focused."""

    # Textual reads this class variable to decide if the widget can receive focus
    COMPONENT_CLASSES: set[str] = set()
    can_focus = True

    DEFAULT_CSS = """
    Pane {
        border: solid white;
        padding: 0 1;
        height: 100%;
        width: 100%;
    }
    Pane:focus {
        border: solid yellow;
    }
    """

    def __init__(self, pane_title: str = "", **kwargs):
        super().__init__(**kwargs)
        self._pane_title = pane_title

    def on_mount(self) -> None:
        self.border_title = self._pane_title


# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------

class SearchBar(Input):
    """Input widget that activates on '/' and deactivates on Esc."""

    DEFAULT_CSS = """
    SearchBar {
        height: 3;
        border: solid white;
        background: $surface;
    }
    SearchBar:focus {
        border: solid yellow;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(placeholder="Press / to search…", **kwargs)
        self.disabled = True  # start non-editable


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

IMAGE_PATH = Path("./devour/Anger.png")   # same default as the Rust app


class CalApp(App):
    """Textual port of the Rust ratatui Cal TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #search-row {
        height: 3;
        width: 100%;
    }

    #main-row {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }

    #left-pane {
        width: 70%;
        height: 100%;
        border: solid white;
        padding: 0 1;
    }
    #left-pane:focus {
        border: solid yellow;
    }

    #right-col {
        width: 50%;
        height: 100%;
        layout: vertical;
    }

    #top-right {
        height: 1fr;
        border: solid white;
        padding: 0 1;
    }
    #top-right:focus {
        border: solid yellow;
    }
    #card-list {
    border: solid white;
    padding: 0 1;
    height: 100%;
    background: $surface;
}

#card-list:focus {
    border: solid yellow;
}

    #preview {
    border: solid white;
    padding: 0 1;
    height: 100%;
    background: $surface;
}

    #bottom-right {
        height: 1fr;
        border: solid white;
        padding: 0 1;
    }
    #bottom-right:focus {
        border: solid yellow;
    }

    #image-placeholder {
        color: $text-muted;
        text-align: center;
        padding: 1;
    }

    #messages {
        height: auto;
        padding: 0 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q",       "quit",          "Quit",          show=True),
        Binding("tab",     "focus_next",    "Next pane",     show=True),
        Binding("shift+tab","focus_previous","Prev pane",    show=True),
        Binding("/",       "activate_search","Search",       show=True),

        Binding(":",       "activate_command","Command",       show=True),
    ]

    # Track submitted search messages
    messages: reactive[list[str]] = reactive(list)
    decks: reactive[list[dict]] = reactive(list)
    preview: reactive(str)= reactive(str)

    # ---------------------------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        # Top search bar
        yield SearchBar(id="search")

        with Horizontal(id="main-row"):
            # Left large pane
            # yield Pane(pane_title="left", id="left-pane")
            with Pane(id= "left-pane"):
                yield ListView(id="card-list")
            # Right column: image on top, generic bottom pane
            with Vertical(id="right-col"):
                with Pane(pane_title="preview", id="top-right"):
                    yield Image(id="preview")
        yield SearchBar(id="command")

    def build_list_view(self)-> ListView:
        list_view= self.query_one("#card-list");
        for deck in self.decks:
            for card in deck:
                item = ListItem(Label(card["name"]))
                list_view.append(item)
        return list_view

    def build_image(self)-> ListView: 
        image= self.query_one("#preview")
        filename = self.preview.replace(" ", "_").replace(",", "").replace("/", "_") + ".png"
        image.image= "devour/" + filename
        return image

    def on_mount(self) -> None:
        # Give initial focus to the left pane
        self.query_one("#left-pane").focus()
        self.query_one("#search").border_title = "Search"
        # top-right title only needed when it's an ImageViewer (not a Pane)
        try:
            top = self.query_one("#top-right")
            if not isinstance(top, Pane):
                top.border_title = "top"
        except Exception:
            pass

    # ---------------------------------------------------------------------------
    # Search bar activation
    # ---------------------------------------------------------------------------
    def action_activate_search(self) -> None:
        """Press '/' to jump into the search bar."""
        search = self.query_one("#search", SearchBar)
        search.disabled = False
        search.focus()

    @on(Input.Submitted, "#search")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.messages = [*self.messages, text]
            self.notify(f"Search: {text}", title="Submitted")
        search = self.query_one("#search", SearchBar)
        search.clear()
        search.disabled = True
        # Return focus to left pane
        self.query_one("#left-pane").focus()

    @on(Input.Changed, "#search")
    def on_search_escape(self, event: Input.Changed) -> None:
        # Esc is handled by Textual's Input natively (clears focus)
        pass

    def on_key(self, event) -> None:
        search = self.query_one("#search", SearchBar)
        # If Esc pressed while search is active, deactivate it
        if event.key == "escape" and not search.disabled:
            search.clear()
            search.disabled = True
            self.query_one("#left-pane").focus()
            event.stop()
    
    def action_activate_command(self)-> None:
        "Execute commands"
        search = self.query_one("#command", SearchBar)
        search.disabled = False
        search.focus();

    @on(Input.Submitted, "#command")
    def on_command_submitted(self, event: Input.Submitted)-> None:
        text= event.value.strip()
        s= text.split(" ")
        if s[0]== "load":
            response= parse_decklist(s[1])
            self.decks= [*self.decks, response]
            self.notify(f"Deck: {s[1]}", title="Loaded")
            self.build_list_view()
        search = self.query_one("#command", SearchBar)
        search.clear()
        search.disabled = True
        # Return focus to left pane
        self.query_one("#left-pane").focus()
    @on(ListView.Selected, "#card-list")
    def on_card_selected(self, event: ListView.Selected):
        idx = event.index
        msg=self.decks[0]

        msg= msg["data"]

        msg= msg[idx]

        msg= msg["name"]
        
        self.preview= msg
        self.build_image()


    # download + display (or call kitty icat)


    @on(Input.Changed, "#command")
    def on_search_escape(self, event: Input.Changed) -> None:
        # Esc is handled by Textual's Input natively (clears focus)
        pass

    def on_key_c(self, event) -> None:
        search = self.query_one("#command", SearchBar)
        # If Esc pressed while search is active, deactivate it
        if event.key == "escape" and not search.disabled:
            search.clear()
            search.disabled = True
            self.query_one("#left-pane").focus()
            event.stop()

            



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = CalApp()
    app.run()
