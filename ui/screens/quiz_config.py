import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Dict, Optional


class QuizConfigScreen:
    def __init__(self, master: ctk.CTkFrame,
                 total_available: int,
                 on_start_quiz: Callable[[int, int, Dict[str, str]], None],
                 saved_config: Optional[Dict[str, str]] = None):
        self.master = master
        self.total_available = total_available
        self.saved_config = saved_config or {}
        self.on_start_quiz = on_start_quiz

        self.seg_timer: Optional[ctk.CTkSegmentedButton] = None
        self.custom_timer_entry: Optional[ctk.CTkEntry] = None
        self.entry_count: Optional[ctk.CTkEntry] = None

        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self.master, text="Quiz Configuration", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 40))

        settings_row = ctk.CTkFrame(self.master, fg_color="transparent")
        settings_row.pack(fill="x")

        # --- Timer Column ---
        timer_col = ctk.CTkFrame(settings_row, fg_color="transparent")
        timer_col.pack(side="left", expand=True, fill="both", padx=(0, 20))
        
        ctk.CTkLabel(timer_col, text="Time Limit per Word", font=("Inter", 14, "bold")).pack(anchor="w")
        self.seg_timer = ctk.CTkSegmentedButton(timer_col, values=["5s", "10s", "15s", "∞", "Custom"],
                                                command=self._timer_choice_handler, height=40)
        
        # Set saved timer or default to 10s
        saved_timer = self.saved_config.get("timer_choice", "10s")
        self.seg_timer.set(saved_timer)
        self.seg_timer.pack(pady=10, fill="x")

        self.custom_timer_entry = ctk.CTkEntry(timer_col, placeholder_text="Seconds...", height=40)
        if saved_timer == "Custom":
            self.custom_timer_entry.insert(0, self.saved_config.get("custom_time", ""))
            self.custom_timer_entry.pack(pady=5, fill="x")

        # --- Word Count Column ---
        count_col = ctk.CTkFrame(settings_row, fg_color="transparent")
        count_col.pack(side="left", expand=True, fill="both", padx=(20, 0))
        
        ctk.CTkLabel(count_col, text="Word Count", font=("Inter", 14, "bold")).pack(anchor="w")
        self.entry_count = ctk.CTkEntry(count_col, height=40, font=("Inter", 16))
        
        # Set saved word count or default to total list size
        saved_count = self.saved_config.get("word_count", str(self.total_available))
        self.entry_count.insert(0, saved_count)
        self.entry_count.pack(pady=10, fill="x")

        ctk.CTkButton(self.master, text="Begin Quiz Session", font=("Inter", 16, "bold"),
                      height=60, command=self._validate_and_start).pack(side="bottom", fill="x", pady=20)

    def _timer_choice_handler(self, val: str) -> None:
        """Handle timer selection change."""
        if val == "Custom":
            self.custom_timer_entry.pack(pady=5, fill="x")
        else:
            self.custom_timer_entry.pack_forget()

    def _validate_and_start(self) -> None:
        """Validate inputs and start quiz."""
        try:
            if not self.seg_timer or not self.entry_count or not self.custom_timer_entry:
                return

            # Capture settings
            choice = self.seg_timer.get()
            custom_val = self.custom_timer_entry.get().strip()
            count_val = self.entry_count.get().strip()

            # Timer Logic
            if choice == "Custom":
                time_limit = int(custom_val) if custom_val else 10
            elif choice == "∞":
                time_limit = 0
            else:
                time_limit = int(choice.replace("s", ""))

            # Count Logic
            count = int(count_val) if count_val else self.total_available
            if count > self.total_available or count <= 0:
                messagebox.showwarning("Invalid Amount", f"Please enter a number between 1 and {self.total_available}.")
                return

            # Save config for next time
            config = {
                "timer_choice": choice,
                "custom_time": custom_val,
                "word_count": count_val
            }

            self.on_start_quiz(count, time_limit, config)

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
