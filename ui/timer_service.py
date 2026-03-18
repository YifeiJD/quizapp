import tkinter as tk
from typing import Optional, Callable
from core.quiz_engine import QuizEngine


class TimerService:
    """Standalone timer service that manages quiz timer ticks and UI updates."""
    
    def __init__(self, root: tk.Tk, quiz_engine: QuizEngine, on_timer_update: Callable[[float], None], on_answer_submit: Callable[[str], None]):
        """
        Initialize timer service.

        Args:
            root: Tkinter root window
            quiz_engine: QuizEngine instance to track timer state
            on_timer_update: Callback to update timer UI (progress 0.0-1.0)
            on_answer_submit: Callback to submit answer when timer expires
        """
        self.root = root
        self.quiz_engine = quiz_engine
        self.on_timer_update = on_timer_update
        self.on_answer_submit = on_answer_submit
        self.timer_job: Optional[str] = None
        self._is_running: bool = False
    
    def start(self) -> None:
        """Start or resume the timer."""
        if not self._is_running:
            self._is_running = True
            self._run_tick()
    
    def stop(self) -> None:
        """Pause the timer."""
        self._is_running = False
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
    
    def reset(self) -> None:
        """Reset and stop the timer."""
        self.stop()
        self.timer_job = None
    
    def _run_tick(self) -> None:
        """Internal timer tick handler."""
        if not self._is_running or not self.quiz_engine.timer_running:
            return
             
        # Update timer state
        if self.quiz_engine.timer_tick():
            # Time is up, auto-submit empty answer to trigger timeout penalty
            self.stop()
            # Auto-submit for timeout
            if self.quiz_engine and not self.quiz_engine.is_waiting_for_next:
                self.on_answer_submit("", is_timeout=True)
             
        # Update UI
        progress = self.quiz_engine.get_timer_progress()
        self.on_timer_update(progress)
        
        # Schedule next tick if still running
        if self._is_running and self.quiz_engine.timer_running:
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
            self.timer_job = self.root.after(50, self._run_tick)
    
    def is_running(self) -> bool:
        """Check if timer is active."""
        return self._is_running