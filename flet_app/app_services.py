from __future__ import annotations

from dataclasses import dataclass
import logging

from core.database import StudentDatabase
from core.file_parser import VocabFileParser
from spellchecker import SpellChecker


@dataclass(frozen=True)
class AppServices:
    db: StudentDatabase
    file_parser: VocabFileParser
    spell: SpellChecker


def build_services(logger: logging.Logger) -> AppServices:
    return AppServices(
        db=StudentDatabase(logger=logger),
        file_parser=VocabFileParser(logger=logger),
        spell=SpellChecker(language="en"),
    )
