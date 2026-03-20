import flet as ft
from typing import Callable, Dict, Tuple, Optional
from flet_app.ui_flet.theme import palette

class SettingsScreen(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        current_resolution: Tuple[int, int],
        show_animations: bool,
        current_fps: int,
        on_resolution_change: Callable[[Tuple[int, int]], None],
        on_animations_toggle: Callable[[bool], None],
        on_fps_change: Callable[[int], None],
        on_reset_session: Callable,
        on_back: Callable,
        on_view_history: Callable,
        on_quit_session: Callable,
        on_session_summary: Callable,
        on_administer_records: Callable,
        debug_report: Optional[Callable[..., None]] = None,
    ):
        super().__init__(expand=True)
        self.host_page = page
        self.current_resolution = current_resolution
        self.show_animations = show_animations
        self.current_fps = current_fps
        self.on_resolution_change = on_resolution_change
        self.on_animations_toggle = on_animations_toggle
        self.on_fps_change = on_fps_change
        self.on_reset_session = on_reset_session
        self.on_back = on_back
        self.on_view_history = on_view_history
        self.on_quit_session = on_quit_session
        self.on_session_summary = on_session_summary
        self.on_administer_records = on_administer_records
        self.debug_report = debug_report
        self.res_options: Dict[str, Tuple[int, int]] = {
            "Standard (1024 x 720)": (1024, 720),
            "Compact (960 x 640)": (960, 640),
            "Wide HD (1280 x 800)": (1280, 800),
            "Large (1152 x 864)": (1152, 864),
        }
        
        self.alignment = ft.MainAxisAlignment.START
        self.controls = self._build_ui()

    def _build_ui(self) -> list[ft.Control]:
        colors = palette(self.host_page)
        current_label = next(
            (label for label, size in self.res_options.items() if size == self.current_resolution),
            "Standard (1024 x 720)",
        )
        self.res_dropdown = ft.Dropdown(
            label="Window Resolution",
            options=[ft.dropdown.Option(label) for label in self.res_options],
            value=current_label,
            width=320,
            color=colors["text"],
            border_color=colors["card_border"],
            on_select=lambda e: self._apply_resolution(),
        )

        return [
            ft.Text("Settings & Records", size=28, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Divider(height=20),
            
            ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=colors["card_bg"],
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON_OUTLINE),
                            ft.Text("Account", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ], spacing=15),
                        ft.Divider(height=10),
                        self._build_settings_row(
                            "View Personal History",
                            "See your past quiz results and progress over time.",
                            ft.Icons.HISTORY,
                            on_click=self.on_view_history,
                            event_name="settings_view_history",
                        ),
                        ft.Divider(height=5),
                        self._build_settings_row(
                            "Quit Current Session",
                            "Ends the current session and returns to the name entry screen.",
                            ft.Icons.EXIT_TO_APP,
                            on_click=self.on_quit_session,
                            event_name="settings_quit_session",
                        ),
                    ])
                )
            ),
            
            ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=colors["card_bg"],
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.DASHBOARD_OUTLINED),
                            ft.Text("Session", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ], spacing=15),
                        ft.Divider(height=10),
                         self._build_settings_row(
                            "View Session Summary",
                            "See a summary of the current session.",
                            ft.Icons.ASSESSMENT_OUTLINED,
                            on_click=self.on_session_summary,
                            event_name="settings_view_summary",
                        ),
                        ft.Divider(height=5),
                        self._build_settings_row(
                            "Reset Entire Session",
                            "Clear current in-memory session progress and return to the start.",
                            ft.Icons.DELETE_SWEEP_OUTLINED,
                            on_click=self.on_reset_session,
                            event_name="settings_reset_session",
                        ),
                    ])
                )
            ),

            ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=colors["card_bg"],
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED),
                            ft.Text("Visuals", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ], spacing=15),
                        ft.Divider(height=10),
                        ft.Row([
                            ft.Column([
                                ft.Text("Enable Animations", size=15, color=colors["text"]),
                                ft.Text("Toggle Duolingo-style fly-ins and feedback effects.", size=12, color=colors["muted"])
                            ], expand=True),
                            ft.Switch(
                                value=self.show_animations,
                                on_change=lambda e: self.on_animations_toggle(e.control.value)
                            )
                        ], spacing=15),
                        ft.Divider(height=15),
                        ft.Row([
                            ft.Column([
                                ft.Text("Animation FPS", size=15, color=colors["text"]),
                                ft.Text("Higher FPS = smoother animations (60 or 120).", size=12, color=colors["muted"])
                            ], expand=True),
                            ft.Dropdown(
                                value=str(self.current_fps),
                                options=[
                                    ft.dropdown.Option("60", "60 FPS (Smooth)"),
                                    ft.dropdown.Option("120", "120 FPS (Ultra Fluid)"),
                                ],
                                width=180,
                                color=colors["text"],
                                border_color=colors["card_border"],
                                on_select=lambda e: self.on_fps_change(int(e.control.value))
                            )
                        ], spacing=15)
                    ])
                )
            ),

            ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=colors["card_bg"],
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED),
                            ft.Text("Administration", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ], spacing=15),
                        ft.Divider(height=10),
                        self._build_settings_row(
                            "Administer Database",
                            "View all students and delete students or individual saved sessions.",
                            ft.Icons.STORAGE_OUTLINED,
                            on_click=self.on_administer_records,
                            event_name="settings_administer_records",
                        ),
                    ])
                )
            ),

            ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=colors["card_bg"],
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.DESKTOP_WINDOWS_OUTLINED),
                            ft.Text("Window", size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ], spacing=15),
                        ft.Divider(height=10),
                        ft.Text("Choose a layout that fits your screen best.", color=colors["muted"]),
                        self.res_dropdown,
                        ft.ElevatedButton(
                            "Apply Resolution",
                            icon=ft.Icons.CROP_FREE,
                            on_click=lambda e: self._apply_resolution(),
                            bgcolor=colors["primary"],
                            color=colors["primary_text"],
                        ),
                    ])
                )
            ),
        ]

    def _build_settings_row(self, title, subtitle, icon, on_click, event_name: Optional[str] = None):
        colors = palette(self.host_page)
        return ft.Row(
            [
                ft.Icon(icon, color=colors["muted"]),
                ft.Column(
                    [
                        ft.Text(title, size=15, color=colors["text"]),
                        ft.Text(subtitle, size=12, color=colors["muted"])
                    ],
                    spacing=2,
                    expand=True
                ),
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self._handle_action(event_name, on_click))
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _handle_action(self, event_name: Optional[str], callback: Callable):
        if self.debug_report and event_name:
            self.debug_report(event_name)
        callback()

    def _apply_resolution(self):
        if self.debug_report:
            self.debug_report("settings_apply_resolution", selected=self.res_dropdown.value)
        self.on_resolution_change(self.res_options[self.res_dropdown.value])
