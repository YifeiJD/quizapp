import os
import logging
from core.quiz_engine import QuizEngine
from flet_app.ui_flet.utils import show_message

class QuizController:
    def __init__(self, page, services, state, navigator, logger):
        self.page = page
        self.services = services
        self.state = state
        self.navigator = navigator
        self.logger = logger

    def start_quiz_setup(self, ignored_name, filename):
        if self.state.admin_mode:
            show_message(self.page, "Quiz is paused in Admin Mode. Log out to continue.", "errorContainer")
            return
        
        self.state.current_vocab_file = filename
        self.navigator.debug_report("start_quiz_setup", filename=filename)
        
        vocab_path = os.path.join(self.services.file_parser.save_dir, filename)
        vocab = self.services.file_parser.parse_file(vocab_path)
        
        if not vocab:
            show_message(self.page, self.services.file_parser.last_error or "That vocabulary file is empty or could not be parsed.")
            return
            
        self.state.current_vocab = vocab
        self.navigator.show_quiz_config()

    def start_quiz(self, question_count, time_limit, config):
        if not self.state.current_vocab:
            show_message(self.page, "Load a vocabulary list before starting a quiz.")
            return
            
        self.state.quiz_mode = "standard"
        self.state.practice_parent_index = None
        self.state.current_config = config
        self.navigator.debug_report(
            "start_quiz",
            question_count=question_count,
            time_limit=time_limit,
            config=config,
        )
        
        if self.state.student_name:
            student_data = self.state.student_data or {"sessions": [], "total_words_learned": 0}
            student_data["last_config"] = config
            self.state.student_data = student_data
        
        engine = QuizEngine(self.logger, self.state.current_vocab, self.services.spell)
        engine.start(question_count=question_count, time_limit=time_limit)
        engine.timer_running = True
        self.state.quiz_engine = engine
        
        self.navigator.show_quiz()

    def finish_quiz(self):
        engine = self.state.quiz_engine
        if not engine:
            return
        
        quiz_data = engine.finalize()
        self.state.last_quiz_data = quiz_data
        self.navigator.debug_report(
            "finish_quiz",
            score=quiz_data["score"],
            total=quiz_data["total"],
            mistakes=len(quiz_data.get("mistakes", [])),
            quiz_mode=self.state.quiz_mode,
        )

        if self.state.quiz_mode == "practice" and self.state.practice_parent_index is not None:
            practice_entry = {
                "date": quiz_data["date"],
                "score": quiz_data["score"],
                "total": quiz_data["total"],
                "accuracy": (quiz_data["score"] / quiz_data["total"] * 100) if quiz_data["total"] > 0 else 0,
            }
            if 0 <= self.state.practice_parent_index < len(self.state.session_history):
                parent_session = self.state.session_history[self.state.practice_parent_index]
                parent_session.setdefault("practice_attempts", []).append(practice_entry)
                parent_session.setdefault("results_log", parent_session.get("log", []))
                parent_session["results_log"].extend(list(quiz_data["results_log"]))
                parent_session["log"] = list(parent_session["results_log"])
            if self.state.student_name and self.state.student_data:
                student_sessions = self.state.student_data.get("sessions", [])
                if 0 <= self.state.practice_parent_index < len(student_sessions):
                    student_parent = student_sessions[self.state.practice_parent_index]
                    student_parent.setdefault("practice_attempts", []).append(practice_entry)
                    student_parent.setdefault("results_log", [])
                    student_parent["results_log"].extend(list(quiz_data["results_log"]))
                    self.services.db.update_student(self.state.student_name, self.state.student_data)
        else:
            if self.state.student_name:
                if self.state.student_data:
                    self.services.db.update_student(self.state.student_name, self.state.student_data)
                self.services.db.add_session(self.state.student_name, quiz_data)
                self.state.student_data = self.services.db.get_student(self.state.student_name)

            session_entry = {
                "score": quiz_data["score"],
                "total": quiz_data["total"],
                "date": quiz_data["date"],
                "log": list(quiz_data["results_log"]),
                "results_log": list(quiz_data["results_log"]),
                "mistakes": quiz_data.get("mistakes", []),
                "accuracy": (quiz_data["score"] / quiz_data["total"] * 100) if quiz_data["total"] > 0 else 0,
                "practice_attempts": [],
            }
            self.state.session_history.append(session_entry)

        self.state.quiz_mode = "standard"
        self.state.practice_parent_index = None
        self.navigator.update_sidebar_stats()
        
        self.navigator.show_results(quiz_data["score"], quiz_data["total"])
