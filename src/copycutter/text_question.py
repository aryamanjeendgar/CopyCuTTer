#!/usr/bin/env python3
from cookiecutter.exceptions import OutputDirExistsException, RepositoryNotFound
from rich.console import RenderableType
import os, json, subprocess
from textual.containers import VerticalScroll
from textual.events import Key
from cookiecutter.main import cookiecutter
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
    _property_val: str

    def __init__(self, label, placeholder, property_val, **kwargs):
        super().__init__(**kwargs)
        self._label = Label(label)
        self._input = Input(placeholder=placeholder)
        self._property_val = property_val

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str, str]:
        return (self._label.renderable, self._input.value, self._property_val)

    #TODO: method to show value of actual field when hovering
    # def watch_mouse_over(self, value: bool) -> None:
    #     self._label.update("Funni")
    #     return super().watch_mouse_over(value)

class SelectQuestion(Static):
    _label: Label
    _input: Select
    _property_val: str

    def __init__(self, label, lines, property_val, **kwargs):
        super().__init__(**kwargs)
        self._label = Label(label)
        self._input = Select((line, line) for line in lines)
        self._property_val = property_val

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str | None, str]:
        return (self._label.renderable, self._input.value, self._property_val)


class TestApp(App):
    BINDINGS = [
        ('h', 'dump_values', 'Generate Template'),
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
        self.call_cookie_template()

    @staticmethod
    def read_cookie_cutter() -> list[tuple[str, str]] | dict:
        """Helper method for reading cookiecutter.json"""
        fp = open('cookiecutter.json')
        cookie_handle = json.load(fp)
        if '__prompts__' in cookie_handle.keys():
            return cookie_handle
        return list(cookie_handle.items())

    @staticmethod
    def parse_cookie_cutter():
        """Helper method for parsing read_cookie_cutter"""
        template = TestApp.read_cookie_cutter()
        widgets = []
        if isinstance(template, dict):
            """The __prompts__ field is available"""
            prompts = template['__prompts__']
            for prompt in prompts.keys():
                if isinstance(template[prompt], str):
                    # template[prompt] is a default value
                        widgets.append(
                            TextQuestion(prompts[prompt], template[prompt], prompt))
                elif isinstance(template[prompt], list):
                    # templatep[prompt] is a list of options to choose from
                        widgets.append(
                            SelectQuestion(prompts[prompt], template[prompt], prompt))
        else:
            """No __prompts__"""
            for prompt in template:
                if prompt[0][0] != "_":
                    if isinstance(prompt[1], str):
                        # prompt[1] is a default value
                        widgets.append(TextQuestion(prompt[0], prompt[1], prompt[0]))
                    elif isinstance(prompt[1], list):
                        # prompt[2] is a list of options to choose from
                        widgets.append(SelectQuestion(prompt[0], prompt[1], prompt[0]))
        return widgets

    @staticmethod
    def read_copier() -> None:
        """ Placeholder for a helper method for reading copier.yml"""
        pass

    @staticmethod
    def parse_copier() -> None:
        """Placeholder for a helper method for parsing read_copier()"""
        pass

    def call_cookie_template(self, template="cookie", source='gh', owner="scientific-python", repo_name="cookie") -> None:#, template_name: str, repo_source: str, repo_owner: str, options) -> bool:
        """Method to call and dump the current inputs to the template"""
        textboxes = self.query(TextQuestion)
        selects = self.query(SelectQuestion)
        path = "~/.cookiecutters/{template}"
        path = os.path.expanduser(path.format(template=template))
        context = {}
        #TODO: The `context` builder breaks in the case `cookiecutter.json`
        # has the `__prompts__` field
        for text in textboxes:
            if text.value[1] != "":
                # if the user gave some input use that
                context[str(text.value[2])] = text.value[1]
            else:
                # ... else use the default (held in the placeholder)
                context[str(text.value[2])] = text._input.placeholder
        for select in selects:
            if select.value[1] != None:
                # If the user selected an input, use that
                context[str(select.value[2])] = select.value[1]
            else:
                # .. else use the intended default
                context[str(select.value[2])] = select._input._options[1][0]
        #TODO: Allow this to generalize to other `cookiecutter` templates other than
        #`cookie` in a more structured manner
        if not os.path.isdir("./tmp"):
            subprocess.run(["mkdir", "tmp"])
        try:
            cookiecutter(template=path, no_input=True, output_dir=os.path.expanduser('./tmp'),
                        extra_context=context)
        except RepositoryNotFound:
            #TODO: add arguments to method to allow for owner and repo_name to be passed in
            template_repo_source = "{}:{}/{}".format(source, owner, repo_name)
            cookiecutter(template=template_repo_source, no_input=True, output_dir=os.path.expanduser('./tmp'),
                                    extra_context=context)
        except OutputDirExistsException:
            subprocess.run(["rm", "-rf", "tmp"])
            subprocess.run(["mkdir", "tmp"])
            cookiecutter(template=path, no_input=True, output_dir=os.path.expanduser('./tmp'),
                                    extra_context=context)
            """Some code for removing existing directory and regenerating the project"""
            #TODO: Major problem is being able to grab the `TextQuestion` field with
            # the name of the directory being created, since it hasn't been explicitly
            # tagged with a DOM selector


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
