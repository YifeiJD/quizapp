import flet as ft
from typing import Callable, Dict, Optional
from flet_app.ui_flet.theme import palette


class QuizConfigScreen(ft.Container):
    def __init__(self, page: ft.Page, total_available: int, on_start_quiz: Callable[[int, int, Dict], None], on_back: Callable, saved_config: Dict = None, debug_report: Optional[Callable[..., None]] = None):
        super().__init__(expand=True)
        self.host_page = page
        self.total_available = total_available
        self.on_start_quiz = on_start_quiz
        self.on_back = on_back
        self.saved_config = saved_config or {}
        self.debug_report = debug_report

        self.content = self._build_ui()
        self.alignment = ft.alignment.Alignment(0, 0)
        
        self._starting = False
        # Allow Enter key to trigger quiz start globally on this screen
        self.host_page.on_keyboard_event = self._handle_key_event

    def _safe_update(self) -> None:
        """Update only after the control has been mounted on a page."""
        try:
            self.update()
        except AssertionError:
            pass
    
    def _build_ui(self) -> ft.Container:
        colors = palette(self.host_page)
        saved_word_count = self.saved_config.get("word_count", str(self.total_available))
        saved_timer_choice = self.saved_config.get("timer_choice", "10s")
        saved_custom_time = self.saved_config.get("custom_time", "")
        self.timer_choice = saved_timer_choice
        self.timer_buttons: Dict[str, ft.ElevatedButton] = {}

        self.count_input = ft.TextField(
            value=saved_word_count,
            label="Words to include",
            text_align=ft.TextAlign.CENTER,
            height=50,
            text_size=18,
            on_change=self._clear_feedback,
            color=colors["text"],
            border_color=colors["card_border"],
            on_submit=self._on_start_click,
        )

        timer_options = ["5s", "10s", "15s", "∞", "Custom"]
        timer_option_row = ft.ResponsiveRow(
            controls=[self._build_timer_button(option) for option in timer_options],
            run_spacing=10,
            spacing=10,
        )
        
        self.custom_timer = ft.TextField(
            hint_text="Seconds...",
            value=saved_custom_time,
            text_align=ft.TextAlign.CENTER,
            height=50,
            visible=(saved_timer_choice == "Custom"),
            on_change=self._clear_feedback,
            color=colors["text"],
            border_color=colors["card_border"],
            on_submit=self._on_start_click,
        )
        self.feedback_text = ft.Text("", color=colors["danger"], visible=False)
        
        form_card = ft.Container(
            content=ft.Column([
                ft.Text("Quiz Configuration", size=32, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Divider(height=30, color="transparent"),
                ft.Text("Number of Words", size=16, weight=ft.FontWeight.BOLD, color=colors["text"]),
                self.count_input,
                ft.Divider(height=20, color="transparent"),
                ft.Text("Time Limit per Word", size=16, weight=ft.FontWeight.BOLD, color=colors["text"]),
                timer_option_row,
                self.custom_timer,
                self.feedback_text,
                ft.Divider(height=30, color="transparent"),
                ft.ElevatedButton(
                    "Start Quiz",
                    on_click=self._on_start_click,
                    style=ft.ButtonStyle(padding=20),
                    width=370,
                    height=50,
                    bgcolor=colors["primary"],
                    color=colors["primary_text"]
                ),
                ft.Divider(height=10, color="transparent"),
                ft.TextButton("← Back", on_click=lambda e: self.on_back())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=450,
            padding=40,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["card_border"]),
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=25, color="#00000014", offset=ft.Offset(0, 8)),
        )
        return form_card

    def _build_timer_button(self, option: str) -> ft.Control:
        button = ft.ElevatedButton(
            option,
            col={"sm": 6, "md": 4},
            on_click=lambda e, value=option: self._select_timer(value),
        )
        self.timer_buttons[option] = button
        self._apply_timer_button_style(button, option == self.timer_choice)
        return button

    def _apply_timer_button_style(self, button: ft.ElevatedButton, selected: bool) -> None:
        colors = palette(self.host_page)
        button.bgcolor = colors["primary"] if selected else colors["card_alt_bg"]
        button.color = colors["primary_text"] if selected else colors["text"]
        button.style = ft.ButtonStyle(
            padding=16,
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, colors["primary"] if selected else colors["card_border"]),
        )

    def _clear_feedback(self, e=None):
        self.count_input.error_text = None
        self.custom_timer.error_text = None
        self.feedback_text.value = ""
        self.feedback_text.visible = False
        self._safe_update()

    def _show_feedback(self, message: str, field: Optional[ft.TextField] = None):
        if self.debug_report:
            self.debug_report("quiz_config_feedback", message=message, field=getattr(field, "label", None))
        if field is not None:
            field.error_text = message
        self.feedback_text.value = message
        self.feedback_text.visible = True
        self._safe_update()

    def _select_timer(self, value: str):
        self.timer_choice = value
        for option, button in self.timer_buttons.items():
            self._apply_timer_button_style(button, option == value)
        if self.debug_report:
            self.debug_report("quiz_config_timer_changed", value=value)
        self._clear_feedback()
        self.custom_timer.visible = value == "Custom"
        self._safe_update()

    def _handle_key_event(self, e):
        if getattr(e, "key", None) == "Enter":
            self._on_start_click(e)

    def _on_start_click(self, e):
        if getattr(self, "_starting", False):
            return
            
        try:
            if self.debug_report:
                self.debug_report(
                    "quiz_config_start_attempt",
                    count_value=self.count_input.value,
                    timer_value=self.timer_choice,
                    custom_time=self.custom_timer.value,
                )
            self._clear_feedback()

            count_raw = (self.count_input.value or "").strip()
            # Robustly parse numeric value (e.g., "5 words" -> 5)
            count_clean = "".join(filter(str.isdigit, count_raw))
            count = int(count_clean) if count_clean else self.total_available
            
            if count <= 0 or count > self.total_available:
                self._show_feedback(
                    f"Enter a word count between 1 and {self.total_available}.",
                    self.count_input,
                )
                return
            
            timer_val = self.timer_choice
            if not timer_val:
                self._show_feedback("Choose a timer option before starting.")
                return

            if timer_val == "∞":
                time_limit = 0
            elif timer_val == "Custom":
                custom_raw = (self.custom_timer.value or "").strip()
                if not custom_raw:
                    self._show_feedback("Enter a custom number of seconds.", self.custom_timer)
                    return
                # Robustly parse numeric value (e.g., "5 s" -> 5)
                custom_clean = "".join(filter(str.isdigit, custom_raw))
                if not custom_clean:
                    self._show_feedback("Please enter valid whole numbers.", self.custom_timer)
                    return
                time_limit = int(custom_clean)
                if time_limit <= 0:
                    self._show_feedback("Custom time must be greater than 0 seconds.", self.custom_timer)
                    return
            else:
                time_limit = int(timer_val.replace("s", "").strip())
            
            config = {
                "word_count": str(count),
                "timer_choice": timer_val,
                "custom_time": (self.custom_timer.value or "").strip()
            }
            if self.debug_report:
                self.debug_report("quiz_config_start_success", count=count, time_limit=time_limit, config=config)
            self._starting = True
            self.on_start_quiz(count, time_limit, config)
        except (ValueError, TypeError) as ex:
            # If it's a parsing error of our expected fields, show the friendly message
            if "int()" in str(ex) or "isdigit" in str(ex):
                field = self.custom_timer if self.timer_choice == "Custom" else self.count_input
                self._show_feedback("Please enter valid whole numbers.", field)
            else:
                # Otherwise, it might be a code error (like missing arguments)
                if self.debug_report:
                    import traceback
                    self.debug_report("quiz_config_critical_error", error=str(ex), traceback=traceback.format_exc())
                self._show_feedback(f"A system error occurred: {ex}")
        except Exception as ex:
            if self.debug_report:
                import traceback
                self.debug_report("quiz_config_unexpected_error", error=str(ex), traceback=traceback.format_exc())
            self._show_feedback(f"Unexpected error: {ex}")
