from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import logging

import flet as ft

from flet_app.ui_flet.theme import palette


DEFAULT_APP_RESOLUTION = (1000, 700)
WINDOW_FRAME_PADDING = (40, 96)
APP_SHELL_PADDING = 16
MIN_WINDOW_SIZE = (900, 600)
TOP_WINDOW_MARGIN = 24


def log_flet_version(logger: logging.Logger) -> None:
    try:
        print(f"Flet version: {version('flet')}")
    except PackageNotFoundError:
        logger.info("Could not determine installed Flet package version.")


def window_size_for_resolution(app_resolution: tuple[int, int]) -> tuple[int, int]:
    shell_padding = APP_SHELL_PADDING * 2
    return (
        app_resolution[0] + shell_padding + WINDOW_FRAME_PADDING[0],
        app_resolution[1] + shell_padding + WINDOW_FRAME_PADDING[1],
    )


def configure_page(page: ft.Page, app_resolution: tuple[int, int]) -> None:
    page.title = "Vocab Master"
    
    literature_font_stack = "Bookerly, 'Palatino Linotype', Palatino, Georgia, 'Times New Roman', serif"
    
    page.theme = ft.Theme(
        color_scheme_seed="#4F46E5",  # Sleek modern Indigo
        font_family=literature_font_stack,
        use_material3=True,
        scaffold_bgcolor="#F3F4F6",  # Softer gray
        visual_density=ft.VisualDensity.COMFORTABLE,
        page_transitions=ft.PageTransitionsTheme(
            macos=ft.PageTransitionTheme.FADE_UPWARDS,
            windows=ft.PageTransitionTheme.FADE_UPWARDS,
        ),
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed="#818CF8",  # Lighter Indigo for dark mode contrast
        font_family=literature_font_stack,
        use_material3=True,
        scaffold_bgcolor="#0B0F19",  # Deeper sleek dark background
        visual_density=ft.VisualDensity.COMFORTABLE,
        page_transitions=ft.PageTransitionsTheme(
            macos=ft.PageTransitionTheme.FADE_UPWARDS,
            windows=ft.PageTransitionTheme.FADE_UPWARDS,
        ),
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    window_width, window_height = window_size_for_resolution(app_resolution)
    page.window.width = window_width
    page.window.height = window_height
    page.window.min_width = MIN_WINDOW_SIZE[0]
    page.window.min_height = MIN_WINDOW_SIZE[1]
    page.expand = True
    page.bgcolor = palette(page)["page_bg"]
