import os
import json
from typing import Dict, Any, Optional


class StudentDatabase:
    def __init__(self, db_path: str = "student_records.json"):
        self.db_path = db_path
        self.database: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load or create the persistent JSON database."""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.database = json.load(f)
        else:
            self.database = {}

    def save(self) -> None:
        """Save all student records to the local file."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.database, f, indent=4)

    def get_student(self, name: str) -> Optional[Dict[str, Any]]:
        """Get student data by name."""
        return self.database.get(name)

    def update_student(self, name: str, data: Dict[str, Any]) -> None:
        """Update student data, creating the entry if it doesn't exist."""
        if name not in self.database:
            self.database[name] = {"sessions": [], "total_words_learned": 0}
        
        self.database[name].update(data)
        self.save()

    def add_session(self, name: str, session_data: Dict[str, Any]) -> None:
        """Add a new quiz session to a student's record."""
        if name not in self.database:
            self.database[name] = {"sessions": [], "total_words_learned": 0}
        
        self.database[name]["sessions"].append(session_data)
        self.database[name]["total_words_learned"] += session_data["score"]
        self.save()
