import customtkinter as ctk
from typing import Callable, List, Dict, Any, Optional


class ResultsScreen:
    def __init__(self, master: ctk.CTkFrame,
                 student_name: str,
                 score: int,
                 total: int,
                 results_log: List[Dict[str, Any]],
                 has_mistakes: bool,
                 on_home_click: Callable,
                 on_practice_mistakes: Optional[Callable] = None):
        self.master = master
        self.student_name = student_name
        self.score = score
        self.total = total
        self.results_log = results_log
        self.has_mistakes = has_mistakes
        self.on_home_click = on_home_click
        self.on_practice_mistakes = on_practice_mistakes

        self._build_ui()

    def _build_ui(self) -> None:
        # Round Header
        ctk.CTkLabel(self.master, text="Round Summary", font=("Inter", 32, "bold")).pack(anchor="w")
        
        acc = (self.score / self.total * 100) if self.total else 0
        stats_text = f"Student: {self.student_name}  |  Score: {self.score}/{self.total}  |  Accuracy: {acc:.1f}%"
        ctk.CTkLabel(self.master, text=stats_text, font=("Inter", 16), text_color="#3b82f6").pack(anchor="w", pady=(5, 20))

        # Results List (Scrollable)
        ctk.CTkLabel(self.master, text="Detailed Word Report:", font=("Inter", 14, "bold")).pack(anchor="w")
        txt_box = ctk.CTkTextbox(self.master, fg_color=("#f1f5f9", "#0f172a"), font=("Inter", 13), corner_radius=10)
        
        for r in self.results_log:
            txt_box.insert("end", f"{r['status']} {r['chi']} -> {r['correct']} (You typed: '{r['user']}')\n")
        
        txt_box.configure(state="disabled")
        txt_box.pack(fill="both", expand=True, pady=(10, 20))

        # Action Buttons
        btn_row = ctk.CTkFrame(self.master, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", pady=10)
        
        ctk.CTkButton(btn_row, text="🏠 Return to Home", fg_color="#64748b",
                      command=self.on_home_click, height=50).pack(side="right", expand=True, padx=5)

        if self.has_mistakes and self.on_practice_mistakes:
            ctk.CTkButton(btn_row, text="🔁 Practice Mistakes Only", fg_color="#16a34a",
                          command=self.on_practice_mistakes, height=50).pack(side="left", expand=True, padx=5)
