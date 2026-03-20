import os
import shutil
import flet as ft
from pathlib import Path
from flet_app.ui_flet.utils import show_message, confirm_action, show_download_success
from flet_app.session_utils import build_session_report

class AdminController:
    def __init__(self, page, services, state, navigator, admin_settings, export_dir):
        self.page = page
        self.services = services
        self.state = state
        self.navigator = navigator
        self.admin_settings = admin_settings
        self.export_dir = export_dir
        
        self.admin_save_picker = None
        self.admin_open_picker = None
        self.pending_admin_export = {"content": ""}

    def initialize_pickers(self):
        if self.admin_save_picker is None:
            self.admin_save_picker = ft.FilePicker()
            self.admin_save_picker.on_result = self.on_admin_save_result
            self.page.overlay.append(self.admin_save_picker)
        if self.admin_open_picker is None:
            self.admin_open_picker = ft.FilePicker()
            self.admin_open_picker.on_result = self.on_admin_open_result
            self.page.overlay.append(self.admin_open_picker)
        self.page.update()

    def on_admin_save_result(self, e):
        if e.path:
            Path(e.path).write_text(self.pending_admin_export["content"], encoding="utf-8")
            show_message(self.page, f"Report saved to {e.path}", "primaryContainer")

    def on_admin_open_result(self, e):
        if e.files and len(e.files) > 0:
            source_path = e.files[0].path
            filename = e.files[0].name
            dest_path = os.path.join(self.services.file_parser.save_dir, filename)
            try:
                shutil.copy2(source_path, dest_path)
                show_message(self.page, f"Imported {filename} successfully.", "primaryContainer")
                if self.state.current_view == "admin":
                    self.navigator.show_admin_database()
            except Exception as ex:
                show_message(self.page, f"Failed to import: {ex}", "errorContainer")

    def delete_student_record(self, student_name: str) -> None:
        def do_delete():
            deleted = self.services.db.delete_student(student_name)
            self.navigator.debug_report("admin_delete_student", student_name=student_name, deleted=deleted)
            if deleted and self.state.student_name == student_name:
                self.state.pending_deleted_active_student = True
            if deleted and self.state.student_name != student_name:
                show_message(self.page, f"Deleted student record for {student_name}.", "primaryContainer")
            self.navigator.show_admin_database()

        confirm_action(
            self.page,
            "Delete Student Record",
            f"Delete {student_name} and all saved sessions from the database?",
            do_delete,
            debug_report=self.navigator.debug_report
        )

    def delete_student_session(self, student_name: str, session_index: int) -> None:
        def do_delete():
            deleted = self.services.db.delete_session(student_name, session_index)
            self.navigator.debug_report("admin_delete_session", student_name=student_name, session_index=session_index, deleted=deleted)
            if deleted:
                show_message(self.page, "Deleted saved session record.", "primaryContainer")
            self.navigator.show_admin_database()

        confirm_action(
            self.page,
            "Delete Saved Session",
            f"Delete session #{session_index + 1} for {student_name} from the database?",
            do_delete,
            debug_report=self.navigator.debug_report
        )

    def list_wordlists(self) -> list[str]:
        files = self.services.file_parser.list_available_files()
        self.navigator.debug_report("admin_wordlists_listed", count=len(files), files=files)
        return files

    def preview_wordlist(self, filename: str) -> dict:
        safe_filename = os.path.basename(filename)
        path = os.path.join(self.services.file_parser.save_dir, safe_filename)
        vocab = self.services.file_parser.parse_file(path)
        preview_entries = list(vocab.items())[:100]
        self.navigator.debug_report(
            "admin_wordlist_preview",
            filename=safe_filename,
            entries=len(preview_entries),
            error=self.services.file_parser.last_error,
        )
        return {
            "entries": preview_entries,
            "error": self.services.file_parser.last_error,
        }

    def delete_wordlist(self, filename: str) -> None:
        safe_filename = os.path.basename(filename)

        def do_delete():
            path = os.path.join(self.services.file_parser.save_dir, safe_filename)
            deleted = False
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    deleted = True
                    if self.state.current_vocab_file == safe_filename:
                        self.state.current_vocab_file = None
                        self.state.current_vocab = {}
                self.navigator.debug_report("admin_delete_wordlist", filename=safe_filename, deleted=deleted)
            except Exception as exc:
                self.navigator.debug_report("admin_delete_wordlist_failed", filename=safe_filename, error=str(exc))
                show_message(self.page, f"Could not delete {safe_filename}.")
                return

            if deleted:
                show_message(self.page, f"Deleted word list {safe_filename}.", "primaryContainer")
            else:
                show_message(self.page, f"{safe_filename} was not found.")
            self.navigator.show_admin_database()

        confirm_action(
            self.page,
            "Delete Word List",
            f"Delete {safe_filename} from the saved vocabulary lists?",
            do_delete,
            debug_report=self.navigator.debug_report
        )

    def download_student_record_admin(self, student_name: str) -> None:
        student = self.services.db.get_student(student_name)
        if not student or not student.get("sessions"):
            show_message(self.page, "No sessions to download.", "errorContainer")
            return
        content = build_session_report(student_name, student["sessions"])
        safe_name = student_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_Full_Report.txt"
        out_path = self.export_dir / filename
        try:
            out_path.write_text(content, encoding="utf-8")
            show_download_success(self.page, out_path)
        except Exception as e:
            show_message(self.page, f"Failed to save record: {e}", "errorContainer")

    def download_session_record_admin(self, student_name: str, session_index: int) -> None:
        student = self.services.db.get_student(student_name)
        if not student or session_index >= len(student.get("sessions", [])):
            return
        content = build_session_report(student_name, [student["sessions"][session_index]])
        safe_name = student_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_Session_{session_index + 1}.txt"
        out_path = self.export_dir / filename
        try:
            out_path.write_text(content, encoding="utf-8")
            show_download_success(self.page, out_path)
        except Exception as e:
            show_message(self.page, f"Failed to save session: {e}", "errorContainer")

    def import_wordlist_admin(self) -> None:
        self.initialize_pickers()
        try:
            self.page.run_task(
                self.admin_open_picker.pick_files,
                dialog_title="Import Vocabulary List",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["txt", "docx"]
            )
        except Exception as e:
            show_message(self.page, f"Failed to open file picker: {e}", "errorContainer")

    def open_admin_gate(self, from_name_entry: bool = False) -> None:
        password_input = ft.TextField(
            label="Admin Password",
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        dialog = None

        def submit_admin_password(_=None):
            if self.admin_settings.verify_password(password_input.value or ""):
                dialog.open = False
                self.page.update()
                self.state.admin_entry_route = from_name_entry
                self.navigator.show_admin_database()
                return
            password_input.error_text = "Incorrect password"
            password_input.update()

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Admin Access Required"),
            content=password_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Enter Admin Panel", on_click=submit_admin_password),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        password_input.on_submit = submit_admin_password
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def change_admin_password(self, current_password: str, new_password: str, confirm_password: str) -> bool:
        if not self.admin_settings.verify_password(current_password):
            show_message(self.page, "Current admin password is incorrect.")
            return False
        if not new_password.strip():
            show_message(self.page, "Enter a new admin password.")
            return False
        if new_password != confirm_password:
            show_message(self.page, "New password and confirmation do not match.")
            return False
        self.admin_settings.set_password(new_password)
        self.navigator.debug_report("admin_password_changed")
        show_message(self.page, "Admin password updated.", "primaryContainer")
        return True

    def close_admin_database(self) -> None:
        self.state.admin_mode = False
        self.navigator.update_fab()
        self.navigator.layout.set_admin_mode(False)
        self.navigator.apply_shell_theme()
        if self.state.admin_entry_route:
            self.navigator.debug_report("admin_logout_to_begin")
            self.state.reset_session()
            self.navigator.layout.set_student("")
            self.navigator.layout.set_nav_enabled(False)
            self.navigator.layout.update_stats(0, 0)
            self.navigator.show_name_entry()
            return
        if self.state.pending_deleted_active_student:
            self.navigator.debug_report("admin_close_with_deleted_active_student")
            self.state.reset_session()
            self.navigator.layout.set_student("")
            self.navigator.layout.set_nav_enabled(False)
            self.navigator.layout.update_stats(0, 0)
            self.navigator.show_name_entry()
            return
        if self.state.student_name:
            self.state.student_data = self.services.db.get_student(self.state.student_name) or {"sessions": []}
            self.navigator.layout.set_student(self.state.student_name)
        self.navigator.show_settings()
