import os
import shutil
import logging
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional
from core.debug_report import emit_debug_report

try:
    from docx import Document
except ImportError:
    Document = None


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAVE_DIR = os.path.join(ROOT_DIR, "saved_lists")


class VocabFileParser:
    def __init__(self, logger: logging.Logger, save_dir: str = DEFAULT_SAVE_DIR):
        self.logger = logger
        self.save_dir = os.path.abspath(save_dir)
        self.last_error: Optional[str] = None
        os.makedirs(self.save_dir, exist_ok=True)

    def parse_file(self, path: str) -> Dict[str, str]:
        """Parse vocabulary file (.txt or .docx) and return dictionary of definition -> word."""
        self.last_error = None
        vocab = {}
        emit_debug_report(
            self.logger,
            "DEBUG-REPORT",
            "parse_started",
            details={"path": path, "save_dir": self.save_dir},
        )
        try:
            if path.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ',' in line:
                            word, defn = line.strip().split(',', 1)
                            vocab[defn.strip()] = word.strip()
            elif path.endswith('.docx') and Document:
                doc = Document(path)
                for para in doc.paragraphs:
                    if ',' in para.text:
                            word, defn = para.text.strip().split(',', 1)
                            vocab[defn.strip()] = word.strip()
            elif path.endswith('.docx') and not Document:
                self.last_error = "DOCX support is unavailable because python-docx is not installed."
            else:
                self.last_error = "Unsupported file type. Use .txt or .docx vocabulary lists."
        except Exception as e:
            self.last_error = f"Could not read file: {e}"
        emit_debug_report(
            self.logger,
            "DEBUG-REPORT",
            "parse_completed",
            details={
                "path": path,
                "vocab_count": len(vocab),
                "error": self.last_error,
            },
        )
        return vocab

    def parse_file_or_raise_tk_error(self, path: str) -> Dict[str, str]:
        """Parse a file and show a Tk message box if a read error occurs."""
        vocab = self.parse_file(path)
        if self.last_error:
            messagebox.showerror("File Error", self.last_error)
        return vocab

    def import_file(self) -> Optional[str]:
        """Open file dialog to import a vocabulary file, copy it to save directory."""
        path = filedialog.askopenfilename(filetypes=[("Text/Word", "*.txt *.docx")])
        if path:
            dest_path = os.path.join(self.save_dir, os.path.basename(path))
            shutil.copy(path, dest_path)
            emit_debug_report(
                self.logger,
                "DEBUG-REPORT",
                "file_imported",
                details={"source": path, "destination": dest_path},
            )
            return dest_path
        emit_debug_report(self.logger, "DEBUG-REPORT", "file_import_cancelled")
        return None

    def list_available_files(self) -> List[str]:
        """List all available vocabulary files in the save directory."""
        files = [f for f in os.listdir(self.save_dir) if f.endswith(('.txt', '.docx'))]
        emit_debug_report(
            self.logger,
            "DEBUG-REPORT",
            "files_listed",
            details={"count": len(files), "files": files},
        )
        return files
