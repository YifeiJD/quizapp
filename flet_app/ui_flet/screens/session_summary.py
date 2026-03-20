import flet as ft
from typing import List, Dict, Any, Callable, Optional
from flet_app.ui_flet.theme import palette

class SessionSummaryScreen(ft.Column):
    def __init__(self, page: ft.Page, student_name: str, session_history: List[Dict[str, Any]], on_home: Callable, on_download_report: Callable[[], None], debug_report: Optional[Callable[..., None]] = None):
        super().__init__(expand=True)
        self.host_page = page
        self.student_name = student_name
        self.session_history = session_history
        self.on_home = on_home
        self.on_download_report = on_download_report
        self.debug_report = debug_report

        self.alignment = ft.MainAxisAlignment.START
        self.controls = self._build_ui()

    def _build_ui(self) -> List[ft.Control]:
        colors = palette(self.host_page)
        total_correct = sum(q.get('score', 0) for q in self.session_history)
        total_attempted = sum(q.get('total', 0) for q in self.session_history)
        accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        num_quizzes = len(self.session_history)

        return [
            ft.Text("Session Dashboard", size=32, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Divider(height=30),
            
            ft.Container(
                content=ft.Row(
                    controls=[
                        self._build_stat_card("Total Accuracy", f"{accuracy:.1f}%"),
                        self._build_stat_card("Words Tested", str(total_attempted)),
                        self._build_stat_card("Quizzes Taken", str(num_quizzes)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                padding=20,
                border_radius=10,
                bgcolor=colors["card_bg"],
                border=ft.border.all(1, colors["card_border"]),
            ),

            ft.Column(height=20), # Spacer

            ft.ElevatedButton(
                "Download Session Report (.txt)",
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                on_click=lambda e: self._download_report(),
                bgcolor=colors["primary"],
                color=colors["primary_text"],
            ),

            ft.Row(
                [ft.ElevatedButton("← Return to Menu", on_click=self.on_home)],
                alignment=ft.MainAxisAlignment.CENTER
            )
        ]

    def _build_stat_card(self, title: str, value: str) -> ft.Column:
        return ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=palette(self.host_page)["muted"]),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=palette(self.host_page)["text"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _download_report(self):
        if self.debug_report:
            self.debug_report("session_summary_download_report")
        self.on_download_report()
