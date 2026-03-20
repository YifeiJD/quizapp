import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT_DIR / "admin_settings.json"
DEFAULT_PASSWORD = "admin"


class AdminSettings:
    def __init__(self, settings_path: Path = SETTINGS_PATH):
        self.settings_path = settings_path
        self._settings = self._load()

    def _load(self) -> dict:
        if self.settings_path.exists():
            with self.settings_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        settings = {"password": DEFAULT_PASSWORD}
        self._save(settings)
        return settings

    def _save(self, settings: dict) -> None:
        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def verify_password(self, password: str) -> bool:
        return password == self._settings.get("password", DEFAULT_PASSWORD)

    def set_password(self, password: str) -> None:
        self._settings["password"] = password
        self._save(self._settings)
