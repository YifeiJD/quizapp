import os
import sys
import asyncio

# Ensure shared root modules can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import flet as ft
import logging
from pathlib import Path
from core.debug_report import configure_debug_logging, emit_debug_report
from core.admin_settings import AdminSettings
from core.quiz_engine import QuizEngine
from flet_app.app_config import (
    APP_SHELL_PADDING,
    DEFAULT_APP_RESOLUTION,
    TOP_WINDOW_MARGIN,
    configure_page,
    log_flet_version,
    window_size_for_resolution,
)
from flet_app.app_services import build_services
from flet_app.app_state import AppState
from flet_app.session_utils import build_session_report, session_totals
from flet_app.ui_flet.theme import palette

# Configure logging
LOG_PATH = configure_debug_logging("flet_app.log")
logger = logging.getLogger(__name__)

# UI Imports
from flet_app.ui_flet.layout import AppLayout
from flet_app.ui_flet.screens.name_entry import NameEntryScreen
from flet_app.ui_flet.screens.welcome import WelcomeScreen
from flet_app.ui_flet.screens.quiz_config import QuizConfigScreen
from flet_app.ui_flet.screens.quiz import QuizScreen
from flet_app.ui_flet.screens.results import ResultsScreen
from flet_app.ui_flet.screens.settings import SettingsScreen
from flet_app.ui_flet.screens.personal_history import PersonalHistoryScreen
from flet_app.ui_flet.screens.session_summary import SessionSummaryScreen
from flet_app.ui_flet.screens.admin_database import AdminDatabaseScreen


