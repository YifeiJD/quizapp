import flet as ft
from pathlib import Path
from flet_app.ui_flet.theme import palette
from flet_app.ui_flet.utils import show_message, confirm_action, show_download_success, normalize_student_name
from flet_app.session_utils import build_session_report, session_totals

# UI Imports
from flet_app.ui_flet.screens.name_entry import NameEntryScreen
from flet_app.ui_flet.screens.welcome import WelcomeScreen
from flet_app.ui_flet.screens.quiz_config import QuizConfigScreen
from flet_app.ui_flet.screens.quiz import QuizScreen
from flet_app.ui_flet.screens.results import ResultsScreen
from flet_app.ui_flet.screens.settings import SettingsScreen
from flet_app.ui_flet.screens.personal_history import PersonalHistoryScreen
from flet_app.ui_flet.screens.session_summary import SessionSummaryScreen
from flet_app.ui_flet.screens.admin_database import AdminDatabaseScreen

class AppNavigator:
    def __init__(self, page, state, services, layout, admin_settings, logger, debug_report_func, export_dir):
        self.page = page
        self.state = state
        self.services = services
        self.layout = layout
        self.admin_settings = admin_settings
        self.logger = logger
        self.debug_report = debug_report_func
        self.export_dir = export_dir
        
        self.quiz_controller = None
        self.admin_controller = None
        
        self.pending_report = {"content": "", "filename": "session_report.txt"}

    def set_controllers(self, quiz_controller, admin_controller):
        self.quiz_controller = quiz_controller
        self.admin_controller = admin_controller

    def handle_nav_change(self, e):
        try:
            selected = int(e.data) if e.data is not None else e.control.selected_index
        except (TypeError, ValueError):
            selected = e.control.selected_index
            
        self.debug_report("nav_change", selected=selected, raw_data=getattr(e, "data", None))
        if selected == 0:
            self.show_welcome()
        elif selected == 1:
            self.show_personal_history()
        elif selected == 2:
            self.show_session_summary()
        elif selected == 3:
            self.show_settings()

    def toggle_theme(self, is_dark: bool) -> None:
        self.page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        self.apply_shell_theme()
        self.layout.apply_theme()
        self.debug_report("theme_toggle", is_dark=is_dark)
        self.rerender_current_view()

    def apply_shell_theme(self) -> None:
        colors = palette(self.page)
        # We need to find the app_shell and app_surface in main_flet or pass them here
        # For now, let's assume we can update page.bgcolor and let the layout handle the rest
        if self.state.admin_mode:
            self.page.bgcolor = "#2B160B" if self.page.theme_mode == ft.ThemeMode.DARK else "#FEF3C7"
        else:
            self.page.bgcolor = colors["page_bg"]
        
        # Note: app_shell and app_surface update will be handled by main_flet since they are local there
        # OR we can pass them to the navigator.
        if hasattr(self, "app_shell") and self.app_shell:
            self.app_shell.bgcolor = self.page.bgcolor
            if hasattr(self, "app_surface") and self.app_surface:
                if self.state.admin_mode:
                    self.app_surface.bgcolor = "#1F2937" if self.page.theme_mode == ft.ThemeMode.DARK else "#FFF7ED"
                else:
                    self.app_surface.bgcolor = colors["workspace_bg"]
        self.page.update()

    def rerender_current_view(self) -> None:
        view = self.state.current_view
        self.debug_report("rerender_view", target_view=view)
        if view == "name_entry":
            self.show_name_entry()
        elif view == "welcome":
            self.show_welcome()
        elif view == "quiz_config":
            self.show_quiz_config()
        elif view == "quiz":
            self.show_quiz()
        elif view == "settings":
            self.show_settings()
        elif view == "history":
            self.show_personal_history()
        elif view == "summary":
            self.show_session_summary()
        elif view == "admin":
            self.show_admin_database()
        elif view == "results" and self.state.last_quiz_data:
            quiz_data = self.state.last_quiz_data
            self.show_results(quiz_data["score"], quiz_data["total"])

    def update_fab(self):
        if self.state.admin_mode:
            self.page.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                bgcolor=palette(self.page)["warning"],
                on_click=self._show_admin_fab_menu,
            )
        else:
            self.page.floating_action_button = None
        self.page.update()

    def _show_admin_fab_menu(self, e):
        colors = palette(self.page)
        
        def _go_to_panel(e):
            dialog.open = False
            self.page.update()
            self.show_admin_database()
        
        def _logout(e):
            dialog.open = False
            self.page.update()
            self.admin_controller.close_admin_database()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Admin Actions", color=colors["text"]),
            content=ft.Text("You are currently in Admin Mode. Student session is paused.", color=colors["text"]),
            actions=[
                ft.TextButton("Return to Admin Panel", on_click=_go_to_panel),
                ft.ElevatedButton("Admin Logout", on_click=_logout, bgcolor=colors["danger"], color=colors["primary_text"]),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def cleanup_workspace_content(self) -> None:
        """Run screen cleanup hooks before replacing the current content."""
        current_content = self.layout.content_host.controls[0] if self.layout.content_host.controls else None
        cleanup = getattr(current_content, "cleanup", None)
        if callable(cleanup):
            self.debug_report("workspace_cleanup", content_type=type(current_content).__name__)
            cleanup()

    def clear_quiz_bindings(self) -> None:
        """Remove quiz-specific page handlers when leaving the quiz screen."""
        self.page.on_keyboard_event = None
        self.debug_report("clear_quiz_bindings")

    def update_sidebar_stats(self) -> None:
        """Update sidebar statistics based on current session."""
        history = self.state.session_history
        if not history:
            self.layout.update_stats(0, 0)
            return

        total_correct, total_attempted = session_totals(history)
        self.layout.update_stats(total_correct, total_attempted)

    # --- Screen Display Functions ---

    def show_name_entry(self):
        self.state.current_view = "name_entry"
        self.debug_report("show_name_entry")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.rail.selected_index = 0
        self.layout.set_content(NameEntryScreen(self.page, self.on_name_entered, self.debug_report), centered=True)
        self.page.update()

    def on_name_entered(self, name: str):
        normalized_name = normalize_student_name(name)
        if normalized_name.lower() == "admin":
            self.debug_report("admin_name_entry_route")
            self.admin_controller.open_admin_gate(from_name_entry=True)
            return
        self.state.student_name = normalized_name
        self.layout.set_student(normalized_name)
        self.debug_report("name_entered", name=normalized_name, raw_name=name)
        self.layout.set_nav_enabled(True)
        
        student_data = self.services.db.get_student(normalized_name)
        self.state.student_data = student_data or {"sessions": []}
        
        # Reset session-specific stats when a new student is entered
        self.state.session_history = []
        self.update_sidebar_stats()
        
        self.show_welcome()

    def show_welcome(self):
        self.state.current_view = "welcome"
        self.debug_report("show_welcome")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.set_nav_enabled(bool(self.state.student_name))
        self.layout.rail.selected_index = 0
        self.layout.set_content(WelcomeScreen(
            page=self.page,
            file_parser=self.services.file_parser,
            student_name=self.state.student_name,
            student_data=self.state.student_data,
            on_start=self.quiz_controller.start_quiz_setup,
            on_quit_session=self.quit_session,
            selected_file=self.state.current_vocab_file,
            has_session_history=len(self.state.session_history) > 0,
            debug_report=self.debug_report,
        ), centered=True)
        self.page.update()

    def show_quiz_config(self):
        self.state.current_view = "quiz_config"
        self.debug_report("show_quiz_config")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.set_nav_enabled(bool(self.state.student_name))
        self.layout.rail.selected_index = 0
        saved_config = (self.state.student_data or {}).get("last_config", {})
        
        self.layout.set_content(QuizConfigScreen(
            page=self.page,
            total_available=len(self.state.current_vocab),
            on_start_quiz=self.quiz_controller.start_quiz,
            on_back=self.show_welcome,
            saved_config=saved_config,
            debug_report=self.debug_report,
        ), centered=True)
        self.page.update()

    def show_quiz(self):
        self.state.current_view = "quiz"
        self.debug_report("show_quiz")
        self.cleanup_workspace_content()
        self.layout.set_nav_enabled(bool(self.state.student_name))
        self.layout.rail.selected_index = 0
        self.layout.set_content(QuizScreen(self.page, self.state.quiz_engine, self.quiz_controller.finish_quiz, self.debug_report), centered=True)
        self.page.update()
        current_content = self.layout.content_host.controls[0] if self.layout.content_host.controls else None
        start = getattr(current_content, "start", None)
        if callable(start):
            start()

    def show_settings(self):
        self.state.current_view = "settings"
        self.debug_report("show_settings")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.set_nav_enabled(bool(self.state.student_name))
        self.layout.rail.selected_index = 3
        self.layout.set_content(SettingsScreen(
            page=self.page,
            current_resolution=self.state.app_resolution,
            on_resolution_change=self.change_resolution,
            on_reset_session=self.request_full_reset,
            on_back=self.show_welcome,
            on_view_history=self.show_personal_history,
            on_quit_session=self.quit_session,
            on_session_summary=self.show_session_summary,
            on_administer_records=self.show_admin_database if self.state.admin_mode else lambda: self.admin_controller.open_admin_gate(from_name_entry=False),
            debug_report=self.debug_report,
        ), centered=False)
        self.page.update()

    def show_admin_database(self):
        self.state.current_view = "admin"
        self.state.admin_mode = True
        self.update_fab()
        self.debug_report("show_admin_database")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.set_student("Admin")
        self.layout.set_admin_mode(True)
        self.apply_shell_theme()
        self.layout.set_nav_enabled(True)
        self.layout.rail.selected_index = 3
        self.layout.set_content(
            AdminDatabaseScreen(
                page=self.page,
                students=self.services.db.get_all_students(),
                on_back=self.admin_controller.close_admin_database,
                on_delete_student=self.admin_controller.delete_student_record,
                on_delete_session=self.admin_controller.delete_student_session,
                on_change_password=self.admin_controller.change_admin_password,
                get_wordlists=self.admin_controller.list_wordlists,
                preview_wordlist=self.admin_controller.preview_wordlist,
                on_delete_wordlist=self.admin_controller.delete_wordlist,
                on_download_student=self.admin_controller.download_student_record_admin,
                on_download_session=self.admin_controller.download_session_record_admin,
                on_import_wordlist=self.admin_controller.import_wordlist_admin,
                debug_report=self.debug_report,
            ),
            centered=False,
        )
        self.page.update()

    def show_results(self, score, total):
        self.state.current_view = "results"
        self.debug_report("show_results", score=score, total=total, quiz_mode=self.state.quiz_mode)
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        self.layout.set_nav_enabled(bool(self.state.student_name))
        self.layout.rail.selected_index = 0
        engine = self.state.quiz_engine
        has_mistakes = engine and len(engine.session_mistakes) > 0
        
        def on_practice_click(e):
            if engine and engine.session_mistakes:
                self.state.quiz_mode = "practice"
                self.state.practice_parent_index = len(self.state.session_history) - 1 if self.state.session_history else None
                self.debug_report("start_practice_mistakes", parent_index=self.state.practice_parent_index)
                engine.practice_mistakes()
                engine.timer_running = True
                self.show_quiz()
        
        self.layout.set_content(ResultsScreen(
            page=self.page,
            student_name=self.state.student_name,
            score=score,
            total=total,
            results_log=list(engine.results_log) if engine else [],
            on_home=lambda e: self.show_welcome(),
            on_practice=on_practice_click if has_mistakes else None,
            on_quit_session=self.quit_session,
            debug_report=self.debug_report,
        ), centered=True)
        self.page.update()

    def show_personal_history(self):
        self.state.current_view = "history"
        self.debug_report("show_personal_history")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        if not self.state.student_data:
            self.layout.set_nav_enabled(False)
            self.layout.rail.selected_index = 0
            show_message(self.page, "Enter a student name before opening history.", "primaryContainer")
            return
        self.layout.set_nav_enabled(True)
        self.layout.rail.selected_index = 1
        all_sessions = self.state.student_data.get("sessions", [])
        self.layout.set_content(PersonalHistoryScreen(
            page=self.page,
            student_name=self.state.student_name,
            sessions=all_sessions,
            on_back=self.show_settings,
            debug_report=self.debug_report,
        ), centered=False)
        self.page.update()

    def show_session_summary(self):
        self.state.current_view = "summary"
        self.debug_report("show_session_summary")
        self.clear_quiz_bindings()
        self.cleanup_workspace_content()
        if not self.state.student_name:
            self.layout.set_nav_enabled(False)
            self.layout.rail.selected_index = 0
            show_message(self.page, "Start a session before opening the summary.", "primaryContainer")
            return
        self.layout.set_nav_enabled(True)
        self.layout.rail.selected_index = 2
        self.layout.set_content(SessionSummaryScreen(
            page=self.page,
            student_name=self.state.student_name,
            session_history=self.state.session_history,
            on_home=lambda e: self.show_welcome(),
            on_download_report=self.download_session_report,
            debug_report=self.debug_report,
        ), centered=False)
        self.page.update()

    # --- Session Management ---

    def quit_session(self) -> None:
        """Quit current session and return to name entry."""
        if self.state.admin_mode:
            show_message(self.page, "Cannot quit student session in Admin Mode. Log out first.", "errorContainer")
            return
        self.debug_report("quit_session")
        self.clear_quiz_bindings()
        
        # Clean up ghost student if they have no sessions
        if self.state.student_name:
            student = self.services.db.get_student(self.state.student_name)
            if student and not student.get("sessions"):
                self.services.db.delete_student(self.state.student_name)
                
        self.state.reset_session()
        self.layout.set_student("")
        self.layout.set_nav_enabled(False)
        self.layout.update_stats(0, 0)
        self.show_name_entry()

    def full_reset(self) -> None:
        self.debug_report("full_reset")
        self.clear_quiz_bindings()
        
        # Clean up ghost student if they have no sessions
        if self.state.student_name:
            student = self.services.db.get_student(self.state.student_name)
            if student and not student.get("sessions"):
                self.services.db.delete_student(self.state.student_name)
                
        self.state.reset_session()
        self.layout.set_student("")
        self.layout.set_nav_enabled(False)
        self.layout.update_stats(0, 0)
        self.show_name_entry()

    def request_full_reset(self) -> None:
        if self.state.admin_mode:
            show_message(self.page, "Session reset is disabled in Admin Mode.", "errorContainer")
            return
        confirm_action(
            self.page,
            "Reset Entire Session",
            "This will clear the active student, in-memory session history, and current quiz progress.",
            self.full_reset,
            debug_report=self.debug_report
        )

    def download_session_report(self) -> None:
        if not self.state.session_history:
            show_message(self.page, "Complete at least one quiz before downloading a report.", "primaryContainer")
            return
        self.pending_report["content"] = build_session_report(self.state.student_name, self.state.session_history)
        safe_name = (self.state.student_name or "session").replace(" ", "_").replace("/", "_")
        self.pending_report["filename"] = f"{safe_name}_Report.txt"
        self.debug_report("report_save_requested", filename=self.pending_report["filename"])
        
        try:
            output_path = self.export_dir / self.pending_report["filename"]
            output_path.write_text(self.pending_report["content"], encoding="utf-8")
            show_download_success(self.page, output_path)
        except Exception as exc:
            self.debug_report("report_save_failed", error=str(exc))
            show_message(self.page, f"Failed to save report: {exc}", "errorContainer")

    def change_resolution(self, new_res):
        from flet_app.app_config import window_size_for_resolution, TOP_WINDOW_MARGIN
        import asyncio
        width, height = new_res
        window_width, window_height = window_size_for_resolution((width, height))
        self.state.app_resolution = (width, height)
        self.layout.set_surface_size(width, height)
        
        if hasattr(self, "app_surface") and self.app_surface:
            self.app_surface.width = width
            self.app_surface.height = height
            
        self.page.window.width = window_width
        self.page.window.height = window_height
        
        def _position():
            try:
                center_result = self.page.window.center()
                if asyncio.iscoroutine(center_result):
                    async def _center():
                        await center_result
                        self.page.window.top = TOP_WINDOW_MARGIN
                        self.page.update()
                    self.page.run_task(_center)
                else:
                    self.page.window.top = TOP_WINDOW_MARGIN
                    self.page.update()
            except Exception:
                pass
        
        _position()
        self.debug_report("resolution_change", width=width, height=height)
        show_message(self.page, f"App viewport updated to {width} x {height}", "primaryContainer")
