#!/usr/bin/env python3
from rich.console import RenderableType
import json
from textual.containers import Container, VerticalScroll
from textual.events import Key
from textual import events
from textual import on
from textual.app import App, ComposeResult
from textual.reactive import var
from textual.widgets import Footer, Input, Static, Label, Select, TabbedContent, TabPane
from code_browser import CodeBrowserWidget


LINES = """
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
when an unknown printer took a galley of type and scrambled it to make a type specimen book.
It has survived not only five centuries,
but also the leap into electronic typesetting,
remaining essentially unchanged.
""".splitlines()

NAMES = [
    "Form",
    "Code-Browser"
]


class TextQuestion(Static):
    _label: Label
    _input: Input

    def __init__(self, label, placeholder, **kwargs):
        super().__init__(**kwargs)
        self._label = Label(label)
        self._input = Input(placeholder=placeholder)

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str]:
        return (self._label.renderable, self._input.value)

class SelectQuestion(Static):
    _label: Label
    _input: Select

    def __init__(self, label, lines, **kwargs):
        super().__init__(**kwargs)
        self._label = Label(label)
        self._input = Select((line, line) for line in lines)

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str | None]:
        return (self._label.renderable, self._input.value)


class TestApp(App):
    BINDINGS = [
        ('h', 'dump_values', 'Dump Values'),
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
        TabbedContent {
            height: 100%
    }
        ContentSwitcher {
            height: 100%
    }
        TabPane {
            height: 100%
    }

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

    def on_mount(self, event: events.Mount) -> None:
        self.query_one(TabbedContent).focus()

    def compose(self) -> ComposeResult:
        form_widgets = TestApp.parse_cookie_cutter()
        with TabbedContent():
            with TabPane("Form", id='form'):
                yield VerticalScroll(*form_widgets)
            with TabPane("Code-Browser", id='code-browser'):
                yield CodeBrowserWidget()
        yield Footer()

    def action_dump_values(self) -> None:
        textboxes = self.query(TextQuestion)
        selects = self.query(SelectQuestion)
        with open('test.txt', 'w') as op_file:
            for text in textboxes:
                op_file.write(f"{text.value[0]}:{text.value[1]}\n")
            for select in selects:
                op_file.write(f"{select.value[0]}:{select.value[1]}\n")

    @staticmethod
    def read_cookie_cutter() -> list[tuple[str, str]]:
        """Helper method for reading cookiecutter.json"""
        fp = open('cookiecutter.json')
        cookie_handle = json.load(fp)
        return list(cookie_handle.items())

    @staticmethod
    def parse_cookie_cutter():
        """Helper method for parsing read_cookie_cutter"""
        template = TestApp.read_cookie_cutter()
        widgets = []
        for prompt in template:
            if isinstance(prompt[1], str):
                widgets.append(TextQuestion(prompt[0], prompt[1]))
            elif isinstance(prompt[1], list):
                widgets.append(SelectQuestion(prompt[0], prompt[1]))
        return widgets

    @staticmethod
    def read_copier() -> None:
        """ Placeholder for a helper method for reading copier.yml"""
        pass

    @staticmethod
    def parse_copier() -> None:
        """Placeholder for a helper method for parsing read_copier()"""
        pass

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        if self.query_one(TabbedContent).active == 'code-browser':
            self.show_tree = not self.show_tree

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        if self.query_one(TabbedContent).active == 'code-browser':
            self.set_class(show_tree, "-show-tree")

    @on(Key)
    def tab_shift_tab_pressed(self, event: Key):
        """Placeholder for writing to output when TAB/s-TAB is detected in the input-stream"""
        if event.key == 'return':
            pass
        pass

if __name__ == "__main__":
    TestApp().run()
