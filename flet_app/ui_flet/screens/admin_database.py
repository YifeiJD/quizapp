import flet as ft
from typing import Callable, Dict, Any, Optional
from flet_app.ui_flet.theme import palette


class AdminDatabaseScreen(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        students: Dict[str, Any],
        on_back: Callable,
        on_delete_student: Callable[[str], None],
        on_delete_session: Callable[[str, int], None],
        on_change_password: Callable[[str, str, str], None],
        get_wordlists: Callable[[], list[str]],
        preview_wordlist: Callable[[str], Dict[str, Any]],
        on_delete_wordlist: Callable[[str], None],
        on_download_student: Callable[[str], None],
        on_download_session: Callable[[str, int], None],
        on_import_wordlist: Callable[[], None],
        debug_report: Optional[Callable[..., None]] = None,
    ):
        super().__init__(expand=True)
        self.host_page = page
        self.students = students
        self.on_back = on_back
        self.on_delete_student = on_delete_student
        self.on_delete_session = on_delete_session
        self.on_change_password = on_change_password
        self.get_wordlists = get_wordlists
        self.preview_wordlist = preview_wordlist
        self.on_delete_wordlist = on_delete_wordlist
        self.on_download_student = on_download_student
        self.on_download_session = on_download_session
        self.on_import_wordlist = on_import_wordlist
        self.debug_report = debug_report
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 16
        self.scroll = ft.ScrollMode.AUTO
        self.controls = self._build_ui()

    def _build_ui(self) -> list[ft.Control]:
        colors = palette(self.host_page)
        student_names = sorted(self.students.keys(), key=str.lower)
        total_sessions = sum(len((self.students.get(name) or {}).get("sessions", [])) for name in student_names)

        return [
            ft.Text("Admin Database", size=28, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Text(
                "Admin tools for managing the student database and security settings.",
                color=colors["muted"],
            ),
            self._build_summary_card(len(student_names), total_sessions),
            self._build_action_card(),
            ft.Row(
                controls=[ft.ElevatedButton("Admin Logout", on_click=lambda e: self.on_back())],
                alignment=ft.MainAxisAlignment.END,
            ),
        ]

    def _build_action_card(self) -> ft.Control:
        colors = palette(self.host_page)
        return ft.Container(
            padding=18,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=12,
            content=ft.Column(
                controls=[
                    ft.Text("Admin Actions", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Student Records",
                                icon=ft.Icons.STORAGE_OUTLINED,
                                on_click=lambda e: self._open_student_records_dialog(),
                                bgcolor=colors["primary"],
                                color=colors["primary_text"],
                            ),
                            ft.ElevatedButton(
                                "Change Password",
                                icon=ft.Icons.LOCK_OUTLINE,
                                on_click=lambda e: self._open_password_dialog(),
                                bgcolor=colors["warning"],
                                color=colors["primary_text"],
                            ),
                            ft.ElevatedButton(
                                "Word Lists",
                                icon=ft.Icons.MENU_BOOK_OUTLINED,
                                on_click=lambda e: self._open_wordlists_dialog(),
                                bgcolor=colors["success"],
                                color=colors["primary_text"],
                            ),
                        ft.ElevatedButton(
                            "Import Word List",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda e: self.on_import_wordlist(),
                            bgcolor=colors["primary"],
                            color=colors["primary_text"],
                        ),
                        ],
                        wrap=True,
                        spacing=12,
                    ),
                ],
                spacing=12,
            ),
        )

    def _build_password_card(self) -> ft.Control:
        colors = palette(self.host_page)
        self.current_password = ft.TextField(label="Current Password", password=True, can_reveal_password=True)
        self.new_password = ft.TextField(label="New Password", password=True, can_reveal_password=True)
        self.confirm_password = ft.TextField(label="Confirm Password", password=True, can_reveal_password=True)
        return ft.Column(
            controls=[
                ft.Text("Default password is 'admin' until you change it.", color=colors["muted"]),
                self.current_password,
                self.new_password,
                self.confirm_password,
            ],
            spacing=10,
        )

    def _open_password_dialog(self) -> None:
        colors = palette(self.host_page)
        dialog = None

        def submit(_=None):
            self._submit_password_change(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Change Admin Password", color=colors["text"]),
            content=self._build_password_card(),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save Password",
                    on_click=submit,
                    bgcolor=colors["warning"],
                    color=colors["primary_text"],
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.current_password.on_submit = submit
        self.new_password.on_submit = submit
        self.confirm_password.on_submit = submit
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

    def _submit_password_change(self, dialog) -> None:
        changed = self.on_change_password(
            self.current_password.value or "",
            self.new_password.value or "",
            self.confirm_password.value or "",
        )
        if changed:
            self._close_dialog(dialog)

    def _open_student_records_dialog(self) -> None:
        colors = palette(self.host_page)
        student_names = sorted(self.students.keys(), key=str.lower)
        student_cards = [self._build_student_card(name, self.students[name]) for name in student_names]
        if not student_cards:
            student_cards = [
                ft.Container(
                    padding=18,
                    border_radius=10,
                    bgcolor=colors["card_alt_bg"],
                    content=ft.Text("No student records in the database.", color=colors["muted"]),
                )
            ]

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Student Records", color=colors["text"]),
            content=ft.Container(
                width=780,
                content=ft.Column(
                    controls=student_cards,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    height=420,
                ),
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

    def _open_wordlists_dialog(self) -> None:
        colors = palette(self.host_page)
        filenames = sorted(self.get_wordlists(), key=str.lower)
        file_rows = [self._build_wordlist_row(filename) for filename in filenames]
        if not file_rows:
            file_rows = [
                ft.Container(
                    padding=18,
                    border_radius=10,
                    bgcolor=colors["card_alt_bg"],
                    content=ft.Text("No saved vocabulary lists found.", color=colors["muted"]),
                )
            ]

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Word Lists", color=colors["text"]),
            content=ft.Container(
                width=780,
                content=ft.Column(
                    controls=file_rows,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    height=420,
                ),
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

    def _build_wordlist_row(self, filename: str) -> ft.Control:
        colors = palette(self.host_page)
        return ft.Container(
            padding=12,
            border_radius=8,
            bgcolor=colors["card_alt_bg"],
            border=ft.border.all(1, colors["card_border"]),
            content=ft.Row(
                controls=[
                    ft.Text(filename, color=colors["text"], expand=True),
                    ft.TextButton(
                        "Preview",
                        on_click=lambda e, name=filename: self._open_wordlist_preview(name),
                    ),
                    ft.TextButton(
                        "Delete",
                        on_click=lambda e, name=filename: self.on_delete_wordlist(name),
                        style=ft.ButtonStyle(color=colors["danger"]),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _open_wordlist_preview(self, filename: str) -> None:
        colors = palette(self.host_page)
        preview = self.preview_wordlist(filename)
        if preview.get("error"):
            entries_control = ft.Text(preview["error"], color=colors["danger"])
        else:
            rows = [
                ft.Row(
                    controls=[
                        ft.Text(chinese, color=colors["text"], expand=True),
                        ft.Text(english, color=colors["muted"], expand=True),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for chinese, english in preview.get("entries", [])
            ]
            if not rows:
                rows = [ft.Text("This word list is empty.", color=colors["muted"])]
            entries_control = ft.Column(controls=rows, spacing=8, scroll=ft.ScrollMode.AUTO, height=360)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Preview: {filename}", color=colors["text"]),
            content=ft.Container(width=720, content=entries_control),
            actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

    def _close_dialog(self, dialog) -> None:
        dialog.open = False
        self.host_page.update()

    def _build_summary_card(self, student_count: int, total_sessions: int) -> ft.Control:
        colors = palette(self.host_page)
        return ft.Container(
            padding=20,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=12,
            content=ft.ResponsiveRow(
                controls=[
                    self._build_metric("Students", str(student_count)),
                    self._build_metric("Saved Sessions", str(total_sessions)),
                ]
            ),
        )

    def _build_metric(self, title: str, value: str) -> ft.Control:
        colors = palette(self.host_page)
        return ft.Column(
            col={"sm": 6, "md": 3},
            controls=[
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=colors["muted"]),
                ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ],
            spacing=6,
        )

    def _build_student_card(self, student_name: str, student_data: Dict[str, Any]) -> ft.Control:
        colors = palette(self.host_page)
        sessions = student_data.get("sessions", [])
        total_words_learned = student_data.get("total_words_learned", 0)
        session_controls = [self._build_session_row(student_name, index, session) for index, session in enumerate(sessions)]
        if not session_controls:
            session_controls = [ft.Text("No saved sessions.", color=colors["muted"], italic=True)]

        return ft.Container(
            padding=18,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=12,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(student_name, size=20, weight=ft.FontWeight.BOLD, color=colors["text"]),
                                    ft.Text(
                                        f"Sessions: {len(sessions)} | Total learned: {total_words_learned}",
                                        color=colors["muted"],
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Download Record",
                                    icon=ft.Icons.DOWNLOAD,
                                    bgcolor=colors["primary"],
                                    color=colors["primary_text"],
                                    on_click=lambda e, name=student_name: self.on_download_student(name),
                                ),
                                ft.ElevatedButton(
                                    "Delete Student",
                                    icon=ft.Icons.DELETE,
                                    bgcolor=colors["danger"],
                                    color=colors["primary_text"],
                                    on_click=lambda e, name=student_name: self._delete_student(name),
                                ),
                            ],
                            spacing=10,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10),
                    ft.Column(controls=session_controls, spacing=10),
                ],
                spacing=10,
            ),
        )

    def _build_session_row(self, student_name: str, session_index: int, session: Dict[str, Any]) -> ft.Control:
        colors = palette(self.host_page)
        return ft.Container(
            padding=12,
            border_radius=8,
            bgcolor=colors["card_alt_bg"],
            border=ft.border.all(1, colors["card_border"]),
            content=ft.Row(
                controls=[
                    ft.Text(
                        f"{session.get('date', 'Unknown date')} | Score {session.get('score', 0)}/{session.get('total', 0)}"
                        f" ({session.get('accuracy', 0):.1f}%)",
                        color=colors["text"],
                        expand=True,
                    ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            icon_color=colors["primary"],
                            tooltip="Download Session",
                            on_click=lambda e, name=student_name, idx=session_index: self.on_download_session(name, idx),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=colors["danger"],
                            tooltip="Delete Session",
                            on_click=lambda e, name=student_name, idx=session_index: self._delete_session(name, idx),
                        ),
                    ],
                    spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _delete_student(self, student_name: str) -> None:
        if self.debug_report:
            self.debug_report("admin_delete_student_click", student_name=student_name)
        self.on_delete_student(student_name)

    def _delete_session(self, student_name: str, session_index: int) -> None:
        if self.debug_report:
            self.debug_report("admin_delete_session_click", student_name=student_name, session_index=session_index)
        self.on_delete_session(student_name, session_index)
