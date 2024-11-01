from __future__ import annotations

import argparse
import base64
import enum
import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar

import requests
import yaml
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter
from copier.errors import UnsafeTemplateError
from copier.main import run_copy
from rich.console import ConsoleRenderable, RenderableType, RichCast
from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.events import Key
from textual.reactive import var
from textual.widgets import Footer, Input, Label, Select, Static, TabbedContent, TabPane

from .code_browser import CodeBrowserWidget


class Backend(enum.Enum):
    cookie = enum.auto()
    copier = enum.auto()


NAMES = ["Form", "Code-Browser"]


class TextQuestion(Static):
    def __init__(self, placeholder: str, property_val: str, prompt: str, **kwargs: Any):
        super().__init__(**kwargs)
        self._label = Label(prompt)
        self._input = Input(placeholder=placeholder)
        self._property_val = property_val
        self._prompt = prompt

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str, str]:
        return (self._label.renderable, self._input.value, self._property_val)

    def watch_mouse_over(self, value: bool) -> None:
        if value:
            self._label.update(self._property_val)
        else:
            self._label.update(self._prompt)


class SelectQuestion(Static):
    def __init__(
        self,
        lines: Iterable[str],
        property_val: str,
        prompt: str,
        _extras: dict[str, str] | None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._label = Label(prompt)
        self._input = Select((line, line) for line in lines)
        self._property_val = property_val
        self._prompt = prompt
        self._extras = _extras

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._input

    @property
    def value(self) -> tuple[RenderableType, str | None, str, dict[str, str] | None]:
        select_value = self._input.value
        return (
            self._label.renderable,
            select_value if isinstance(select_value, str) else None,
            self._property_val,
            self._extras,
        )

    def watch_mouse_over(self, value: bool) -> None:
        if value:
            self._label.update(self._property_val)
        else:
            self._label.update(self._prompt)


class TestApp(App[None]):
    BINDINGS: ClassVar = [
        ("h", "dump_values", "Generate Template"),
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

    def __init__(
        self, backend: Backend, template: Path, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self._backend = backend
        self._template = template
        # HACK, structure this out better
        path_string = str(template)
        if "gh" in path_string:
            self._repo_owner = path_string[3 : path_string.index("/")]
            self._repo_name = path_string[path_string.index("/") + 1 :]

    def on_mount(self, _event: events.Mount) -> None:
        self.query_one(TabbedContent).focus()

    def compose(self) -> ComposeResult:
        if self._backend == Backend.copier:
            form_widgets = self.parse_copier()
        else:
            form_widgets = self.parse_cookie_cutter()
        with TabbedContent():
            with TabPane("Form", id="form"):
                yield VerticalScroll(*form_widgets)
            with TabPane("Code-Browser", id="code-browser"):
                yield CodeBrowserWidget()
        yield Footer()

    def action_dump_values(self) -> None:
        if self._backend == Backend.copier:
            self.call_copier_template()
        else:
            self.call_cookie_template()

    def read_cookie_cutter(
        self, repo_owner: str | None, repo_name: str | None
    ) -> list[tuple[str, str]] | dict[str, Any]:
        """Helper method for reading cookiecutter.json"""
        cookie_handle: dict[str, Any]
        if self._template.exists():
            with self._template.joinpath("cookiecutter.json").open(
                encoding="utf-8"
            ) as fp:
                cookie_handle = json.load(fp)
        elif repo_owner is not None and repo_name is not None:
            f = self.grab_github(repo_owner, repo_name)
            cookie_handle = json.loads(f)
        else:
            msg = "No template found"
            raise ValueError(msg)
        if "__prompts__" in cookie_handle:
            return cookie_handle
        return list(cookie_handle.items())

    def parse_cookie_cutter(self) -> list[SelectQuestion | TextQuestion]:
        """Helper method for parsing read_cookie_cutter"""
        if hasattr(self, "_repo_owner"):
            template = self.read_cookie_cutter(self._repo_owner, self._repo_name)
        else:
            template = self.read_cookie_cutter(None, None)
        widgets: list[SelectQuestion | TextQuestion] = []
        if isinstance(template, dict):
            # The __prompts__ field is available
            prompts = template["__prompts__"]
            for prompt in prompts:
                if isinstance(template[prompt], str):
                    # template[prompt] is a default value
                    widgets.append(
                        TextQuestion(template[prompt], prompt, prompts[prompt])
                    )
                elif isinstance(template[prompt], list):
                    # template[prompt] is a list of options to choose from
                    if isinstance(prompts[prompt], dict):
                        # In this case, we have a 'list' type choice, which has some additional
                        # information provided via a dictionary
                        tmp = prompts[prompt].copy()
                        del tmp["__prompt__"]
                        inv_map = {v: k for k, v in tmp.items()}
                        widgets.append(
                            SelectQuestion(
                                list(tmp.values()),
                                prompt,
                                prompts[prompt]["__prompt__"],
                                inv_map,
                            )
                        )
                    else:
                        widgets.append(
                            SelectQuestion(
                                template[prompt], prompt, prompts[prompt], None
                            )
                        )
        else:
            # No __prompts__
            for prompt in template:
                if prompt[0][0] != "_":
                    if isinstance(prompt[1], str):
                        # prompt[1] is a default value
                        widgets.append(TextQuestion(prompt[1], prompt[0], prompt[0]))
                    elif isinstance(prompt[1], list):
                        # prompt[2] is a list of options to choose from
                        widgets.append(
                            SelectQuestion(prompt[1], prompt[0], prompt[0], None)
                        )
        return widgets

    def read_copier(
        self, repo_owner: str | None, repo_name: str | None
    ) -> list[tuple[str, dict[str, str]]]:
        """Helper method for reading in copier.yml"""
        copier_handle = None
        if self._template.exists():
            with self._template.joinpath("copier.yml").open(encoding="utf-8") as fp:
                copier_handle = yaml.safe_load(fp)
        elif repo_owner is not None and repo_name is not None:
            f = self.grab_github(repo_owner, repo_name)
            copier_handle = yaml.safe_load(f)
        else:
            msg = "No template found"
            raise ValueError(msg)
        return list(copier_handle.items())

    def parse_copier(self) -> list[SelectQuestion | TextQuestion]:
        """Helper method for parsing read_copier's output"""
        if hasattr(self, "_repo_owner"):
            template = self.read_copier(self._repo_owner, self._repo_name)
        else:
            template = self.read_copier(None, None)
        widgets: list[SelectQuestion | TextQuestion] = []
        for prompt in template:
            if prompt[0][0] != "_":
                if "choices" in prompt[1]:
                    # A `SelectQuestion` field
                    if isinstance(prompt[1]["choices"], dict):
                        # The choices in copier can be specified eithe
                        # via a dictionary....
                        if "help" in prompt[1]:
                            # if descriptions for fields exist
                            widgets.append(
                                SelectQuestion(
                                    prompt[1]["choices"].keys(),
                                    prompt[0],
                                    prompt[1]["help"],
                                    prompt[1]["choices"],
                                )
                            )
                        else:
                            # ... if they do not
                            widgets.append(
                                SelectQuestion(
                                    prompt[1]["choices"].keys(),
                                    prompt[0],
                                    prompt[0],
                                    prompt[1]["choices"],
                                )
                            )
                    # .... Or as a list
                    elif "help" in prompt[1]:
                        # if descriptions for fields exist
                        widgets.append(
                            SelectQuestion(
                                prompt[1]["choices"],
                                prompt[0],
                                prompt[1]["help"],
                                None,
                            )
                        )
                    else:
                        # ... if they do not
                        widgets.append(
                            SelectQuestion(
                                prompt[1]["choices"], prompt[0], prompt[0], None
                            )
                        )
                # A `TextQuestion` field
                elif "help" in prompt[1]:
                    # If descriptions for fields exist
                    # TODO: Figure out how to deal with
                    # `placeholder` and `default` fields
                    if "placeholder" in prompt[1]:
                        if "default" in prompt[1]:
                            # Can have both defaults + placeholders in this case
                            q = TextQuestion(
                                prompt[1]["placeholder"],
                                prompt[0],
                                prompt[1]["help"],
                            )
                            q._input.value = prompt[1]["default"]
                            widgets.append(q)
                        else:
                            # Placeholder, but no default
                            widgets.append(
                                TextQuestion(
                                    prompt[1]["placeholder"],
                                    prompt[0],
                                    prompt[1]["help"],
                                )
                            )
                    elif "default" in prompt[1]:
                        # Only a default
                        q = TextQuestion("", prompt[0], prompt[1]["help"])
                        q._input.value = prompt[1]["default"]
                        widgets.append(q)
                    else:
                        # Only a help text, and no placeholder nor a default
                        widgets.append(TextQuestion("", prompt[0], prompt[1]["help"]))
                else:
                    # ... in case they do not
                    widgets.append(TextQuestion("", prompt[0], prompt[0]))
        return widgets

    def call_cookie_template(self) -> None:
        """Method to call and dump the current inputs to the template"""
        textboxes = self.query(TextQuestion)
        selects = self.query(SelectQuestion)
        context: dict[str, ConsoleRenderable | RichCast | str] = {}
        # TODO: The `context` builder breaks in the case `cookiecutter.json`
        # has the `__prompts__` field
        for text in textboxes:
            if text.value[1]:
                # if the user gave some input use that
                context[str(text.value[2])] = text.value[1]
            else:
                # ... else use the default (held in the placeholder)
                context[str(text.value[2])] = text._input.placeholder
        for select in selects:
            if select.value[1] is not None:
                # If the user selected an input, use that
                if select.value[-1] is not None:
                    # in case this is a select field which is represented as a dict
                    context[str(select.value[2])] = select.value[-1][select.value[1]]
                else:
                    context[str(select.value[2])] = select.value[1]
            # .. else use the intended default
            elif select.value[-1] is not None:
                # Again, while choosing defaults checks if the select-field is represented
                # as a `dict`
                context[str(select.value[2])] = select.value[-1][
                    str(select._input._options[1][0])
                ]
            # .. else use the intended default
            elif select.value[-1] is not None:
                # Again, while choosing defaults checks if the select-field is represented
                # as a `dict`
                value = select.value[-1][list(select._input._options)[1][0]]
                context[str(select.value[2])] = value
            else:
                context[str(select.value[2])] = list(select._input._options)[1][0]
        # TODO: Allow this to generalize to other `cookiecutter` templates other than
        # `cookie` in a more structured manner
        tmp_path = Path("tmp")
        tmp_path.mkdir(exist_ok=True)
        try:
            cookiecutter(
                template=str(self._template),
                no_input=True,
                output_dir="tmp",
                extra_context=context,
            )
        except OutputDirExistsException:
            shutil.rmtree("tmp", ignore_errors=True)
            Path("tmp").mkdir(exist_ok=True)
            cookiecutter(
                template=str(self._template),
                no_input=True,
                output_dir="tmp",
                extra_context=context,
            )
            # Some code for removing existing directory and regenerating the project
            # That code should go into the handler for the button/binding that is pressed
            # for committing changes

    def call_copier_template(self) -> None:
        textboxes = self.query(TextQuestion)
        selects = self.query(SelectQuestion)
        context: dict[str, ConsoleRenderable | RichCast | str] = {}
        for text in textboxes:
            if text.value[1]:
                # if the user gave some input use that
                context[str(text.value[2])] = text.value[1]
            else:
                # in copier's case, there is no necessitating supplying
                # the `default` field for a template, so we cannot proceed
                # here and just have to show an appropriate error message
                # to the user
                # TODO: Make this an error prompt
                return
                # context[str(text.value[2])] = text._input.placeholder
        for select in selects:
            if select.value[1] is not None:
                # If the user selected an input, use that
                if select.value[3] is None:
                    # This particular `SelectQuestion` question had it's
                    # `choices` field provided as a list
                    context[str(select.value[2])] = select.value[1]
                else:
                    # This particular `SelectQuestion` question had it's
                    # `choices` field provided as a dict
                    context[str(select.value[2])] = select.value[3][select.value[1]]
            else:
                # .. else use the first option as the intended default
                context[str(select.value[2])] = list(select._input._options)[1][0]
        tmp_path = Path("tmp")
        tmp_path.mkdir(exist_ok=True)
        # with open("test.txt", "w") as op_file:
        #     op_file.write(json.dumps(context))
        try:
            run_copy(src_path=str(self._template), dst_path="tmp", data=context)
        except UnsafeTemplateError:
            run_copy(
                src_path=str(self._template),
                dst_path="tmp",
                data=context,
                unsafe=True,
            )

    def grab_github(self, repo_owner: str, repo_name: str) -> str:
        if self._backend == Backend.copier:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/copier.yml"
        else:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/cookiecutter.json"
        response = requests.get(url, timeout=5)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Attempt to decode the response content as JSON
            file_info = response.json()
            file_content = base64.b64decode(file_info["content"]).decode("utf-8")
        else:
            msg = f"Error: {response.status_code}"
            raise RuntimeError(msg)
        return file_content

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        if self.query_one(TabbedContent).active == "code-browser":
            self.show_tree = not self.show_tree

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        if self.query_one(TabbedContent).active == "code-browser":
            self.set_class(show_tree, "-show-tree")

    @on(Key)
    def tab_shift_tab_pressed(self, event: Key) -> None:
        """Placeholder for writing to output when TAB/s-TAB is detected in the input-stream"""
        if event.key == "return":
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "backend",
        type=lambda x: getattr(Backend, x),
        help="Pick a backend",
        choices=list(Backend),
    )
    parser.add_argument("template", type=Path, help="Path to template directory")
    args = parser.parse_args()
    TestApp(args.backend, args.template).run()


if __name__ == "__main__":
    main()
