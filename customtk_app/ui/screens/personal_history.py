import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, List, Dict, Any, Tuple


class PersonalHistoryScreen:
    def __init__(self, master: ctk.CTkFrame,
                 student_name: str,
                 sessions: List[Dict[str, Any]],
                 on_back_click: Callable):
        self.master = master
        self.student_name = student_name
        self.sessions = sessions
        self.on_back_click = on_back_click

        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self.master, text=f"History: {self.student_name}", font=("Inter", 28, "bold")).pack(anchor="w")
        
        history_frame = ctk.CTkScrollableFrame(self.master, height=400)
        history_frame.pack(fill="both", expand=True, pady=20)

        for idx, session in enumerate(reversed(self.sessions)):
            color = "#1e293b" if idx % 2 == 0 else "transparent"
            row = ctk.CTkFrame(history_frame, fg_color=color)
            row.pack(fill="x", pady=2)
            
            lbl_text = f"📅 {session['date']}  |  🎯 Score: {session['score']}/{session['total']} ({session['accuracy']}%)"
            ctk.CTkLabel(row, text=lbl_text, font=("Inter", 13)).pack(side="left", padx=10, pady=5)
            
            # Show mistakes button
            if session['mistakes']:
                btn = ctk.CTkButton(row, text="View Mistakes", width=100, height=24,
                                     command=lambda m=session['mistakes']: self._show_mistake_popup(m))
                btn.pack(side="right", padx=10)

        ctk.CTkButton(self.master, text="Back to Settings", command=self.on_back_click).pack(pady=10)

    def _show_mistake_popup(self, mistakes: List[Tuple[str, str]]) -> None:
        """Show popup with mistake details."""
        popup = ctk.CTkToplevel(self.master.winfo_toplevel())
        popup.title("Mistake Review")
        popup.geometry("400x500")
        txt = ctk.CTkTextbox(popup, font=("Inter", 14))
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        
        content = "WORDS TO REVIEW:\n" + "-"*20 + "\n"
        for m in mistakes:
            content += f"❌ {m[0]} -> {m[1]}\n"
        txt.insert("0.0", content)
        txt.configure(state="disabled")
