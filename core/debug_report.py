import json
import logging
from pathlib import Path
from typing import Any, Optional


def configure_debug_logging(log_filename: str = "flet_app.log") -> Path:
    """Configure readable app logging for terminal monitoring and file capture."""
    log_dir = Path(__file__).resolve().parents[1] / "debug_reports"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / log_filename

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    for noisy_logger in ("flet", "flet_core", "flet_desktop", "asyncio"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    return log_path


def emit_debug_report(
    logger: logging.Logger,
    prefix: str,
    event: str,
    details: Optional[dict[str, Any]] = None,
    state: Optional[dict[str, Any]] = None,
) -> None:
    payload: dict[str, Any] = {"event": event}
    if details is not None:
        payload["details"] = details
    if state is not None:
        payload["state"] = state
    logger.info("[%s]\n%s", prefix, json.dumps(payload, ensure_ascii=False, indent=2, default=str))
