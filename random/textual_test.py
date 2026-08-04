from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Footer,
    Header,
    Input,
    Label,
    ListView,
    LoadingIndicator,
    TabbedContent,
    TabPane,
    Tabs,
)


class CreateTab(Widget):
    DEFAULT_CSS = """
        CreateTab {
            height: auto;
            width: 1fr;
        }
    """

    def compose(self) -> ComposeResult:
        yield Label("Create something")
        yield Input("Enter something")
        yield Button("Submit")

    def on_button_presses(self, event) -> None:
        print("pressed")


class ArchiveTab(Widget):
    DEFAULT_CSS = """
        ArchiveTab {
            height: auto;
            width: 1fr;
        }
    """

    def compose(self) -> ComposeResult:
        yield Label("Archive view")


class TestApp(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    CSS = """
          Tab {
              text-style: bold;
              padding: 0 2;
          }
          """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with TabbedContent():
            with TabPane("Create", id="create"):
                yield CreateTab()
            with TabPane("Archive", id="archive"):
                yield ArchiveTab()

    def on_mount(self) -> None:
        self.title = "Custom Name"

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = TestApp()
    app.run()
