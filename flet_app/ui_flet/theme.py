import flet as ft


def palette(page: ft.Page) -> dict:
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    if is_dark:
        return {
            "page_bg": "#0B0F19",
            "workspace_bg": "#111827",
            "sidebar_bg": "#111827",
            "card_bg": "#1F2937",
            "card_alt_bg": "#374151",
            "card_border": "#4B5563",
            "text": "#F9FAFB",
            "muted": "#9CA3AF",
            "primary": "#6366F1",  # Modern Indigo
            "primary_text": "#FFFFFF",
            "success": "#10B981",  # Vibrant Emerald
            "danger": "#EF4444",   # Punchy Rose
            "warning": "#F59E0B",
            "divider": "#334155",
            "surface_tint": "#172554",
        }
    else:
        return {
            "page_bg": "#E5E7EB",
            "workspace_bg": "#F9FAFB",
            "sidebar_bg": "#E5E7EB",
            "card_bg": "#FFFFFF",
            "card_alt_bg": "#F3F4F6",
            "card_border": "#E5E7EB",
            "text": "#111827",
            "muted": "#6B7280",
            "primary": "#4F46E5",
            "primary_text": "#FFFFFF",
            "success": "#10B981",
            "danger": "#EF4444",
            "warning": "#F59E0B",
            "divider": "#CBD5E1",
            "surface_tint": "#DBEAFE",
        }
