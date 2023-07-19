#!/usr/bin/env python3
"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import sys

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import DirectoryTree, Static

class CodeBrowserWidget(Static):
    """Textual code browser app."""

    CSS_PATH = "code_browser.css"

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" #if len(sys.argv) < 2 else sys.argv[1]
        with Container():
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)

    def on_mount(self, event: events.Mount) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=True,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)


"""
The problem was essentially to see how to split the contents
of the initial `code_browser` would be split across the actual `App`
and the `Static` widget
"""
class TestApp(App):
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
        #tree-view {
            display: none;
            scrollbar-gutter: stable;
            overflow: auto;
            width: auto;
            height: 100%;
            dock: left;
        }

        .-show-tree #tree-view {
            display: block;
            max-width: 50%;
        }
    """

    show_tree = var(True)

    def compose(self) -> ComposeResult:
        yield CodeBrowserWidget()

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree

if __name__ == "__main__":
    TestApp().run()
