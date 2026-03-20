import random
import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Any
from spellchecker import SpellChecker
from core.debug_report import emit_debug_report

class QuizEngine:
    def __init__(self, logger: logging.Logger, vocab: Dict[str, str], spell_checker: SpellChecker):
        self.logger = logger
        self.vocab = vocab
        self.spell = spell_checker
        
        # Quiz state
        self.questions: List[Tuple[str, str]] = []
        self.session_mistakes: List[Tuple[str, str]] = []
        self.results_log: List[Dict[str, Any]] = []
        self.word_time_limit: int = 10
        self._word_time_left_ms: int = 0
        self._time_lock = threading.Lock()  # Lock for thread-safe timer access
        self.timer_running: bool = False
        self.is_waiting_for_next: bool = False
        self.current_idx: int = 0
        self.score: int = 0
        self._report("engine_initialized", vocab_count=len(self.vocab))

    def _state_snapshot(self) -> Dict[str, Any]:
        return {
            "vocab_count": len(self.vocab),
            "question_count": len(self.questions),
            "mistake_count": len(self.session_mistakes),
            "results_count": len(self.results_log),
            "word_time_limit": self.word_time_limit,
            "word_time_left_ms": self.word_time_left_ms,
            "timer_running": self.timer_running,
            "is_waiting_for_next": self.is_waiting_for_next,
            "current_idx": self.current_idx,
            "score": self.score,
        }

    def _report(self, event: str, **details: Any) -> None:
        emit_debug_report(
            self.logger,
            "DEBUG-REPORT",
            event,
            details=details,
            state=self._state_snapshot(),
        )
    
    @property
    def word_time_left_ms(self) -> int:
        """Thread-safe getter for word_time_left_ms"""
        with self._time_lock:
            return self._word_time_left_ms
    
    @word_time_left_ms.setter
    def word_time_left_ms(self, value: int) -> None:
        """Thread-safe setter for word_time_left_ms"""
        with self._time_lock:
            self._word_time_left_ms = value

    def start(self, question_count: Optional[int] = None, time_limit: int = 10) -> None:
        """Start a new quiz with specified number of questions and time limit per word."""
        self.word_time_limit = time_limit
        self.word_time_left_ms = time_limit * 1000 if time_limit > 0 else 0
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
        self._report(
            "quiz_started",
            requested_question_count=question_count,
            actual_question_count=len(self.questions),
            time_limit=time_limit,
            shuffled_questions=[q[1] for q in self.questions]
        )

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
        self.logger.debug(f"[CHECK_ANSWER] Called with user_input='{user_input}', is_timeout={is_timeout}, skipped={skipped}")
        
        if self.is_waiting_for_next or self.current_idx >= len(self.questions):
            self.logger.warning("[CHECK_ANSWER] Invalid state - waiting_for_next or no more questions")
            self._report(
                "answer_rejected",
                user_input=user_input,
                is_timeout=is_timeout,
                skipped=skipped,
                reason="invalid_state",
            )
            return {"is_correct": False, "status": "invalid", "correct": ""}
        
        chi, correct = self.questions[self.current_idx]
        user_input = user_input.strip()
        self.is_waiting_for_next = True
        
        # Always do case-insensitive comparison first
        # This is more forgiving and matches user expectations
        is_correct = (user_input.lower() == correct.lower())
        
        # If case-insensitive fails, optionally check spell corrections
        # (but don't require them - user's answer should be accepted if matches case-insensitive)
        if not is_correct:
            self.logger.debug(f"[CHECK_ANSWER] Case-insensitive match failed: '{user_input.lower()}' != '{correct.lower()}'")
        else:
            self.logger.debug(f"[CHECK_ANSWER] Case-insensitive match succeeded")

        # Prepare result
        if skipped:
            status = "⏭️"
            self.session_mistakes.append((chi, correct))
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
        self.logger.debug(f"[CHECK_ANSWER] Final result: status={status}, is_correct={is_correct}")
        self._report(
            "answer_checked",
            user_input=user_input,
            is_timeout=is_timeout,
            skipped=skipped,
            result=result,
        )
        
        return result

    def next_question(self) -> bool:
        """Move to next question, return False if quiz is complete."""
        self.current_idx += 1
        if self.current_idx >= len(self.questions):
            self._report("quiz_completed")
            return False
        
        self.is_waiting_for_next = False
        if self.word_time_limit > 0:
            self.word_time_left_ms = self.word_time_limit * 1000
        else:
            self.word_time_left_ms = 0
        self._report("next_question", next_idx=self.current_idx)
        return True

    def finalize(self) -> Dict[str, Any]:
        """Finalize quiz and return session data."""
        accuracy = round((self.score / len(self.questions)) * 100, 1) if self.questions else 0
        session_data = {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "score": self.score,
            "total": len(self.questions),
            "mistakes": self.session_mistakes,
            "accuracy": accuracy,
            "results_log": self.results_log
        }
        self._report("quiz_finalized", accuracy=accuracy, total=len(self.questions))
        return session_data

    def practice_mistakes(self) -> None:
        """Reset quiz to practice only mistakes from previous session."""
        if not self.session_mistakes:
            self._report("practice_mistakes_skipped", reason="no_mistakes")
            return
        
        # Convert mistakes to vocab dict
        self.vocab = {chi: eng for chi, eng in self.session_mistakes}
        self._report("practice_mistakes_started", mistake_count=len(self.session_mistakes))
        self.start(time_limit=self.word_time_limit)

    def timer_tick(self, ms_passed: int = 50) -> bool:
        """Update timer, return True if time is up for current question."""
        if not self.timer_running or self.is_waiting_for_next or self.word_time_limit <= 0:
            return False
        
        with self._time_lock:
            self._word_time_left_ms -= ms_passed
            time_up = self._word_time_left_ms <= 0
            remaining = self._word_time_left_ms
        if time_up:
            self._report("timer_expired", ms_passed=ms_passed, remaining_ms=remaining)
        
        return time_up

    def get_timer_progress(self) -> float:
        """Get timer progress as a value between 0 and 1."""
        if self.word_time_limit <= 0:
            return 1.0  # Full progress for infinite timer
        with self._time_lock:
            progress = self._word_time_left_ms / (self.word_time_limit * 1000)
        return max(0.0, min(1.0, progress))
