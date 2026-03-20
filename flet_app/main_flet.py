import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path

# Ensure shared root modules can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import flet as ft
from core.debug_report import configure_debug_logging, emit_debug_report
from core.admin_settings import AdminSettings
from flet_app.app_config import (
    APP_SHELL_PADDING,
    DEFAULT_APP_RESOLUTION,
    TOP_WINDOW_MARGIN,
    configure_page,
    log_flet_version,
    window_size_for_resolution,
)
from flet_app.app_services import build_services
from flet_app.app_state import AppState
from flet_app.ui_flet.theme import palette
from flet_app.ui_flet.layout import AppLayout

# New Modular Imports
from flet_app.ui_flet.navigator import AppNavigator
from flet_app.ui_flet.controllers.quiz_controller import QuizController
from flet_app.ui_flet.controllers.admin_controller import AdminController

# Configure logging
LOG_PATH = configure_debug_logging("flet_app.log")
logger = logging.getLogger(__name__)

def main(page: ft.Page):
    try:
        log_flet_version(logger)
        configure_page(page, DEFAULT_APP_RESOLUTION)

        # --- Core Services ---
        services = build_services(logger)
        admin_settings = AdminSettings(logger)
        state = AppState(app_resolution=DEFAULT_APP_RESOLUTION)
        
        # Determine export directory
        try:
            export_dir = Path(os.path.join(os.path.expanduser("~"), "Downloads"))
            if not export_dir.exists():
                export_dir = Path(ROOT_DIR) / "debug_reports" / "exports"
                if not export_dir.exists():
                    export_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            export_dir = Path(ROOT_DIR) / "debug_reports" / "exports"
            if not export_dir.exists():
                export_dir.mkdir(parents=True, exist_ok=True)

        def _debug_report(event: str, **details) -> None:
            emit_debug_report(
                logger,
                "DEBUG-REPORT",
                event,
                details=details,
                state=state.snapshot(page),
            )

        # --- UI Initialization ---
        # Note: We use a lambda to defer the navigator call since navigator is defined below
        layout = AppLayout(
            page, 
            on_nav_change=lambda e: navigator.handle_nav_change(e), 
            on_theme_toggle=lambda is_dark: navigator.toggle_theme(is_dark), 
            surface_size=state.app_resolution
        )
        
        navigator = AppNavigator(
            page=page,
            state=state,
            services=services,
            layout=layout,
            admin_settings=admin_settings,
            logger=logger,
            debug_report_func=_debug_report,
            export_dir=export_dir
        )
        
        quiz_controller = QuizController(page, services, state, navigator, logger)
        admin_controller = AdminController(page, services, state, navigator, admin_settings, export_dir)
        
        navigator.set_controllers(quiz_controller, admin_controller)

        app_surface = ft.Container(
            content=layout,
            width=state.app_resolution[0],
            height=state.app_resolution[1],
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=24, color="#00000024", offset=ft.Offset(0, 10)),
            bgcolor=palette(page)["workspace_bg"],
        )
        app_shell = ft.Container(
            content=app_surface,
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
            padding=APP_SHELL_PADDING,
            bgcolor=palette(page)["page_bg"],
        )
        
        # Give navigator references to the shell containers so it can update their themes
        navigator.app_shell = app_shell
        navigator.app_surface = app_surface

        page.add(app_shell)
        layout.initialize()
        navigator.apply_shell_theme()

        # --- Window Management ---
        window_centered = {"done": False}

        def _position_window_top_center() -> None:
            try:
                center_result = page.window.center()
                if asyncio.iscoroutine(center_result):
                    async def _center():
                        await center_result
                        page.window.top = TOP_WINDOW_MARGIN
                        page.update()
                    page.run_task(_center)
                else:
                    page.window.top = TOP_WINDOW_MARGIN
                    page.update()
            except Exception:
                pass

        async def _stabilize_window_geometry(width: int, height: int) -> None:
            window_width, window_height = window_size_for_resolution((width, height))
            for _ in range(3):
                await asyncio.sleep(0.12)
                try:
                    page.window.width = window_width
                    page.window.height = window_height
                    _position_window_top_center()
                    page.update()
                except Exception:
                    return

        def _handle_page_error(e) -> None:
            _debug_report("page_error", data=getattr(e, "data", None), name=getattr(e, "name", None))

        def _handle_lifecycle_change(e) -> None:
            _debug_report("lifecycle", data=getattr(e, "data", None))
            if getattr(e, "data", None) in {"show", "resume"} and not window_centered["done"]:
                try:
                    window_centered["done"] = True
                    page.run_task(
                        _stabilize_window_geometry,
                        state.app_resolution[0],
                        state.app_resolution[1],
                    )
                except Exception:
                    pass

        page.on_error = _handle_page_error
        page.on_app_lifecycle_state_change = _handle_lifecycle_change
        
        def _on_window_event(e):
            if e.data == "close":
                _debug_report("window_close_event")
                page.window.destroy()
        
        page.on_window_event = _on_window_event
        
        _debug_report("app_started", debug_log_path=str(LOG_PATH))
        page.run_task(_stabilize_window_geometry, state.app_resolution[0], state.app_resolution[1])

        # Initial screen
        navigator.show_name_entry()

    except Exception as e:
        logger.exception("Unhandled exception in main")
        try:
            _debug_report("unhandled_exception", error=str(e), traceback=traceback.format_exc())
        except Exception:
            pass

if __name__ == "__main__":
    ft.app(target=main)
