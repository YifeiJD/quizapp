from __future__ import annotations

from dataclasses import dataclass

from core.database import StudentDatabase
from core.file_parser import VocabFileParser
from spellchecker import SpellChecker


@dataclass(frozen=True)
class AppServices:
    db: StudentDatabase
    file_parser: VocabFileParser
    spell: SpellChecker


def build_services() -> AppServices:
    return AppServices(
        db=StudentDatabase(),
        file_parser=VocabFileParser(),
        spell=SpellChecker(language="en"),
    )
