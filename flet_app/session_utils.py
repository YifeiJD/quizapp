from __future__ import annotations

from typing import Any


def build_session_report(student_name: str, session_history: list[dict[str, Any]]) -> str:
    report = f"STUDENT SESSION REPORT\nName: {student_name}\n"
    for index, quiz in enumerate(session_history, start=1):
        report += f"\nQUIZ #{index} [{quiz['date']}]\n"
        report += f"Score: {quiz['score']}/{quiz['total']}\n"
        for item in quiz["log"]:
            report += f"[{item['status']}] {item['chi']} -> {item['correct']}\n"
    return report


def session_totals(session_history: list[dict[str, Any]]) -> tuple[int, int]:
    total_correct = sum(quiz.get("score", 0) for quiz in session_history)
    total_attempted = sum(quiz.get("total", 0) for quiz in session_history)
    return total_correct, total_attempted
