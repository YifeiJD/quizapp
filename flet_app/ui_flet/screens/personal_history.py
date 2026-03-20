import flet as ft
from typing import List, Dict, Any, Callable, Tuple, Optional
from flet_app.ui_flet.theme import palette


class PersonalHistoryScreen(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        student_name: str,
        sessions: List[Dict[str, Any]],
        on_back: Callable,
        debug_report: Optional[Callable[..., None]] = None,
    ):
        super().__init__(expand=True)
        self.host_page = page
        self.student_name = student_name
        self.sessions = sessions
        self.on_back = on_back
        self.debug_report = debug_report
        self.word_sections: Dict[str, Dict[str, ft.Control]] = {}

        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 16
        self.scroll = ft.ScrollMode.AUTO
        self.controls = self._build_ui()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _compute_cumulative_stats(self) -> Dict[str, Any]:
        tested_words: Dict[Tuple[str, str], str] = {}
        learned_words: Dict[Tuple[str, str], str] = {}
        wrong_words: Dict[Tuple[str, str], str] = {}

        for session in self.sessions:
            results_log = session.get("results_log", []) or session.get("log", [])
            for result in results_log:
                chi = result.get("chi", "")
                correct = result.get("correct", "")
                if not chi or not correct:
                    continue
                key = (chi, correct)
                label = f"{chi} -> {correct}"
                tested_words[key] = label
                if result.get("is_correct"):
                    learned_words[key] = label
                else:
                    wrong_words[key] = label

        return {
            "sessions_tried": len(self.sessions),
            "tested_words": sorted(tested_words.values()),
            "learned_words": sorted(learned_words.values()),
            "wrong_words": sorted(wrong_words.values()),
        }

    def _build_ui(self) -> List[ft.Control]:
        colors = palette(self.host_page)
        stats = self._compute_cumulative_stats()
        session_rows = self._build_session_rows()

        return [
            ft.Text(f"History: {self.student_name}", size=28, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Text(
                "Cumulative performance across all saved sessions.",
                color=colors["muted"],
            ),
            self._build_summary_card(stats),
            self._build_word_section("Distinct Words Tested", stats["tested_words"], "tested"),
            self._build_word_section("Words Learned", stats["learned_words"], "learned"),
            self._build_word_section("Words Gotten Wrong", stats["wrong_words"], "wrong"),
            ft.Divider(height=8, color="transparent"),
            ft.Text("Session Timeline", size=22, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Column(controls=session_rows, spacing=10),
            ft.Row(
                controls=[ft.ElevatedButton("Back to Settings", on_click=lambda e: self.on_back())],
                alignment=ft.MainAxisAlignment.END,
            ),
        ]

    def _build_summary_card(self, stats: Dict[str, Any]) -> ft.Control:
        colors = palette(self.host_page)
        summary_items = [
            ("Sessions Tried", str(stats["sessions_tried"])),
            ("Distinct Words Tested", str(len(stats["tested_words"]))),
            ("Words Learned", str(len(stats["learned_words"]))),
            ("Words Gotten Wrong", str(len(stats["wrong_words"]))),
        ]
        return ft.Container(
            padding=20,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=12,
            content=ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        col={"sm": 6, "md": 3},
                        controls=[
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=colors["muted"]),
                            ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ],
                        spacing=6,
                    )
                    for title, value in summary_items
                ],
                run_spacing=16,
            ),
        )

    def _build_word_section(self, title: str, words: List[str], section_key: str) -> ft.Control:
        colors = palette(self.host_page)
        word_controls = [ft.Text(word, color=colors["text"], selectable=True) for word in words]
        if not word_controls:
            word_controls = [ft.Text("No words recorded yet.", color=colors["muted"], italic=True)]

        content = ft.Column(
            controls=word_controls,
            visible=False,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            height=min(240, max(80, 32 * min(len(word_controls), 6))),
        )
        toggle_button = ft.TextButton(
            f"Show words ({len(words)})",
            on_click=lambda e, key=section_key: self._toggle_word_section(key),
        )
        self.word_sections[section_key] = {
            "content": content,
            "button": toggle_button,
            "title": title,
            "count": len(words),
        }

        return ft.Container(
            padding=16,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=12,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=colors["text"], expand=True),
                            ft.Text(str(len(words)), size=18, weight=ft.FontWeight.BOLD, color=colors["primary"]),
                        ],
                    ),
                    toggle_button,
                    content,
                ],
                spacing=10,
            ),
        )

    def _toggle_word_section(self, section_key: str) -> None:
        section = self.word_sections[section_key]
        content = section["content"]
        button = section["button"]
        content.visible = not content.visible
        button.text = (
            f"Hide words ({section['count']})"
            if content.visible
            else f"Show words ({section['count']})"
        )
        if self.debug_report:
            self.debug_report(
                "history_toggle_word_section",
                section=section_key,
                visible=content.visible,
                count=section["count"],
            )
        self._safe_update()

    def _build_session_rows(self) -> List[ft.Control]:
        colors = palette(self.host_page)
        if not self.sessions:
            return [
                ft.Container(
                    padding=16,
                    border_radius=8,
                    bgcolor=colors["card_alt_bg"],
                    content=ft.Text("No sessions saved yet.", color=colors["muted"]),
                )
            ]

        session_rows = []
        for idx, session in enumerate(reversed(self.sessions)):
            practice_attempts = session.get("practice_attempts", [])
            mistakes_button = None
            if session.get("mistakes"):
                mistakes_button = ft.ElevatedButton(
                    "View Mistakes",
                    width=150,
                    height=30,
                    on_click=lambda _, m=session["mistakes"]: self._show_mistake_dialog(m),
                )

            subtitle_lines = []
            if practice_attempts:
                practice_parts = [
                    f"{attempt['score']}/{attempt['total']} ({attempt.get('accuracy', 0):.1f}%)"
                    for attempt in practice_attempts
                ]
                subtitle_lines.append(
                    f"Practice follow-up: {len(practice_attempts)} run(s) | " + ", ".join(practice_parts)
                )

            session_rows.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{session['date']}  |  Score: {session['score']}/{session['total']} ({session.get('accuracy', 0):.2f}%)",
                                        size=14,
                                        color=colors["text"],
                                        expand=True,
                                    ),
                                    mistakes_button if mistakes_button else ft.Container(width=0),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            *[
                                ft.Text(line, size=12, color=colors["muted"], italic=True)
                                for line in subtitle_lines
                            ],
                        ],
                        spacing=6,
                    ),
                    padding=10,
                    border_radius=8,
                    bgcolor=colors["card_bg"] if idx % 2 == 0 else colors["card_alt_bg"],
                    border=ft.border.all(1, colors["card_border"]),
                )
            )
        return session_rows

    def _show_mistake_dialog(self, mistakes: List[Tuple[str, str]]) -> None:
        if self.debug_report:
            self.debug_report("history_view_mistakes", count=len(mistakes))
        colors = palette(self.host_page)
        content = "WORDS TO REVIEW:\n" + "-" * 20 + "\n"
        for chi, correct in mistakes:
            content += f"❌ {chi} -> {correct}\n"

        mistake_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Mistake Review", color=colors["text"]),
            content=ft.Column(
                [ft.Text(content, font_family="monospace", color=colors["text"])],
                scroll=ft.ScrollMode.AUTO,
                tight=True,
            ),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        mistake_dialog.actions = [
            ft.TextButton("Close", on_click=lambda e: self._close_dialog(mistake_dialog)),
        ]

        self.host_page.overlay.append(mistake_dialog)
        mistake_dialog.open = True
        self.host_page.update()

    def _close_dialog(self, dialog):
        if self.debug_report:
            self.debug_report("history_close_mistakes_dialog")
        dialog.open = False
        self.host_page.update()
