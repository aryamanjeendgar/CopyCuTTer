#!/usr/bin/env python3
from textual.events import Key
from textual import events
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
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
    _label_1: Label
    _label_2: Label
    _label_3: Label
    _input_1: Input
    _input_2: Input
    _input_3: Select

    def compose(self) -> ComposeResult:
        self._label_1 = Label("This is a fancy description")
        self._label_2 = Label("This is another fancy description")
        self._label_3 = Label("A cool selector")
        self._input_1 = Input(placeholder="First Name")
        self._input_2 = Input(placeholder="Last Name")
        self._input_3 = Select((line, line) for line in LINES)
        yield self._label_1
        yield self._input_1
        yield self._label_2
        yield self._input_2
        yield self._label_3
        yield self._input_3

class TestApp(App):
    BINDINGS = [
        ('h', 'dump_values', 'Dump Values'),
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

    def on_mount(self, event: events.Mount) -> None:
        self.query_one(TabbedContent).focus()

    # def compose(self) -> ComposeResult:
    #     with TabbedContent(initial="jessica"):
    #         with TabPane("Leto", id="leto"):
    #             yield Markdown("_LETO_")
    #         with TabPane("Jessica", id="jessica"):
    #             yield Markdown("*JESSICA*")
    #         with TabPane("Paul", id="paul"):
    #             yield Markdown("`PAUL`")

    def compose(self) -> ComposeResult:
        yield Footer()
        with TabbedContent():
            with TabPane("Form", id='form'):
                yield TextQuestion()
            with TabPane("Code-Browser", id='code-browser'):
                yield CodeBrowserWidget()
        # yield self._tab

    def action_dump_values(self) -> None:
        l1 = self.query_one(TextQuestion)._input_1.value
        l2 = self.query_one(TextQuestion)._input_2.value
        l3 = self.query_one(TextQuestion)._input_3.value
        with open('test.txt', 'w') as op_file:
            op_file.write("First Name: {}\nLast Name: {}\nSelect Output: {}".format(l1, l2, l3))

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        if self.query_one(TabbedContent).active == 'code-browser':
            self.show_tree = not self.show_tree

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        if self.query_one(TabbedContent).active == 'code-browser':
            self.set_class(show_tree, "-show-tree")

    # Placeholder for writing to output when TAB/s-TAB is detected in the input-stream
    @on(Key)
    def tab_shift_tab_pressed(self, event: Key):
        if event.key == 'return':
            pass
        pass

    # def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
    #     """Handle TabActivated message sent by Tabs."""
    #     if self._tab.active == 'tab-1':
    #         self._textbox.visible = True
    #         self._code_browser.visible = False
    #     else:
    #         self._textbox.visible = False
    #         self._code_browser.visible = True

if __name__ == "__main__":
    TestApp().run()
