import flet as ft
from typing import Callable, List, Dict, Any, Optional
from flet_app.ui_flet.theme import palette


class ResultsScreen(ft.Container):
    def __init__(self, page: ft.Page, student_name: str, score: int, total: int, results_log: List[Dict[str, Any]], on_home: Callable, on_practice: Callable = None, on_quit_session: Callable = None, debug_report: Optional[Callable[..., None]] = None):
        super().__init__(expand=True)
        self.host_page = page
        self.student_name = student_name
        self.score = score
        self.total = total
        self.results_log = results_log
        self.on_home = on_home
        self.on_practice = on_practice
        self.on_quit_session = on_quit_session
        self.debug_report = debug_report
        
        self.content = self._build_ui()
        self.alignment = ft.alignment.Alignment(0, 0)

    def _build_ui(self) -> ft.Container:
        colors = palette(self.host_page)
        correct_results = [r for r in self.results_log if r.get("is_correct")]
        review_results = [r for r in self.results_log if not r.get("is_correct")]
        
        summary_metrics = ft.Column(
            controls=[
                ft.Text("This Round", size=16, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Text(f"Total Questions: {self.total}", size=15, color=colors["text"]),
                ft.Text(f"Correct Answers: {self.score}", size=15, color=colors["primary"]),
            ],
            spacing=8,
        )
        correct_word_list = self._build_correct_words(correct_results)
        review_panel = self._build_review_table(review_results)
        
        buttons = [
            ft.ElevatedButton(
                "Back to Home",
                on_click=lambda e: self._handle_home(e),
                style=ft.ButtonStyle(
                    padding=20,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=200,
                height=46,
                bgcolor=colors["primary"],
                color=colors["primary_text"]
            )
        ]
        
        if self.on_practice:
            buttons.append(
                ft.ElevatedButton(
                    "Practice Mistakes",
                    on_click=lambda e: self._handle_practice(e),
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    width=200,
                    height=46,
                    bgcolor=colors["success"],
                    color=colors["primary_text"]
                )
            )
        
        left_panel = ft.Container(
            expand=4,
            padding=24,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=15,
            content=ft.Column(
                controls=[
                    summary_metrics,
                    ft.Text("Correct Answers", size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    correct_word_list,
                    ft.Container(expand=True),
                    ft.Row(buttons, alignment=ft.MainAxisAlignment.START, spacing=10, wrap=True),
                    ft.TextButton(
                        "Quit Session",
                        on_click=lambda e: self._handle_quit(e),
                        style=ft.ButtonStyle(color=colors["danger"])
                    ) if self.on_quit_session else ft.Container(),
                ],
                spacing=12,
                expand=True,
                alignment=ft.MainAxisAlignment.START,
            ),
        )

        right_panel = ft.Container(
            expand=5,
            padding=24,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=15,
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Words Missed ({len(review_results)})",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=colors["text"],
                    ),
                    ft.Text(
                        "Only this panel scrolls, so your actions stay visible.",
                        color=colors["muted"],
                        size=13,
                    ),
                    review_panel,
                ],
                spacing=12,
                expand=True,
            ),
        )

        results_card = ft.Container(
            content=ft.Row(
                controls=[left_panel, right_panel],
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            width=860,
            height=560,
        )
        
        return results_card

    def _build_correct_words(self, correct_results: List[Dict[str, Any]]) -> ft.Control:
        colors = palette(self.host_page)
        content = (
            ft.Column(
                controls=[
                    ft.Text(
                        f"{result['chi']} -> {result['correct']}",
                        color=colors["text"],
                    )
                    for result in correct_results
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                height=min(130, max(44, 28 * min(len(correct_results), 4))),
            )
            if correct_results
            else ft.Text("No correct answers this round.", color=colors["muted"], italic=True)
        )
        return ft.Container(
            content=content,
            padding=12,
            bgcolor=colors["card_alt_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=10,
        )

    def _build_review_table(self, review_results: List[Dict[str, Any]]) -> ft.Control:
        colors = palette(self.host_page)
        header = ft.Container(
            padding=12,
            bgcolor=colors["card_alt_bg"],
            border_radius=10,
            content=ft.Row(
                controls=[
                    ft.Text("Chinese", weight=ft.FontWeight.BOLD, color=colors["text"], expand=3),
                    ft.Text("Correct Answer", weight=ft.FontWeight.BOLD, color=colors["text"], expand=3),
                    ft.Text("Your Answer", weight=ft.FontWeight.BOLD, color=colors["text"], expand=3),
                ],
                spacing=12,
            ),
        )

        if not review_results:
            body = ft.Container(
                padding=16,
                bgcolor=colors["card_bg"],
                border=ft.border.all(1, colors["card_border"]),
                border_radius=10,
                content=ft.Text("No incorrect, skipped, or timed-out answers.", color=colors["muted"], italic=True),
            )
            return ft.Column([header, body], spacing=8, expand=True)

        rows = []
        for result in review_results:
            user_value = result.get("user", "")
            if result.get("skipped"):
                user_value = "Skipped"
            elif result.get("is_timeout") and not user_value:
                user_value = "Timed out"
            rows.append(
                ft.Container(
                    padding=12,
                    bgcolor=colors["card_bg"],
                    border=ft.border.all(1, colors["card_border"]),
                    border_radius=10,
                    content=ft.Row(
                        controls=[
                            ft.Text(result.get("chi", ""), color=colors["text"], expand=3),
                            ft.Text(result.get("correct", ""), color=colors["text"], expand=3),
                            ft.Text(user_value or "-", color=colors["danger"], expand=3),
                        ],
                        spacing=12,
                    ),
                )
            )

        return ft.Column(
            controls=[header, ft.Column(controls=rows, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)],
            spacing=8,
            expand=True,
        )

    def _handle_home(self, e):
        if self.debug_report:
            self.debug_report("results_home_click")
        self.on_home(e)

    def _handle_practice(self, e):
        if self.debug_report:
            self.debug_report("results_practice_click")
        if self.on_practice:
            self.on_practice(e)

    def _handle_quit(self, e):
        if self.debug_report:
            self.debug_report("results_quit_click")
        if self.on_quit_session:
            self.on_quit_session()
