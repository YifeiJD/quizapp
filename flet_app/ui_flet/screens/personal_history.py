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
                if result.get("is_correct") or result.get("status") == "correct":
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
            
            # Action buttons for cumulative word lists
            ft.ResponsiveRow(
                controls=[
                    self._build_word_list_button("Distinct Words Tested", stats["tested_words"], colors["primary"], ft.Icons.LIST_ALT),
                    self._build_word_list_button("Words Learned", stats["learned_words"], colors["success"], ft.Icons.CHECK_CIRCLE_OUTLINE),
                    self._build_word_list_button("Words Gotten Wrong", stats["wrong_words"], colors["danger"], ft.Icons.ERROR_OUTLINE),
                ],
                spacing=10,
                run_spacing=10,
            ),
            
            ft.Divider(height=8, color="transparent"),
            ft.Text("Session Timeline", size=22, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Column(controls=session_rows, spacing=10),
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

    def _build_word_list_button(self, title: str, words: List[str], color: str, icon: str) -> ft.Control:
        return ft.Container(
            col={"sm": 12, "md": 4},
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, size=20),
                    ft.Text(f"{title} ({len(words)})", size=14, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                style=ft.ButtonStyle(
                    color=color,
                    padding=20,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=lambda _: self._show_word_list_dialog(title, words, color),
            )
        )

    def _show_word_list_dialog(self, title: str, words: List[str], color: str) -> None:
        colors = palette(self.host_page)
        word_controls = [ft.Text(word, color=colors["text"], selectable=True, size=14) for word in words]
        if not word_controls:
            word_controls = [ft.Text("No words recorded yet.", color=colors["muted"], italic=True)]

        # Get window height with a safe fallback
        win_h = self.host_page.window.height if self.host_page.window.height else 800
        
        content_container = ft.Container(
            content=ft.Column(
                controls=word_controls,
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                spacing=8,
            ),
            width=400,
        )
        content_container.max_height = win_h * 0.6

        dialog = ft.AlertDialog(
            title=ft.Text(title, color=color, weight=ft.FontWeight.BOLD),
            content=content_container,
            actions=[
                ft.TextButton("Dismiss", on_click=lambda e: self._close_dialog(dialog))
            ],
        )
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

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
            
            details_button = ft.ElevatedButton(
                "Details",
                width=120,
                height=35,
                icon=ft.Icons.LIST_ALT_OUTLINED,
                on_click=lambda _, s=session: self._show_session_details_dialog(s),
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
                                    details_button,
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
                    padding=12,
                    border_radius=10,
                    bgcolor=colors["card_bg"] if idx % 2 == 0 else colors["card_alt_bg"],
                    border=ft.border.all(1, colors["card_border"]),
                )
            )
        return session_rows

    def _show_session_details_dialog(self, session: Dict[str, Any]) -> None:
        """Show a detailed pop-up of all words in a specific session."""
        colors = palette(self.host_page)
        results_log = session.get("results_log", []) or session.get("log", [])
        
        learned_items = []
        missed_items = []
        
        for item in results_log:
            chi = item.get("chi", "N/A")
            correct = item.get("correct", "N/A")
            entry = f"{chi} -> {correct}"
            if item.get("is_correct") or item.get("status") == "correct":
                learned_items.append(ft.Text(f"✅ {entry}", color=colors["success"], size=14))
            else:
                missed_items.append(ft.Text(f"❌ {entry}", color=colors["danger"], size=14))

        content_controls = []
        
        if learned_items:
            content_controls.append(ft.Text("LEARNED WORDS:", weight=ft.FontWeight.BOLD, color=colors["success"]))
            content_controls.extend(learned_items)
            content_controls.append(ft.Divider(height=10, color="transparent"))
            
        if missed_items:
            content_controls.append(ft.Text("MISSED WORDS:", weight=ft.FontWeight.BOLD, color=colors["danger"]))
            content_controls.extend(missed_items)
            
        if not content_controls:
            content_controls.append(ft.Text("No word data available for this session.", italic=True, color=colors["muted"]))

        content_container = ft.Container(
            content=ft.Column(
                controls=content_controls,
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                spacing=5,
            ),
            width=400,
        )
        content_container.max_height = page_height_helper(self.host_page) * 0.6

        dialog = ft.AlertDialog(
            title=ft.Text(f"Session: {session.get('date', 'Unknown')}", color=colors["text"]),
            content=content_container,
            actions=[
                ft.TextButton("Dismiss", on_click=lambda e: self._close_dialog(dialog))
            ],
        )
        
        self.host_page.overlay.append(dialog)
        dialog.open = True
        self.host_page.update()

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        if self.debug_report:
            self.debug_report("history_close_dialog")
        dialog.open = False
        self.host_page.update()


def page_height_helper(page: ft.Page) -> float:
    try:
        return page.window.height or 800
    except:
        return 800
