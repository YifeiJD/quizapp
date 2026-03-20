from __future__ import annotations

from typing import Any


def build_session_report(student_name: str, session_history: list[dict[str, Any]]) -> str:
    report = f"STUDENT SESSION REPORT\nName: {student_name}\n"
    for index, quiz in enumerate(session_history, start=1):
        report += f"\nQUIZ #{index} [{quiz.get('date', 'N/A')}]\n"
        report += f"Score: {quiz.get('score', 0)}/{quiz.get('total', 0)}\n"
        
        # Robustly handle different log key names
        log_items = quiz.get("results_log", quiz.get("log", []))
        for item in log_items:
            report += f"[{item.get('status', '?')}] {item.get('chi', 'N/A')} -> {item.get('correct', 'N/A')}\n"
    return report


def session_totals(session_history: list[dict[str, Any]]) -> tuple[int, int]:
    total_correct = sum(quiz.get("score", 0) for quiz in session_history)
    total_attempted = sum(quiz.get("total", 0) for quiz in session_history)
    return total_correct, total_attempted
