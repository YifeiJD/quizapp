import flet as ft
import logging
from typing import Callable, Optional
from flet_app.ui_flet.theme import palette

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def NameEntryScreen(page: ft.Page, on_name_submit: Callable[[str], None], debug_report: Optional[Callable[..., None]] = None):
    """Screen for entering student name. Only shown at app start or when quitting session."""
    colors = palette(page)
    name_input = ft.TextField(
        label="Your Name",
        hint_text="e.g. John Doe",
        border_color=colors["card_border"],
        color=colors["text"],
        autofocus=True
    )

    def handle_submit(e):
        if debug_report:
            debug_report("name_entry_submit_attempt", raw_value=name_input.value or "")
        if not name_input.value.strip():
            name_input.error_text = "Please enter your name"
            name_input.update()
            if debug_report:
                debug_report("name_entry_validation_error", reason="empty_name")
            return
        if debug_report:
            debug_report("name_entry_submit_success", name=name_input.value.strip())
        on_name_submit(name_input.value.strip())

    # Handle Enter key
    def on_key(e):
        if e.key == "Enter":
            handle_submit(None)

    name_input.on_submit = handle_submit

    # Modern Card Layout
    form_card = ft.Container(
        content=ft.Column([
            ft.Text("Vocab Master", size=32, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Text("Enter your name to begin or resume your session.", color=colors["muted"]),
            ft.Divider(height=30, color="transparent"),
            name_input,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Continue →",
                on_click=handle_submit,
                style=ft.ButtonStyle(
                    padding=20,
                    bgcolor=colors["primary"],
                    color=colors["primary_text"],
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=420
            )
        ]),
        width=500,
        padding=40,
        bgcolor=colors["card_bg"],
        border=ft.border.all(1, colors["card_border"]),
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=25, color="#00000014", offset=ft.Offset(0, 8))
    )

    return ft.Container(content=form_card, alignment=ft.alignment.Alignment(0, 0), expand=True)
