import flet as ft
from pathlib import Path
from flet_app.ui_flet.theme import palette

def normalize_student_name(name: str) -> str:
    """Standardizes student names with titles and casing."""
    parts = [part for part in (name or "").strip().split() if part]
    if not parts:
        return ""
    if len(parts) == 1 and parts[0].lower() == "admin":
        return "Admin"
    
    if len(parts) > 1:
        first_name = parts[0].lower()
        last_name = parts[-1][:1].upper() + parts[-1][1:].lower()
        
        # Simple gender heuristic
        male_exceptions = {"george", "mike", "charlie", "henry", "anthony", "steve", "dave", "joe", "jake", "luke", "blake", "kyle", "tyler", "jesse", "chase", "cole", "gabe", "matthew", "andrew"}
        female_exceptions = {"sarah", "elizabeth", "lauren", "megan", "rachel", "hannah", "abigail", "madison", "eleanor", "vivian", "lillian", "allison", "carmen", "jocelyn", "ruth", "edith"}
        
        if first_name in male_exceptions:
            title = "Mr."
        elif first_name in female_exceptions:
            title = "Ms."
        elif first_name[-1:] in ('a', 'e', 'i', 'y'):
            title = "Ms."
        else:
            title = "Mr."
        return f"{title} {last_name}"
    
    return parts[0][:1].upper() + parts[0][1:].lower()

def show_message(page: ft.Page, message: str, color: str = "errorContainer") -> None:
    """Show a transient message to the user."""
    colors = palette(page)
    # Map semantic color names to actual hex colors from our theme
    bgcolor = colors["danger"]
    if color == "primaryContainer":
        bgcolor = colors["success"]
    elif color.startswith("#"):
        bgcolor = color
        
    snack = ft.SnackBar(
        content=ft.Text(message, color="#FFFFFF", weight=ft.FontWeight.BOLD),
        bgcolor=bgcolor,
        open=True,
        duration=5000,
    )
    if hasattr(page, "open"):
        page.open(snack)
    else:
        page.snack_bar = snack
    page.update()

def confirm_action(page: ft.Page, title: str, message: str, on_confirm, debug_report=None) -> None:
    """Open a confirmation dialog."""
    if debug_report:
        debug_report("confirm_open", title=title, message=message)
        
    def close_dialog(e):
        dialog.open = False
        if debug_report:
            debug_report("dialog_close")
        page.update()

    def confirm_and_close(e):
        dialog.open = False
        page.update()
        on_confirm()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton("Continue", on_click=confirm_and_close),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_download_success(page: ft.Page, path: Path) -> None:
    """Show a clear dialog when a download finishes."""
    colors = palette(page)
    
    def close_dialog(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        modal=False,
        title=ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=colors["success"]),
            ft.Text("Download Complete", color=colors["text"])
        ], spacing=10),
        content=ft.Column([
            ft.Text("The file has been successfully saved to your Downloads folder:", color=colors["text"]),
            ft.Container(
                content=ft.Text(str(path), color=colors["primary"], size=13, weight=ft.FontWeight.BOLD),
                padding=10,
                bgcolor=colors["card_alt_bg"],
                border_radius=8,
            )
        ], tight=True, spacing=10),
        actions=[
            ft.TextButton("Dismiss", on_click=close_dialog)
        ],
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
