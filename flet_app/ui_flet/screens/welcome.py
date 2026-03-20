import flet as ft
import logging
from typing import Callable, List, Optional
from flet_app.ui_flet.theme import palette

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def WelcomeScreen(
    page: ft.Page,
    file_parser,
    student_name: str,
    student_data: Optional[dict],
    on_start: Callable[[str, str], None],
    on_quit_session: Callable,
    selected_file: str = "",
    debug_report: Optional[Callable[..., None]] = None,
):
    colors = palette(page)
    
    files: List[str] = file_parser.list_available_files()
    logger.debug(f"[WELCOME] Available files: {files}")
    
    # Check for empty file list and show error message
    if not files:
        logger.error("[WELCOME] CRITICAL: No vocabulary files available!")
        # Show error state instead of crashing
        error_card = ft.Container(
            content=ft.Column([
                ft.Text("No Vocabulary Files Found", size=24, weight=ft.FontWeight.BOLD, color=colors["danger"]),
                ft.Text("Please add vocabulary files to the saved_lists/ directory.", color=colors["muted"]),
                ft.Divider(height=20, color="transparent"),
                ft.Text("Expected format: CSV files with Chinese,English columns", color=colors["muted"], size=12),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=500,
            padding=40,
            bgcolor=colors["card_bg"],
            border_radius=15,
            border=ft.border.all(2, colors["danger"]),
            shadow=ft.BoxShadow(blur_radius=15, color="#0000001F", offset=ft.Offset(0, 4))
        )
        return ft.Container(content=error_card, alignment=ft.alignment.Alignment(0, 0), expand=True)
    
    dropdown_options = [ft.dropdown.Option(f) for f in files]
    # Pre-select file if in an active session, otherwise use first file
    default_file = selected_file if selected_file and selected_file in files else (files[0] if files else None)
    file_dropdown = ft.Dropdown(
        label="Select Vocabulary List",
        options=dropdown_options,
        value=default_file,
        color=colors["text"],
        border_color=colors["card_border"]
    )
    
    logger.debug(f"[WELCOME] Dropdown value set to: {file_dropdown.value}")

    def handle_start(e):
        if debug_report:
            debug_report("welcome_start_attempt", selected_file=file_dropdown.value, student_name=student_name)
        if not file_dropdown.value:
            file_dropdown.error_text = "Please select a vocabulary list"
            file_dropdown.update()
            if debug_report:
                debug_report("welcome_validation_error", reason="missing_file")
            return
        on_start(student_name, file_dropdown.value)

    header_text = "Study Dashboard" if student_name else "Welcome to Vocab Master"
    sub_text = f"Ready for another round, {student_name}?" if student_name else "Please identify yourself to begin."
    total_learned = (student_data or {}).get("total_words_learned", 0)

    # Modern Card Layout
    form_card = ft.Container(
        content=ft.Column([
            ft.Text(header_text, size=32, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Text(sub_text, color=colors["primary"] if student_name else colors["muted"], size=18 if student_name else 16),
            ft.Text("Select a vocabulary list to continue.", color=colors["muted"]),
            ft.Divider(height=20, color="transparent"),
            file_dropdown,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Configure Quiz →", 
                on_click=handle_start,
                style=ft.ButtonStyle(
                    padding=20,
                    bgcolor=colors["primary"],
                    color=colors["primary_text"],
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=420
            ),
            ft.Text(
                f"Cumulative Words Learned: {total_learned}",
                color=colors["muted"],
                italic=True,
                visible=bool(student_name),
            ),
            ft.Container(height=20, bgcolor="transparent"),
            ft.TextButton(
                "Quit Session",
                on_click=lambda e: on_quit_session(),
                style=ft.ButtonStyle(
                    color=colors["danger"],
                    padding=10
                )
            )
        ]),
        width=500,
        padding=40,
        bgcolor=colors["card_bg"],
        border=ft.border.all(1, colors["card_border"]),
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color="#0000001F", offset=ft.Offset(0, 4))
    )

    return ft.Container(content=form_card, alignment=ft.alignment.Alignment(0, 0), expand=True)
