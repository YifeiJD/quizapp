import flet as ft
from typing import Callable
from flet_app.ui_flet.theme import palette


class AppLayout(ft.Row):
    SIDEBAR_WIDTH = 156

    def __init__(
        self,
        page: ft.Page,
        on_nav_change: Callable,
        on_theme_toggle: Callable[[bool], None],
        surface_size: tuple[int, int],
    ):
        super().__init__()
        self.host_page = page
        self.on_theme_toggle = on_theme_toggle
        self.admin_mode = False
        self.target_width, self.target_height = surface_size
        self.expand = False
        self.spacing = 0
        self.alignment = ft.MainAxisAlignment.START
        self.width = self.target_width
        self.height = self.target_height
        
        # Sidebar Navigation Rail
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=self.SIDEBAR_WIDTH - 24,
            min_extended_width=self.SIDEBAR_WIDTH - 8,
            group_alignment=-0.75,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY_OUTLINED,
                    selected_icon=ft.Icons.HISTORY,
                    label="History"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ASSESSMENT_OUTLINED,
                    selected_icon=ft.Icons.ASSESSMENT,
                    label="Summary"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings"
                ),
            ],
            on_change=on_nav_change,
        )
        
        self.student_label = ft.Text("Hello,", size=20, weight=ft.FontWeight.BOLD, color="#9CA3AF")
        
        # Session Stats Label
        self.stats_label = ft.Text("Session\n--", size=12, text_align=ft.TextAlign.CENTER, color="#666666")
        
        self.dark_mode_switch = ft.Switch(
            label="Dark Mode",
            value=False,
            on_change=lambda e: self.on_theme_toggle(bool(e.control.value)),
        )

        self.rail_container = ft.Container(
            content=self.rail,
            expand=True,
        )

        self.sidebar_content = ft.Column(
            [
                self.student_label,
                ft.Divider(height=8, color="transparent"),
                self.stats_label,
                ft.Divider(height=10, color="transparent"),
                self.rail_container,
                ft.Divider(height=8, color="transparent"),
                self.dark_mode_switch,
            ],
            expand=True,
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
        )
        
        self.sidebar = ft.Container(
            content=self.sidebar_content,
            padding=12,
            width=self.SIDEBAR_WIDTH,
            height=self.target_height,
            bgcolor="#E5E7EB"
        )

        # Main Workspace Container
        self.content_host = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.workspace = ft.Container(
            content=self.content_host,
            expand=True,
            height=self.target_height,
            padding=28,
            bgcolor="#F9FAFB"
        )

        self.controls = [self.sidebar, ft.VerticalDivider(width=1), self.workspace]

    def initialize(self) -> None:
        self.set_nav_enabled(False)
        self.apply_theme()

    def set_admin_mode(self, enabled: bool) -> None:
        self.admin_mode = enabled
        self.apply_theme()

    def set_surface_size(self, width: int, height: int) -> None:
        self.target_width = width
        self.target_height = height
        self.width = width
        self.height = height
        self.sidebar.height = height
        self.workspace.height = height
        self._safe_update()

    def set_content(self, control: ft.Control, centered: bool = True) -> None:
        self.content_host.horizontal_alignment = (
            ft.CrossAxisAlignment.CENTER if centered else ft.CrossAxisAlignment.START
        )
        self.content_host.controls = [control]
        self._safe_update()

    def _safe_update(self) -> None:
        if getattr(self, "page", None) is None or getattr(self, "uid", None) is None:
            return
        try:
            self.update()
        except Exception:
            pass

    def set_student(self, name: str):
        if name:
            self.student_label.value = f"Hello,\n{name}"
            self.student_label.color = palette(self.host_page)["primary"]
            self.student_label.italic = False
        else:
            self.student_label.value = "Hello,\nthere"
            self.student_label.color = palette(self.host_page)["muted"]
            self.student_label.italic = True
        self._safe_update()

    def update_stats(self, total_correct: int = 0, total_attempted: int = 0) -> None:
        """Update the displayed session statistics."""
        if total_attempted == 0:
            self.stats_label.value = "Session Stats\n--"
        else:
            accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
            self.stats_label.value = f"Session Progress\n{total_correct}/{total_attempted} Correct\n({accuracy:.1f}%)"
        self._safe_update()

    def set_nav_enabled(self, enabled: bool) -> None:
        """Enable sidebar navigation once a student session exists."""
        self.rail.disabled = not enabled
        if self.rail.selected_index is None:
            self.rail.selected_index = 0
        self._safe_update()

    def apply_theme(self) -> None:
        colors = palette(self.host_page)
        sidebar_bg = "#3F1D1D" if self.admin_mode and self.host_page.theme_mode == ft.ThemeMode.DARK else (
            "#FDE68A" if self.admin_mode else colors["sidebar_bg"]
        )
        workspace_bg = "#1F2937" if self.admin_mode and self.host_page.theme_mode == ft.ThemeMode.DARK else (
            "#FFF7ED" if self.admin_mode else colors["workspace_bg"]
        )
        accent = "#F59E0B" if self.admin_mode else colors["primary"]
        self.sidebar.bgcolor = sidebar_bg
        self.workspace.bgcolor = workspace_bg
        self.student_label.color = colors["muted"] if self.student_label.italic else accent
        self.stats_label.color = colors["muted"]
        self.dark_mode_switch.label_style = ft.TextStyle(color=colors["text"])
        self.dark_mode_switch.value = self.host_page.theme_mode == ft.ThemeMode.DARK
        self._safe_update()
