import json
import logging
from pathlib import Path
from core.debug_report import emit_debug_report


ROOT_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT_DIR / "admin_settings.json"
DEFAULT_PASSWORD = "admin"


class AdminSettings:
    def __init__(self, logger: logging.Logger, settings_path: Path = SETTINGS_PATH):
        self.logger = logger
        self.settings_path = settings_path
        self._settings = self._load()

    def _load(self) -> dict:
        emit_debug_report(self.logger, "DEBUG-REPORT", "admin_settings_load_started", {"path": str(self.settings_path)})
        if self.settings_path.exists():
            with self.settings_path.open("r", encoding="utf-8") as f:
                settings = json.load(f)
                emit_debug_report(self.logger, "DEBUG-REPORT", "admin_settings_load_completed", {"path": str(self.settings_path)})
                return settings
        settings = {"password": DEFAULT_PASSWORD}
        self._save(settings)
        emit_debug_report(self.logger, "DEBUG-REPORT", "admin_settings_created", {"path": str(self.settings_path)})
        return settings

    def _save(self, settings: dict) -> None:
        emit_debug_report(self.logger, "DEBUG-REPORT", "admin_settings_save_started", {"path": str(self.settings_path)})
        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        emit_debug_report(self.logger, "DEBUG-REPORT", "admin_settings_save_completed", {"path": str(self.settings_path)})


    def verify_password(self, password: str) -> bool:
        return password == self._settings.get("password", DEFAULT_PASSWORD)

    def set_password(self, password: str) -> None:
        self._settings["password"] = password
        self._save(self._settings)