def main(page: ft.Page):
    log_flet_version(logger)
    configure_page(page, DEFAULT_APP_RESOLUTION)
    is_vscode_runtime = os.environ.get("TERM_PROGRAM") == "vscode" or bool(os.environ.get("VSCODE_PID"))

    # --- Core Services ---
    services = build_services()
    admin_settings = AdminSettings()
    pending_report = {"content": "", "filename": "session_report.txt"}
    export_dir = Path(ROOT_DIR) / "debug_reports" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    def handle_report_save(e) -> None:
        if not e.path:
            return
        Path(e.path).write_text(pending_report["content"], encoding="utf-8")
        _show_message(f"Report saved to {e.path}", ft.Colors.PRIMARY_CONTAINER)

    report_picker = None

    def _save_report_to_default_location() -> Path:
        output_path = export_dir / pending_report["filename"]
        output_path.write_text(pending_report["content"], encoding="utf-8")
        return output_path

    # --- Application State ---
    state = AppState(app_resolution=DEFAULT_APP_RESOLUTION)
    window_centered = {"done": False}

    def _normalize_student_name(name: str) -> str:
        parts = [part for part in (name or "").strip().split() if part]
        return " ".join(part[:1].upper() + part[1:].lower() for part in parts)

    def _position_window_top_center() -> None:
        try:
            page.window.center()
            page.window.top = TOP_WINDOW_MARGIN
        except Exception:
            pass

    async def _stabilize_window_geometry(width: int, height: int) -> None:
        window_width, window_height = window_size_for_resolution((width, height))
        for _ in range(3):
            await asyncio.sleep(0.12)
            try:
                page.window.width = window_width
                page.window.height = window_height
                _position_window_top_center()
                page.update()
            except Exception:
                return

    def _debug_report(event: str, **details) -> None:
        emit_debug_report(
            logger,
            "DEBUG-REPORT",
            event,
            details=details,
            state=state.snapshot(page),
        )

    def _handle_page_error(e) -> None:
        _debug_report("page_error", data=getattr(e, "data", None), name=getattr(e, "name", None))

    def _handle_lifecycle_change(e) -> None:
        _debug_report("lifecycle", data=getattr(e, "data", None))
        if getattr(e, "data", None) in {"show", "resume"} and not window_centered["done"]:
            try:
                window_centered["done"] = True
                page.run_task(
                    _stabilize_window_geometry,
                    state.app_resolution[0],
                    state.app_resolution[1],
                )
            except Exception:
                pass

    page.on_error = _handle_page_error
    page.on_app_lifecycle_state_change = _handle_lifecycle_change
    _debug_report("app_started", debug_log_path=str(LOG_PATH))

    # --- Navigation ---
    def handle_nav_change(e):
        try:
            selected = int(e.data) if e.data is not None else e.control.selected_index
        except (TypeError, ValueError):
            selected = e.control.selected_index
        _debug_report("nav_change", selected=selected, raw_data=getattr(e, "data", None))
        if selected == 0:
            show_welcome()
        elif selected == 1:
            show_personal_history()
        elif selected == 2:
            show_session_summary()
        elif selected == 3:
            show_settings()
    
    def _toggle_theme(is_dark: bool) -> None:
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        _apply_shell_theme()
        layout.apply_theme()
        _debug_report("theme_toggle", is_dark=is_dark)
        rerender_current_view()

    def _apply_shell_theme() -> None:
        colors = palette(page)
        if state.admin_mode:
            page.bgcolor = "#2B160B" if page.theme_mode == ft.ThemeMode.DARK else "#FEF3C7"
            app_shell.bgcolor = page.bgcolor
            app_surface.bgcolor = "#1F2937" if page.theme_mode == ft.ThemeMode.DARK else "#FFF7ED"
        else:
            page.bgcolor = colors["page_bg"]
            app_shell.bgcolor = colors["page_bg"]
            app_surface.bgcolor = colors["workspace_bg"]

    def _confirm_action(title: str, message: str, on_confirm) -> None:
        _debug_report("confirm_open", title=title, message=message)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: _close_dialog(dialog)),
                ft.ElevatedButton("Continue", on_click=lambda e: _confirm_and_close(dialog, on_confirm)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def _close_dialog(dialog) -> None:
        dialog.open = False
        _debug_report("dialog_close")
        page.update()

    def _confirm_and_close(dialog, on_confirm) -> None:
        _close_dialog(dialog)
        on_confirm()

    def rerender_current_view() -> None:
        view = state.current_view
        _debug_report("rerender_view", target_view=view)
        if view == "name_entry":
            show_name_entry()
        elif view == "welcome":
            show_welcome()
        elif view == "quiz_config":
            show_quiz_config()
        elif view == "quiz":
            show_quiz()
        elif view == "settings":
            show_settings()
        elif view == "history":
            show_personal_history()
        elif view == "summary":
            show_session_summary()
        elif view == "admin":
            show_admin_database()
        elif view == "results" and state.last_quiz_data:
            quiz_data = state.last_quiz_data
            show_results(quiz_data["score"], quiz_data["total"])

    layout = AppLayout(page, handle_nav_change, _toggle_theme, state.app_resolution)
    app_surface = ft.Container(
        content=layout,
        width=state.app_resolution[0],
        height=state.app_resolution[1],
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=24, color="#00000024", offset=ft.Offset(0, 10)),
        bgcolor=palette(page)["workspace_bg"],
    )
    app_shell = ft.Container(
        content=app_surface,
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        padding=APP_SHELL_PADDING,
        bgcolor=palette(page)["page_bg"],
    )
    page.add(app_shell)
    layout.initialize()
    _apply_shell_theme()
    page.run_task(_stabilize_window_geometry, state.app_resolution[0], state.app_resolution[1])

    def _cleanup_workspace_content() -> None:
        """Run screen cleanup hooks before replacing the current content."""
        current_content = layout.content_host.controls[0] if layout.content_host.controls else None
        cleanup = getattr(current_content, "cleanup", None)
        if callable(cleanup):
            _debug_report("workspace_cleanup", content_type=type(current_content).__name__)
            cleanup()

    def _show_message(message: str, color: str = ft.Colors.ERROR_CONTAINER) -> None:
        """Show a transient message to the user."""
        _debug_report("toast", message=message, color=str(color))
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            open=True,
        )
        page.update()

    def _change_resolution(new_res):
        width, height = new_res
        window_width, window_height = window_size_for_resolution((width, height))
        state.app_resolution = (width, height)
        layout.set_surface_size(width, height)
        app_surface.width = width
        app_surface.height = height
        page.window.width = window_width
        page.window.height = window_height
        _position_window_top_center()
        page.update()
        page.run_task(_stabilize_window_geometry, width, height)
        _debug_report("resolution_change", width=width, height=height)
        _show_message(f"App viewport updated to {width} x {height}", ft.Colors.PRIMARY_CONTAINER)

    def _full_reset() -> None:
        _debug_report("full_reset")
        _clear_quiz_bindings()
        state.reset_session()
        layout.set_student("")
        layout.set_nav_enabled(False)
        layout.update_stats(0, 0)
        show_name_entry()

    def _request_full_reset() -> None:
        _confirm_action(
            "Reset Entire Session",
            "This will clear the active student, in-memory session history, and current quiz progress.",
            _full_reset,
        )

    def _download_session_report() -> None:
        if not state.session_history:
            _show_message("Complete at least one quiz before downloading a report.", ft.Colors.PRIMARY_CONTAINER)
            return
        pending_report["content"] = build_session_report(state.student_name, state.session_history)
        safe_name = (state.student_name or "session").replace(" ", "_")
        pending_report["filename"] = f"{safe_name}_Report.txt"
        _debug_report("report_save_requested", filename=pending_report["filename"])
        if is_vscode_runtime:
            saved_path = _save_report_to_default_location()
            _show_message(f"Report saved to {saved_path}", ft.Colors.PRIMARY_CONTAINER)
            return

        try:
            nonlocal report_picker
            if report_picker is None:
                report_picker = ft.FilePicker()
                report_picker.on_result = handle_report_save
                page.overlay.append(report_picker)
                page.update()
            report_picker.save_file(
                dialog_title="Save Session Report",
                file_name=pending_report["filename"],
                allowed_extensions=["txt"],
            )
        except Exception as exc:
            _debug_report("report_save_fallback", error=str(exc))
            saved_path = _save_report_to_default_location()
            _show_message(f"Report saved to {saved_path}", ft.Colors.PRIMARY_CONTAINER)

    def _clear_quiz_bindings() -> None:
        """Remove quiz-specific page handlers when leaving the quiz screen."""
        page.on_keyboard_event = None
        _debug_report("clear_quiz_bindings")

    def _update_sidebar_stats() -> None:
        """Update sidebar statistics based on current session."""
        history = state.session_history
        if not history:
            layout.update_stats(0, 0)
            return

        total_correct, total_attempted = session_totals(history)
        layout.update_stats(total_correct, total_attempted)

    def _quit_session() -> None:
        """Quit current session and return to name entry."""
        _debug_report("quit_session")
        _clear_quiz_bindings()
        state.reset_session()
        layout.set_student("")
        layout.set_nav_enabled(False)
        layout.update_stats(0, 0)
        show_name_entry()

    def _close_admin_database() -> None:
        state.admin_mode = False
        layout.set_admin_mode(False)
        _apply_shell_theme()
        if state.admin_entry_route:
            _debug_report("admin_logout_to_begin")
            state.reset_session()
            layout.set_student("")
            layout.set_nav_enabled(False)
            layout.update_stats(0, 0)
            show_name_entry()
            return
        if state.pending_deleted_active_student:
            _debug_report("admin_close_with_deleted_active_student")
            state.reset_session()
            layout.set_student("")
            layout.set_nav_enabled(False)
            layout.update_stats(0, 0)
            show_name_entry()
            return
        if state.student_name:
            state.student_data = services.db.get_student(state.student_name) or {"sessions": []}
            layout.set_student(state.student_name)
        show_settings()

    def _open_admin_gate(from_name_entry: bool = False) -> None:
        password_input = ft.TextField(
            label="Admin Password",
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        dialog = None

        def submit_admin_password(_=None):
            if admin_settings.verify_password(password_input.value or ""):
                _close_dialog(dialog)
                state.admin_entry_route = from_name_entry
                show_admin_database()
                return
            password_input.error_text = "Incorrect password"
            password_input.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Admin Access Required"),
            content=password_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: _close_dialog(dialog)),
                ft.ElevatedButton("Enter Admin Panel", on_click=submit_admin_password),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        password_input.on_submit = submit_admin_password
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def _change_admin_password(current_password: str, new_password: str, confirm_password: str) -> bool:
        if not admin_settings.verify_password(current_password):
            _show_message("Current admin password is incorrect.")
            return False
        if not new_password.strip():
            _show_message("Enter a new admin password.")
            return False
        if new_password != confirm_password:
            _show_message("New password and confirmation do not match.")
            return False
        admin_settings.set_password(new_password)
        _debug_report("admin_password_changed")
        _show_message("Admin password updated.", ft.Colors.PRIMARY_CONTAINER)
        return True

    # --- Screen Display Functions ---

    def show_name_entry():
        state.current_view = "name_entry"
        _debug_report("show_name_entry")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.rail.selected_index = 0
        layout.set_content(NameEntryScreen(page, on_name_entered, _debug_report), centered=True)
        page.update()

    def on_name_entered(name: str):
        normalized_name = _normalize_student_name(name)
        if normalized_name.lower() == "admin":
            _debug_report("admin_name_entry_route")
            _open_admin_gate(from_name_entry=True)
            return
        state.student_name = normalized_name
        layout.set_student(normalized_name)
        _debug_report("name_entered", name=normalized_name, raw_name=name)
        layout.set_nav_enabled(True)
        
        student_data = services.db.get_student(normalized_name)
        state.student_data = student_data or {"sessions": []}
        
        # Reset session-specific stats when a new student is entered
        state.session_history = []
        _update_sidebar_stats()
        
        show_welcome()

    def show_welcome():
        state.current_view = "welcome"
        _debug_report("show_welcome")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.set_nav_enabled(bool(state.student_name))
        layout.rail.selected_index = 0
        layout.set_content(WelcomeScreen(
            page=page,
            file_parser=services.file_parser,
            student_name=state.student_name,
            student_data=state.student_data,
            on_start=start_quiz_setup,
            on_quit_session=_quit_session,
            selected_file=state.current_vocab_file
            ,
            debug_report=_debug_report,
        ), centered=True)
        page.update()

    def show_quiz_config():
        state.current_view = "quiz_config"
        _debug_report("show_quiz_config")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.set_nav_enabled(bool(state.student_name))
        layout.rail.selected_index = 0
        saved_config = (state.student_data or {}).get("last_config", {})
        
        layout.set_content(QuizConfigScreen(
            page=page,
            total_available=len(state.current_vocab),
            on_start_quiz=start_quiz,
            on_back=show_welcome,
            saved_config=saved_config,
            debug_report=_debug_report,
        ), centered=True)
        page.update()

    def show_quiz():
        state.current_view = "quiz"
        _debug_report("show_quiz")
        _cleanup_workspace_content()
        layout.set_nav_enabled(bool(state.student_name))
        layout.rail.selected_index = 0
        layout.set_content(QuizScreen(page, state.quiz_engine, finish_quiz, _debug_report), centered=True)
        page.update()
        current_content = layout.content_host.controls[0] if layout.content_host.controls else None
        start = getattr(current_content, "start", None)
        if callable(start):
            start()

    def show_settings():
        state.current_view = "settings"
        _debug_report("show_settings")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.set_nav_enabled(bool(state.student_name))
        layout.rail.selected_index = 3
        layout.set_content(SettingsScreen(
            page=page,
            current_resolution=state.app_resolution,
            on_resolution_change=_change_resolution,
            on_reset_session=_request_full_reset,
            on_back=show_welcome,
            on_view_history=show_personal_history,
            on_quit_session=_quit_session,
            on_session_summary=show_session_summary,
            on_administer_records=lambda: _open_admin_gate(from_name_entry=False),
            debug_report=_debug_report,
        ), centered=False)
        page.update()

    def _delete_student_record(student_name: str) -> None:
        def do_delete():
            deleted = services.db.delete_student(student_name)
            _debug_report("admin_delete_student", student_name=student_name, deleted=deleted)
            if deleted and state.student_name == student_name:
                state.pending_deleted_active_student = True
            if deleted and state.student_name != student_name:
                _show_message(f"Deleted student record for {student_name}.", ft.Colors.PRIMARY_CONTAINER)
            show_admin_database()

        _confirm_action(
            "Delete Student Record",
            f"Delete {student_name} and all saved sessions from the database?",
            do_delete,
        )

    def _delete_student_session(student_name: str, session_index: int) -> None:
        def do_delete():
            deleted = services.db.delete_session(student_name, session_index)
            _debug_report("admin_delete_session", student_name=student_name, session_index=session_index, deleted=deleted)
            if deleted:
                _show_message("Deleted saved session record.", ft.Colors.PRIMARY_CONTAINER)
            show_admin_database()

        _confirm_action(
            "Delete Saved Session",
            f"Delete session #{session_index + 1} for {student_name} from the database?",
            do_delete,
        )

    def _list_wordlists() -> list[str]:
        files = services.file_parser.list_available_files()
        _debug_report("admin_wordlists_listed", count=len(files), files=files)
        return files

    def _preview_wordlist(filename: str) -> dict:
        safe_filename = os.path.basename(filename)
        path = os.path.join(services.file_parser.save_dir, safe_filename)
        vocab = services.file_parser.parse_file(path)
        preview_entries = list(vocab.items())[:100]
        _debug_report(
            "admin_wordlist_preview",
            filename=safe_filename,
            entries=len(preview_entries),
            error=services.file_parser.last_error,
        )
        return {
            "entries": preview_entries,
            "error": services.file_parser.last_error,
        }

    def _delete_wordlist(filename: str) -> None:
        safe_filename = os.path.basename(filename)

        def do_delete():
            path = os.path.join(services.file_parser.save_dir, safe_filename)
            deleted = False
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    deleted = True
                    if state.current_vocab_file == safe_filename:
                        state.current_vocab_file = None
                        state.current_vocab = {}
                _debug_report("admin_delete_wordlist", filename=safe_filename, deleted=deleted)
            except Exception as exc:
                _debug_report("admin_delete_wordlist_failed", filename=safe_filename, error=str(exc))
                _show_message(f"Could not delete {safe_filename}.")
                return

            if deleted:
                _show_message(f"Deleted word list {safe_filename}.", ft.Colors.PRIMARY_CONTAINER)
            else:
                _show_message(f"{safe_filename} was not found.")
            show_admin_database()

        _confirm_action(
            "Delete Word List",
            f"Delete {safe_filename} from the saved vocabulary lists?",
            do_delete,
        )

    def show_admin_database():
        state.current_view = "admin"
        state.admin_mode = True
        _debug_report("show_admin_database")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.set_student("Admin")
        layout.set_admin_mode(True)
        _apply_shell_theme()
        layout.set_nav_enabled(True)
        layout.rail.selected_index = 3
        layout.set_content(
            AdminDatabaseScreen(
                page=page,
                students=services.db.get_all_students(),
                on_back=_close_admin_database,
                on_delete_student=_delete_student_record,
                on_delete_session=_delete_student_session,
                on_change_password=_change_admin_password,
                get_wordlists=_list_wordlists,
                preview_wordlist=_preview_wordlist,
                on_delete_wordlist=_delete_wordlist,
                debug_report=_debug_report,
            ),
            centered=False,
        )
        page.update()

    def show_results(score, total):
        state.current_view = "results"
        _debug_report("show_results", score=score, total=total, quiz_mode=state.quiz_mode)
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        layout.set_nav_enabled(bool(state.student_name))
        layout.rail.selected_index = 0
        engine = state.quiz_engine
        has_mistakes = engine and len(engine.session_mistakes) > 0
        
        def on_practice_click(e):
            if engine and engine.session_mistakes:
                state.quiz_mode = "practice"
                state.practice_parent_index = len(state.session_history) - 1 if state.session_history else None
                _debug_report("start_practice_mistakes", parent_index=state.practice_parent_index)
                engine.practice_mistakes()
                engine.timer_running = True
                show_quiz()
        
        layout.set_content(ResultsScreen(
            page=page,
            student_name=state.student_name,
            score=score,
            total=total,
            results_log=list(engine.results_log) if engine else [],
            on_home=lambda e: show_welcome(),
            on_practice=on_practice_click if has_mistakes else None,
            on_quit_session=_quit_session,
            debug_report=_debug_report,
        ), centered=True)
        page.update()

    def show_personal_history():
        state.current_view = "history"
        _debug_report("show_personal_history")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        if not state.student_data:
            layout.set_nav_enabled(False)
            layout.rail.selected_index = 0
            _show_message("Enter a student name before opening history.", ft.Colors.PRIMARY_CONTAINER)
            return
        layout.set_nav_enabled(True)
        layout.rail.selected_index = 1
        all_sessions = state.student_data.get("sessions", [])
        layout.set_content(PersonalHistoryScreen(
            page=page,
            student_name=state.student_name,
            sessions=all_sessions,
            on_back=show_settings,
            debug_report=_debug_report,
        ), centered=False)
        page.update()

    def show_session_summary():
        state.current_view = "summary"
        _debug_report("show_session_summary")
        _clear_quiz_bindings()
        _cleanup_workspace_content()
        if not state.student_name:
            layout.set_nav_enabled(False)
            layout.rail.selected_index = 0
            _show_message("Start a session before opening the summary.", ft.Colors.PRIMARY_CONTAINER)
            return
        layout.set_nav_enabled(True)
        layout.rail.selected_index = 2
        layout.set_content(SessionSummaryScreen(
            page=page,
            student_name=state.student_name,
            session_history=state.session_history,
            on_home=lambda e: show_welcome(),
            on_download_report=_download_session_report,
            debug_report=_debug_report,
        ), centered=False)
        page.update()

    # --- Logic Flow ---

    def start_quiz_setup(ignored_name, filename):
        state.current_vocab_file = filename
        _debug_report("start_quiz_setup", filename=filename)
        vocab_path = os.path.join(services.file_parser.save_dir, filename)
        vocab = services.file_parser.parse_file(vocab_path)
        if not vocab:
            _show_message(services.file_parser.last_error or "That vocabulary file is empty or could not be parsed.")
            return
        state.current_vocab = vocab
        show_quiz_config()

    def start_quiz(question_count, time_limit, config):
        if not state.current_vocab:
            _show_message("Load a vocabulary list before starting a quiz.")
            return
        state.quiz_mode = "standard"
        state.practice_parent_index = None
        state.current_config = config
        _debug_report(
            "start_quiz",
            question_count=question_count,
            time_limit=time_limit,
            config=config,
        )
        
        if state.student_name:
            student_data = state.student_data or {}
            student_data["last_config"] = config
            services.db.update_student(state.student_name, student_data)
            state.student_data = student_data
        
        engine = QuizEngine(state.current_vocab, services.spell)
        engine.start(question_count=question_count, time_limit=time_limit)
        engine.timer_running = True
        state.quiz_engine = engine
        
        show_quiz()

    def finish_quiz():
        engine = state.quiz_engine
        if not engine:
            return
        
        quiz_data = engine.finalize()
        state.last_quiz_data = quiz_data
        _debug_report(
            "finish_quiz",
            score=quiz_data["score"],
            total=quiz_data["total"],
            mistakes=len(quiz_data.get("mistakes", [])),
            quiz_mode=state.quiz_mode,
        )

        if state.quiz_mode == "practice" and state.practice_parent_index is not None:
            practice_entry = {
                "date": quiz_data["date"],
                "score": quiz_data["score"],
                "total": quiz_data["total"],
                "accuracy": (quiz_data["score"] / quiz_data["total"] * 100) if quiz_data["total"] > 0 else 0,
            }
            if 0 <= state.practice_parent_index < len(state.session_history):
                parent_session = state.session_history[state.practice_parent_index]
                parent_session.setdefault("practice_attempts", []).append(practice_entry)
                parent_session.setdefault("results_log", parent_session.get("log", []))
                parent_session["results_log"].extend(list(quiz_data["results_log"]))
                parent_session["log"] = list(parent_session["results_log"])
            if state.student_name and state.student_data:
                student_sessions = state.student_data.get("sessions", [])
                if 0 <= state.practice_parent_index < len(student_sessions):
                    student_parent = student_sessions[state.practice_parent_index]
                    student_parent.setdefault("practice_attempts", []).append(practice_entry)
                    student_parent.setdefault("results_log", [])
                    student_parent["results_log"].extend(list(quiz_data["results_log"]))
                    services.db.update_student(state.student_name, state.student_data)
        else:
            if state.student_name:
                services.db.add_session(state.student_name, quiz_data)
                state.student_data = services.db.get_student(state.student_name)

            session_entry = {
                "score": quiz_data["score"],
                "total": quiz_data["total"],
                "date": quiz_data["date"],
                "log": list(quiz_data["results_log"]),
                "results_log": list(quiz_data["results_log"]),
                "mistakes": quiz_data.get("mistakes", []),
                "accuracy": (quiz_data["score"] / quiz_data["total"] * 100) if quiz_data["total"] > 0 else 0,
                "practice_attempts": [],
            }
            state.session_history.append(session_entry)

        state.quiz_mode = "standard"
        state.practice_parent_index = None
        _update_sidebar_stats()
        
        show_results(quiz_data["score"], quiz_data["total"])

    # Initial screen
    show_name_entry()


if __name__ == "__main__":
    ft.app(target=main)
