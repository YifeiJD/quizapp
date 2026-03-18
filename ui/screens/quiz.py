import customtkinter as ctk
import time
from typing import Callable, Tuple, Optional


class QuizScreen:
    def __init__(self, master: ctk.CTkFrame,
                 on_submit_answer: Callable[[str], None],
                 on_skip: Callable):
        self.master = master
        self.on_submit_answer = on_submit_answer
        self.on_skip = on_skip

        self.progress_lbl: Optional[ctk.CTkLabel] = None
        self.timer_bar: Optional[ctk.CTkProgressBar] = None
        self.quiz_card: Optional[ctk.CTkFrame] = None
        self.label_main: Optional[ctk.CTkLabel] = None
        self.entry_ans: Optional[ctk.CTkEntry] = None
        self.btn_submit: Optional[ctk.CTkButton] = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        header_row = ctk.CTkFrame(self.master, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))
        self.progress_lbl = ctk.CTkLabel(header_row, text="", font=("Inter", 14, "bold"))
        self.progress_lbl.pack(side="left")

        # Timer Bar
        self.timer_bar = ctk.CTkProgressBar(self.master, height=12)
        self.timer_bar.pack(fill="x", pady=(0, 20))

        # --- THE CARD (Container) ---
        self.card_container = ctk.CTkFrame(self.master, height=300, fg_color="transparent")
        self.card_container.pack(fill="x", pady=20)
        self.card_container.pack_propagate(False)  # Keep height fixed during flip

        self.quiz_card = ctk.CTkFrame(self.card_container, corner_radius=20,
                                      fg_color=("#ffffff", "#1e293b"),
                                      border_width=2, border_color=("#e2e8f0", "#334155"))
        self.quiz_card.pack(expand=True, fill="both")

        # Central Label
        self.label_main = ctk.CTkLabel(self.quiz_card, text="", font=("Microsoft YaHei", 56, "bold"))
        self.label_main.place(relx=0.5, rely=0.5, anchor="center")

        # --- INPUT AREA ---
        self.entry_ans = ctk.CTkEntry(self.master, font=("Inter", 24), height=70,
                                      placeholder_text="Type answer here...", justify="center")
        self.entry_ans.pack(pady=10, fill="x")
        self.entry_ans.focus_set()
        self.entry_ans.bind("<Return>", lambda e: self._handle_submit())

        # Submit Button
        self.btn_submit = ctk.CTkButton(self.master, text="Check Answer",
                                        font=("Inter", 16, "bold"), height=50,
                                        command=self._handle_submit)
        self.btn_submit.pack(fill="x", pady=5)

        # Skip Button
        self.btn_skip = ctk.CTkButton(self.master, text="Skip Question",
                                      fg_color="#64748b", height=40,
                                      command=self.on_skip)
        self.btn_skip.pack(fill="x", pady=5)

    def _handle_submit(self) -> None:
        """Handle answer submission."""
        if self.entry_ans:
            user_input = self.entry_ans.get().strip()
            self.on_submit_answer(user_input)

    def update_progress(self, current: int, total: int) -> None:
        """Update progress display."""
        if self.progress_lbl:
            self.progress_lbl.configure(text=f"Question {current} of {total}")

    def update_timer(self, progress: float) -> None:
        """Update timer bar progress."""
        if self.timer_bar:
            self.timer_bar.set(progress)

    def show_question(self, question_text: str) -> None:
        """Display current question."""
        if self.label_main and self.quiz_card and self.entry_ans and self.btn_submit:
            # Reset card appearance
            self.quiz_card.configure(fg_color=("#ffffff", "#1e293b"))
            self.label_main.configure(text=question_text, text_color=("black", "white"))
            self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
            
            self.entry_ans.delete(0, 'end')
            self.entry_ans.focus_set()
            self.btn_submit.configure(text="Check Answer", fg_color="#3b82f6")

    def animate_feedback(self, text: str, color: str) -> None:
        """Animate card flip with feedback."""
        if not self.quiz_card or not self.label_main:
            return
            
        # Step 1: Shrink
        for w in range(100, 0, -10):
            self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=w/100, relheight=1)
            self.master.update_idletasks()
            time.sleep(0.01)

        # Update Content while 'invisible'
        self.label_main.configure(text=text, text_color="white")
        self.quiz_card.configure(fg_color=color)
        
        # Step 2: Expand
        for w in range(0, 105, 10):
            self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=w/100, relheight=1)
            self.master.update_idletasks()
            time.sleep(0.01)

    def get_input(self) -> str:
        """Get current input value."""
        return self.entry_ans.get().strip() if self.entry_ans else ""
