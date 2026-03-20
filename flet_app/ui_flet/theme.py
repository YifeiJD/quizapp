import flet as ft


def is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def palette(page: ft.Page) -> dict:
    if is_dark(page):
        return {
            "page_bg": "#0F172A",
            "workspace_bg": "#111827",
            "sidebar_bg": "#111827",
            "card_bg": "#1E293B",
            "card_alt_bg": "#0F172A",
            "card_border": "#334155",
            "text": "#F8FAFC",
            "muted": "#94A3B8",
            "primary": "#60A5FA",
            "primary_text": "#0B1220",
            "success": "#22C55E",
            "danger": "#F87171",
            "warning": "#F59E0B",
            "divider": "#334155",
            "surface_tint": "#172554",
        }

    return {
        "page_bg": "#E5E7EB",
        "workspace_bg": "#F8FAFC",
        "sidebar_bg": "#E5E7EB",
        "card_bg": "#FFFFFF",
        "card_alt_bg": "#F8FAFC",
        "card_border": "#D1D5DB",
        "text": "#111827",
        "muted": "#6B7280",
        "primary": "#2563EB",
        "primary_text": "#FFFFFF",
        "success": "#16A34A",
        "danger": "#DC2626",
        "warning": "#D97706",
        "divider": "#CBD5E1",
        "surface_tint": "#DBEAFE",
    }
