#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Static, Label
from EditableText import EditableText

class TextQuestion(Static):
    _label_1: Label
    _label_2: Label
    _input_1: EditableText
    _input_2: EditableText

    def compose(self) -> ComposeResult:
        self._label_1 = Label("This is a fancy description")
        self._input_1 = EditableText()
        self._label_2 = Label("This is another fancy description")
        self._input_2 = EditableText()
        yield Container(
            self._label_1,
            self._input_1,
            self._label_2,
            self._input_2,
        )
        yield Footer()

class TestApp(App):
    BINDINGS = [
        ('h', 'dump_values', 'Dump Values')
    ]
    _textbox: TextQuestion
    def compose(self) -> ComposeResult:
        self._textbox = TextQuestion()
        yield self._textbox

    def action_dump_values(self) -> None:
        l1 = self._textbox._input_1.value
        l2 = self._textbox._input_2.value
        with open('test.txt', 'w') as op_file:
            op_file.write("First Name: {}\nLast Name: {}".format(l1, l2))

if __name__ == "__main__":
    app = TestApp()
    app.run()
