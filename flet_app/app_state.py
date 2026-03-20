from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    student_name: str = ""
    student_data: dict[str, Any] | None = None
    current_vocab: dict[str, str] = field(default_factory=dict)
    current_vocab_file: str = ""
    current_config: dict[str, Any] = field(default_factory=dict)
    session_history: list[dict[str, Any]] = field(default_factory=list)
    quiz_engine: Any = None
    current_view: str = "name_entry"
    last_quiz_data: dict[str, Any] | None = None
    app_resolution: tuple[int, int] = (1000, 700)
    quiz_mode: str = "standard"
    practice_parent_index: int | None = None
    pending_deleted_active_student: bool = False
    admin_mode: bool = False
    admin_entry_route: bool = False

    def snapshot(self, page) -> dict[str, Any]:
        engine = self.quiz_engine
        return {
            "view": self.current_view,
            "student_name": self.student_name,
            "current_vocab_file": self.current_vocab_file,
            "vocab_count": len(self.current_vocab),
            "session_history_count": len(self.session_history),
            "has_student_data": self.student_data is not None,
            "has_last_quiz_data": self.last_quiz_data is not None,
            "quiz_mode": self.quiz_mode,
            "practice_parent_index": self.practice_parent_index,
            "pending_deleted_active_student": self.pending_deleted_active_student,
            "admin_mode": self.admin_mode,
            "admin_entry_route": self.admin_entry_route,
            "theme_mode": str(page.theme_mode),
            "app_resolution": {
                "width": self.app_resolution[0],
                "height": self.app_resolution[1],
            },
            "window": {
                "width": page.window.width,
                "height": page.window.height,
            },
            "quiz_engine": {
                "present": engine is not None,
                "current_idx": engine.current_idx if engine else None,
                "question_count": len(engine.questions) if engine else 0,
                "score": engine.score if engine else None,
                "timer_running": engine.timer_running if engine else None,
                "word_time_limit": engine.word_time_limit if engine else None,
                "is_waiting_for_next": engine.is_waiting_for_next if engine else None,
            },
        }

    def reset_session(self) -> None:
        self.student_name = ""
        self.student_data = None
        self.current_vocab.clear()
        self.current_vocab_file = ""
        self.current_config.clear()
        self.session_history.clear()
        self.quiz_engine = None
        self.last_quiz_data = None
        self.current_view = "name_entry"
        self.quiz_mode = "standard"
        self.practice_parent_index = None
        self.pending_deleted_active_student = False
        self.admin_mode = False
        self.admin_entry_route = False
