import random
import time
from typing import Dict, List, Tuple, Optional, Any
from spellchecker import SpellChecker


class QuizEngine:
    def __init__(self, vocab: Dict[str, str], spell_checker: SpellChecker):
        self.vocab = vocab
        self.spell = spell_checker
        
        # Quiz state
        self.questions: List[Tuple[str, str]] = []
        self.session_mistakes: List[Tuple[str, str]] = []
        self.results_log: List[Dict[str, Any]] = []
        self.word_time_limit: int = 10
        self.word_time_left_ms: int = 0
        self.timer_running: bool = False
        self.is_waiting_for_next: bool = False
        self.current_idx: int = 0
        self.score: int = 0

    def start(self, question_count: Optional[int] = None, time_limit: int = 10) -> None:
        """Start a new quiz with specified number of questions and time limit per word."""
        self.word_time_limit = time_limit
        self.current_idx = 0
        self.score = 0
        self.results_log = []
        self.session_mistakes = []
        self.is_waiting_for_next = False
        
        # Select questions
        vocab_items = list(self.vocab.items())
        if question_count and question_count <= len(vocab_items):
            self.questions = random.sample(vocab_items, question_count)
        else:
            self.questions = vocab_items
            random.shuffle(self.questions)

    def get_current_word(self) -> Tuple[str, str]:
        """Get the current question (Chinese definition, English word)."""
        if self.current_idx < len(self.questions):
            return self.questions[self.current_idx]
        return ("", "")

    def get_progress(self) -> Tuple[int, int]:
        """Get current progress (current question, total questions)."""
        return (self.current_idx + 1, len(self.questions))

    def check_answer(self, user_input: str, is_timeout: bool = False, skipped: bool = False) -> Dict[str, Any]:
        """Check user answer and return result."""
        if self.is_waiting_for_next or self.current_idx >= len(self.questions):
            return {"is_correct": False, "status": "invalid", "correct": ""}
        
        chi, correct = self.questions[self.current_idx]
        user_input = user_input.strip()
        self.is_waiting_for_next = True
        
        # Evaluation
        words = correct.lower().split()
        is_common = all(bool(self.spell.known([w])) for w in words)
        is_correct = (user_input.lower() == correct.lower()) if is_common else (user_input == correct)

        # Prepare result
        if skipped:
            status = "⏭️"
        elif is_correct:
            self.score += 1
            status = "✅"
        else:
            status = "❌"
            self.session_mistakes.append((chi, correct))

        # Logging
        result = {
            "chi": chi,
            "correct": correct,
            "user": user_input,
            "status": status,
            "is_correct": is_correct,
            "is_timeout": is_timeout,
            "skipped": skipped
        }
        self.results_log.append(result)
        
        return result

    def next_question(self) -> bool:
        """Move to next question, return False if quiz is complete."""
        self.current_idx += 1
        if self.current_idx >= len(self.questions):
            return False
        
        self.is_waiting_for_next = False
        self.word_time_left_ms = self.word_time_limit * 1000
        return True

    def finalize(self) -> Dict[str, Any]:
        """Finalize quiz and return session data."""
        accuracy = round((self.score / len(self.questions)) * 100, 1) if self.questions else 0
        
        return {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "score": self.score,
            "total": len(self.questions),
            "mistakes": self.session_mistakes,
            "accuracy": accuracy,
            "results_log": self.results_log
        }

    def practice_mistakes(self) -> None:
        """Reset quiz to practice only mistakes from previous session."""
        if not self.session_mistakes:
            return
        
        # Convert mistakes to vocab dict
        self.vocab = {chi: eng for chi, eng in self.session_mistakes}
        self.start(time_limit=self.word_time_limit)

    def timer_tick(self, ms_passed: int = 50) -> bool:
        """Update timer, return True if time is up for current question."""
        if not self.timer_running or self.is_waiting_for_next or self.word_time_limit <= 0:
            return False
        
        self.word_time_left_ms -= ms_passed
        return self.word_time_left_ms <= 0

    def get_timer_progress(self) -> float:
        """Get timer progress as a value between 0 and 1."""
        if self.word_time_limit <= 0:
            return 1.0
        return max(0, self.word_time_left_ms / (self.word_time_limit * 1000))
