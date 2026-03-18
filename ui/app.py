import customtkinter as ctk
from tkinter import messagebox
import os
from spellchecker import SpellChecker
from typing import Dict, Any, Optional, List, Tuple

# Import core modules
from core.database import StudentDatabase
from core.file_parser import VocabFileParser
from core.quiz_engine import QuizEngine

# Import UI components
from .sidebar import Sidebar
from .screens.welcome import WelcomeScreen
from .screens.settings import SettingsScreen
from .screens.quiz_config import QuizConfigScreen
from .screens.quiz import QuizScreen
from .screens.results import ResultsScreen
from .screens.session_summary import SessionSummaryScreen
from .screens.personal_history import PersonalHistoryScreen


class VocabQuizApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Vocab Master Dashboard")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # --- Initialize Core Services ---
        self.db = StudentDatabase()
        self.file_parser = VocabFileParser()
        self.spell = SpellChecker()
        
        # --- Session State ---
        self.student_name: str = ""
        self.session_history: List[Dict[str, Any]] = []
        self.current_student_data: Optional[Dict[str, Any]] = None
        self.current_vocab: Dict[str, str] = {}
        self.quiz_engine: Optional[QuizEngine] = None
        self.timer_job: Optional[str] = None
        
        # --- Grid Layout Configuration ---
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # 2. Main Workspace
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)

        # Initialize sidebar
        self.sidebar = Sidebar(
            root=self.root,
            on_home_click=self.show_welcome_screen,
            on_settings_click=self.show_settings,
            on_toggle_appearance=self._toggle_appearance
        )

        self.show_welcome_screen()

    def _clear_main(self) -> None:
        """Clear main frame and stop any running timers."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self._stop_timer()

    def _toggle_appearance(self, is_dark: bool) -> None:
        """Toggle between light and dark mode."""
        ctk.set_appearance_mode("dark" if is_dark else "light")

    def _stop_timer(self) -> None:
        """Stop the quiz timer."""
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.quiz_engine:
            self.quiz_engine.timer_running = False

    def _run_timer_tick(self) -> None:
        """Run timer tick for quiz."""
        if not self.quiz_engine or not self.quiz_engine.timer_running:
            return
            
        if self.quiz_engine.timer_tick():
            # Time is up
            self._handle_answer_submit("")
            return
        
        # Update timer UI
        if hasattr(self, 'current_screen') and isinstance(self.current_screen, QuizScreen):
            self.current_screen.update_timer(self.quiz_engine.get_timer_progress())
        
        # Schedule next tick
        self.timer_job = self.root.after(50, self._run_timer_tick)

    def _update_sidebar_stats(self) -> None:
        """Update sidebar statistics."""
        if not self.session_history:
            self.sidebar.update_stats(0, 0)
            return

        total_correct = sum(q['score'] for q in self.session_history)
        total_attempted = sum(q['total'] for q in self.session_history)
        self.sidebar.update_stats(total_correct, total_attempted)

    # --- Screen Navigation ---

    def show_welcome_screen(self) -> None:
        """Show welcome screen."""
        self._clear_main()
        self._stop_timer()
        
        saved_files = self.file_parser.list_available_files()
        student_data = self.db.get_student(self.student_name) if self.student_name else None
        
        self.current_screen = WelcomeScreen(
            master=self.main_frame,
            student_name=self.student_name,
            saved_files=saved_files,
            on_start_click=self._handle_welcome_start,
            student_data=student_data
        )

    def show_settings(self) -> None:
        """Show settings screen."""
        self._clear_main()
        
        current_res = (self.root.winfo_width(), self.root.winfo_height())
        self.current_screen = SettingsScreen(
            master=self.main_frame,
            current_resolution=current_res,
            on_resolution_change=self._change_resolution,
            on_reset_session=self._full_reset,
            on_view_history=self.show_personal_history
        )

    def _change_resolution(self, new_res: Tuple[int, int]) -> None:
        """Change window resolution."""
        new_w, new_h = new_res
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w / 2) - (new_w / 2)
        y = (screen_h / 2) - (new_h / 2)
        self.root.geometry(f"{new_w}x{new_h}+{int(x)}+{int(y)}")

    def _full_reset(self) -> None:
        """Reset entire session."""
        self.session_history = []
        self.student_name = ""
        self.sidebar.update_student_name("")
        self._update_sidebar_stats()
        self.show_welcome_screen()

    def _handle_welcome_start(self, name: str, selected_file: str) -> None:
        """Handle start button click from welcome screen."""
        if not name:
            messagebox.showwarning("Name Required", "Please enter your name before proceeding.")
            return
        
        if not selected_file:
            messagebox.showwarning("No List", "Please select or import a word list.")
            return
            
        # Update student info
        self.student_name = name
        self.sidebar.update_student_name(name)
        self.current_student_data = self.db.get_student(name)
        
        # Load vocab list
        file_path = os.path.join(self.file_parser.save_dir, selected_file)
        self.current_vocab = self.file_parser.parse_file(file_path)
        
        if not self.current_vocab:
            messagebox.showerror("Error", "The selected file is empty or formatted incorrectly (use: word, definition).")
            return

        # Move to quiz configuration
        self.show_quiz_config()

    def show_quiz_config(self) -> None:
        """Show quiz configuration screen."""
        self._clear_main()
        
        # Get saved config if exists
        saved_config = {}
        if self.student_name and self.current_student_data:
            saved_config = self.current_student_data.get("last_config", {})
        
        self.current_screen = QuizConfigScreen(
            master=self.main_frame,
            total_available=len(self.current_vocab),
            on_start_quiz=self._handle_start_quiz,
            saved_config=saved_config
        )

    def _handle_start_quiz(self, question_count: int, time_limit: int, config: Dict[str, str]) -> None:
        """Handle quiz start from configuration screen."""
        # Save config to database
        if self.student_name:
            student_data = self.db.get_student(self.student_name) or {}
            student_data["last_config"] = config
            self.db.update_student(self.student_name, student_data)
            self.current_student_data = student_data
        
        # Initialize quiz engine
        self.quiz_engine = QuizEngine(self.current_vocab, self.spell)
        self.quiz_engine.start(question_count, time_limit)
        self.quiz_engine.timer_running = True
        
        # Show quiz screen
        self.show_quiz_ui()

    def show_quiz_ui(self) -> None:
        """Show main quiz screen."""
        self._clear_main()
        
        self.current_screen = QuizScreen(
            master=self.main_frame,
            on_submit_answer=self._handle_answer_submit,
            on_skip=self._handle_skip_question
        )
        
        # Bind Enter key
        self.root.bind("<Return>", lambda e: self._handle_answer_submit(self.current_screen.get_input()))
        
        # Start quiz
        self._show_next_question()
        self._run_timer_tick()

    def _show_next_question(self) -> None:
        """Show next question or finalize quiz."""
        if not self.quiz_engine:
            return
            
        if not self.quiz_engine.next_question():
            self._finalize_quiz()
            return
            
        chi, _ = self.quiz_engine.get_current_word()
        current, total = self.quiz_engine.get_progress()
        
        self.current_screen.update_progress(current, total)
        self.current_screen.show_question(chi)
        self.current_screen.update_timer(self.quiz_engine.get_timer_progress())

    def _handle_answer_submit(self, user_input: str) -> None:
        """Handle answer submission."""
        if not self.quiz_engine or self.quiz_engine.is_waiting_for_next:
            return
            
        result = self.quiz_engine.check_answer(user_input)
        
        # Show feedback
        feedback_color = "#16a34a" if result["is_correct"] else "#dc2626"
        if result["skipped"]:
            feedback_color = "#64748b"
            
        self.current_screen.animate_feedback(result["correct"], feedback_color)
        
        # Auto advance to next question
        self.root.after(1500, self._show_next_question)

    def _handle_skip_question(self) -> None:
        """Handle question skip."""
        if not self.quiz_engine or self.quiz_engine.is_waiting_for_next:
            return
            
        result = self.quiz_engine.check_answer("", skipped=True)
        
        # Show feedback
        self.current_screen.animate_feedback(result["correct"], "#64748b")
        
        # Auto advance to next question
        self.root.after(1500, self._show_next_question)

    def _finalize_quiz(self) -> None:
        """Finalize quiz and show results."""
        if not self.quiz_engine:
            return
            
        quiz_data = self.quiz_engine.finalize()
        
        # Save to database
        if self.student_name:
            self.db.add_session(self.student_name, quiz_data)
            self.current_student_data = self.db.get_student(self.student_name)
        
        # Add to session history
        old_quiz_data = {
            "score": quiz_data["score"],
            "total": quiz_data["total"],
            "log": list(quiz_data["results_log"]),
            "time": quiz_data["date"].split()[-1]
        }
        self.session_history.append(old_quiz_data)
        self._update_sidebar_stats()
        
        # Show results
        self.show_results(quiz_data)

    def show_results(self, quiz_data: Dict[str, Any]) -> None:
        """Show quiz results screen."""
        self._clear_main()
        self.root.unbind("<Return>")
        
        has_mistakes = len(quiz_data["mistakes"]) > 0
        self.current_screen = ResultsScreen(
            master=self.main_frame,
            student_name=self.student_name,
            score=quiz_data["score"],
            total=quiz_data["total"],
            results_log=quiz_data["results_log"],
            has_mistakes=has_mistakes,
            on_home_click=self.show_welcome_screen,
            on_practice_mistakes=self._practice_mistakes if has_mistakes else None
        )

    def _practice_mistakes(self) -> None:
        """Start quiz with mistakes only."""
        if not self.quiz_engine:
            return
            
        self.quiz_engine.practice_mistakes()
        self.quiz_engine.timer_running = True
        self.show_quiz_ui()

    def show_session_summary(self) -> None:
        """Show session summary screen."""
        self._clear_main()
        
        self.current_screen = SessionSummaryScreen(
            master=self.main_frame,
            student_name=self.student_name,
            session_history=self.session_history,
            on_home_click=self.show_welcome_screen
        )

    def show_personal_history(self) -> None:
        """Show personal history screen."""
        self._clear_main()
        
        if not self.student_name or not self.current_student_data:
            messagebox.showinfo("No Records", "No history found for the current student.")
            self.show_settings()
            return

        sessions = self.current_student_data.get("sessions", [])
        self.current_screen = PersonalHistoryScreen(
            master=self.main_frame,
            student_name=self.student_name,
            sessions=sessions,
            on_back_click=self.show_settings
        )
