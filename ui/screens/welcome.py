import customtkinter as ctk
from typing import Callable, List, Optional


class WelcomeScreen:
    def __init__(self, master: ctk.CTkFrame,
                 student_name: str,
                 saved_files: List[str],
                 on_start_click: Callable[[str, str], None],
                 student_data: Optional[dict] = None):
        self.master = master
        self.student_name = student_name
        self.saved_files = saved_files
        self.on_start_click = on_start_click
        self.student_data = student_data

        self.entry_name: Optional[ctk.CTkEntry] = None
        self.combo_lists: Optional[ctk.CTkComboBox] = None

        self._build_ui()

    def _build_ui(self) -> None:
        header_text = "Study Dashboard" if self.student_name else "Welcome to Vocab Master"
        header = ctk.CTkLabel(self.master, text=header_text, font=("Inter", 32, "bold"))
        header.pack(anchor="w", pady=(0, 10))
        
        # If student is logged in, show a greeting
        if self.student_name:
            greet = f"Ready for another round, {self.student_name}?"
            ctk.CTkLabel(self.master, text=greet, font=("Inter", 18), text_color="#3b82f6").pack(anchor="w", pady=(0, 30))
        else:
            ctk.CTkLabel(self.master, text="Please identify yourself to begin.", font=("Inter", 16), text_color="gray").pack(anchor="w", pady=(0, 40))

        form_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        form_frame.pack(fill="x")

        # Identity Section
        if not self.student_name:
            ctk.CTkLabel(form_frame, text="Your Name", font=("Inter", 13, "bold")).pack(anchor="w")
            self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="e.g. Yifei Zhang", height=45)
            self.entry_name.pack(pady=(5, 20), fill="x")
        
        # List Selection (Always visible)
        ctk.CTkLabel(form_frame, text="Select Vocabulary List", font=("Inter", 13, "bold")).pack(anchor="w")
        self.combo_lists = ctk.CTkComboBox(form_frame, values=self.saved_files, height=45)
        if self.saved_files:
            self.combo_lists.set(self.saved_files[0])
        self.combo_lists.pack(pady=(5, 20), fill="x")

        # Start Button
        ctk.CTkButton(form_frame, text="Configure Quiz →", command=self._handle_start,
                      height=50, font=("Inter", 14, "bold")).pack(fill="x", pady=20)
        
        # Mini-Stats (If user exists)
        if self.student_name and self.student_data:
            total = self.student_data.get("total_words_learned", 0)
            ctk.CTkLabel(self.master, text=f"Cumulative Words Learned: {total}", font=("Inter", 12, "italic")).pack(pady=10)

    def _handle_start(self) -> None:
        """Handle start button click."""
        name = self.student_name
        if not name and self.entry_name:
            name = self.entry_name.get().strip()
        
        selected_file = ""
        if self.combo_lists:
            selected_file = self.combo_lists.get()
        
        self.on_start_click(name, selected_file)
