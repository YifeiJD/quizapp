import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Dict, Tuple


class SettingsScreen:
    def __init__(self, master: ctk.CTkFrame,
                 current_resolution: Tuple[int, int],
                 on_resolution_change: Callable[[Tuple[int, int]], None],
                 on_reset_session: Callable,
                 on_view_history: Callable):
        self.master = master
        self.current_resolution = current_resolution
        self.on_resolution_change = on_resolution_change
        self.on_reset_session = on_reset_session
        self.on_view_history = on_view_history

        self.res_options: Dict[str, Tuple[int, int]] = {
            "Standard (1024 x 720)": (1024, 720),
            "Compact (960 x 640)": (960, 640),
            "Wide HD (1280 x 800)": (1280, 800),
            "Large (1152 x 864)": (1152, 864)
        }
        self.res_dropdown: Optional[ctk.CTkComboBox] = None

        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self.master, text="Settings & Records", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 20))

        # Personal History Button
        ctk.CTkButton(self.master, text="📜 View My Personal History",
                      fg_color="#3b82f6", height=45,
                      command=self.on_view_history).pack(fill="x", pady=10)

        ctk.CTkLabel(self.master, text="Window Resolution", font=("Inter", 16, "bold")).pack(anchor="w", pady=(20, 10))
        ctk.CTkLabel(self.master, text="Choose a layout that fits your screen best.", font=("Inter", 13), text_color="gray").pack(anchor="w", pady=(0, 15))

        self.res_dropdown = ctk.CTkComboBox(self.master, values=list(self.res_options.keys()), width=300, height=40)
        current_res_str = f"{self.current_resolution[0]} x {self.current_resolution[1]}"
        # Find closest match or use default
        self.res_dropdown.set("Standard (1024 x 720)")
        self.res_dropdown.pack(anchor="w", pady=10)

        ctk.CTkButton(self.master, text="Apply Resolution", command=self._apply_resolution, width=200, height=40).pack(anchor="w", pady=20)

        ctk.CTkLabel(self.master, text="Session Management", font=("Inter", 16, "bold")).pack(anchor="w", pady=(30, 10))
        ctk.CTkButton(self.master, text="Reset Entire Session", fg_color="#dc2626", hover_color="#b91c1c",
                      command=self._confirm_reset, width=200).pack(anchor="w")

    def _apply_resolution(self) -> None:
        """Apply selected resolution."""
        if self.res_dropdown:
            choice = self.res_dropdown.get()
            new_res = self.res_options.get(choice, (1024, 720))
            self.on_resolution_change(new_res)
            messagebox.showinfo("Success", f"Resolution updated to {choice}")

    def _confirm_reset(self) -> None:
        """Confirm session reset."""
        if messagebox.askyesno("Confirm Reset", "This will wipe all session history and mistakes. Continue?"):
            self.on_reset_session()
