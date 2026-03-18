import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable, List, Dict, Any


class SessionSummaryScreen:
    def __init__(self, master: ctk.CTkFrame,
                 student_name: str,
                 session_history: List[Dict[str, Any]],
                 on_home_click: Callable):
        self.master = master
        self.student_name = student_name
        self.session_history = session_history
        self.on_home_click = on_home_click

        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self.master, text="Session Dashboard", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 30))
        
        total_correct = sum(q['score'] for q in self.session_history)
        total_attempted = sum(q['total'] for q in self.session_history)
        acc = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        
        stats_frame = ctk.CTkFrame(self.master, height=100)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        # Grid inside stats frame
        ctk.CTkLabel(stats_frame, text=f"Total Accuracy\n{acc:.1f}%", font=("Inter", 16, "bold")).place(relx=0.2, rely=0.5, anchor="center")
        ctk.CTkLabel(stats_frame, text=f"Words Tested\n{total_attempted}", font=("Inter", 16, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(stats_frame, text=f"Quizzes\n{len(self.session_history)}", font=("Inter", 16, "bold")).place(relx=0.8, rely=0.5, anchor="center")

        ctk.CTkButton(self.master, text="📥 Download Complete Session Report (.txt)", height=50, command=self._save_report).pack(pady=20, fill="x")
        ctk.CTkButton(self.master, text="← Return to Menu", fg_color="transparent", command=self.on_home_click).pack()

    def _save_report(self) -> None:
        """Save session report to file."""
        report = f"STUDENT SESSION REPORT\nName: {self.student_name}\n"
        for i, q in enumerate(self.session_history):
            report += f"\nQUIZ #{i+1} [{q['time']}]\nScore: {q['score']}/{q['total']}\n"
            for item in q['log']:
                report += f"[{item['status']}] {item['chi']} -> {item['correct']}\n"
        
        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"{self.student_name}_Report.txt")
        if f:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(report)
            messagebox.showinfo("Success", "Report Saved")
