#!/usr/bin/env python3
from textual.events import Key
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Input, Static, Label, Select, Tabs


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
        yield Container(
            self._label_1,
            self._input_1,
            self._label_2,
            self._input_2,
            self._label_3,
            self._input_3
        )
        yield Footer()

class TestApp(App):
    BINDINGS = [
        ('h', 'dump_values', 'Dump Values')
    ]
    _tab: Tabs
    _textbox: TextQuestion

    def compose(self) -> ComposeResult:
        self._textbox = TextQuestion()
        self._tab = Tabs(NAMES[0], NAMES[1])
        yield self._tab
        yield self._textbox

    def action_dump_values(self) -> None:
        l1 = self._textbox._input_1.value
        l2 = self._textbox._input_2.value
        l3 = self._textbox._input_3.value
        with open('test.txt', 'w') as op_file:
            op_file.write("First Name: {}\nLast Name: {}\nSelect Output: {}".format(l1, l2, l3))

    # Placeholder for writing to output when TAB/s-TAB is detected in the input-stream
    @on(Key)
    def tab_shift_tab_pressed(self, event: Key):
        if event.key == 'return':
            pass
        pass

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle TabActivated message sent by Tabs."""
        if self._tab.active == 'tab-1':
            self._textbox.visible = True
        else:
            self._textbox.visible = False

if __name__ == "__main__":
    app = TestApp()
    app.run()
