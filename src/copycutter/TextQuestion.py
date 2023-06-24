#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.widgets import Input, Footer, Static


class TextQuestion(Static):
    _input_1: Input
    _input_2: Input

    BINDINGS = [
        ('h', 'dump_values', 'Dump Values')
    ]
    def compose(self) -> ComposeResult:
        self._input_1 = Input(placeholder="First Name")
        self._input_2 = Input(placeholder="Last Name")

        yield self._input_1
        yield self._input_2
        yield Footer()

    def action_dump_values(self) -> None:
        l1 = self._input_1.value
        l2 = self._input_2.value
        with open('test.txt', 'w') as op_file:
            op_file.write("First Name: {}\nLast Name: {}".format(l1, l2))

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TextQuestion()

if __name__ == "__main__":
    app = TestApp()
    app.run()
