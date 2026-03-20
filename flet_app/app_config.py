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
    page.theme = ft.Theme(
        color_scheme_seed="#2563EB",
        font_family="Avenir",
        use_material3=True,
        scaffold_bgcolor="#E5E7EB",
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed="#60A5FA",
        font_family="Avenir",
        use_material3=True,
        scaffold_bgcolor="#0F172A",
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
