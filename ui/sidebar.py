import customtkinter as ctk
from typing import Callable, Optional


class Sidebar:
    def __init__(self, root: ctk.CTk,
                 on_home_click: Callable,
                 on_settings_click: Callable,
                 on_toggle_appearance: Callable[[bool], None]):
        self.root = root
        self.on_home_click = on_home_click
        self.on_settings_click = on_settings_click
        self.on_toggle_appearance = on_toggle_appearance

        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self.root, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)  # Push bottom items down

        self.name_display: Optional[ctk.CTkLabel] = None
        self.stats_label: Optional[ctk.CTkLabel] = None
        self.appearance_switch: Optional[ctk.CTkSwitch] = None

        self._init_sidebar()

    def _init_sidebar(self) -> None:
        """Builds the persistent left-hand navigation."""
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        logo = ctk.CTkLabel(self.sidebar_frame, text="VOCAB\nMASTER", font=("Inter", 24, "bold"), text_color="#3b82f6")
        logo.pack(pady=(30, 40))

        # Identity Section
        self.name_display = ctk.CTkLabel(self.sidebar_frame, text="No Student Active", font=("Inter", 12, "italic"), text_color="gray")
        self.name_display.pack(pady=10)

        # Stats Section
        self.stats_label = ctk.CTkLabel(self.sidebar_frame, text="Session Stats\n--", font=("Inter", 13), justify="center")
        self.stats_label.pack(pady=20)

        # Navigation Buttons
        self.btn_home = ctk.CTkButton(self.sidebar_frame, text="🏠 Home", fg_color="transparent", 
                                       text_color=("black", "white"), anchor="w", command=self.on_home_click)
        self.btn_home.pack(pady=5, padx=20, fill="x")

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙️ Settings", fg_color="transparent", 
                                           text_color=("black", "white"), anchor="w", command=self.on_settings_click)
        self.btn_settings.pack(pady=5, padx=20, fill="x")

        # Bottom Sidebar Items
        self.appearance_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", command=self._handle_appearance_toggle)
        if ctk.get_appearance_mode() == "Dark":
            self.appearance_switch.select()
        self.appearance_switch.pack(side="bottom", pady=20)

    def _handle_appearance_toggle(self) -> None:
        """Handle appearance toggle switch change."""
        is_dark = self.appearance_switch.get() == 1
        self.on_toggle_appearance(is_dark)

    def update_student_name(self, name: str) -> None:
        """Update the displayed student name."""
        if self.name_display:
            if name:
                self.name_display.configure(text=f"Student: {name}", font=("Inter", 14, "bold"), text_color="#3b82f6")
            else:
                self.name_display.configure(text="No Student Active", font=("Inter", 12, "italic"), text_color="gray")

    def update_stats(self, total_correct: int = 0, total_attempted: int = 0) -> None:
        """Update the displayed session statistics."""
        if self.stats_label:
            if total_attempted == 0:
                self.stats_label.configure(text="No quizzes completed yet.")
            else:
                self.stats_label.configure(text=f"Session Progress\n{total_correct}/{total_attempted} Correct")
