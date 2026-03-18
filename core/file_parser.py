import os
import shutil
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional

try:
    from docx import Document
except ImportError:
    Document = None


class VocabFileParser:
    def __init__(self, save_dir: str = "saved_lists"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def parse_file(self, path: str) -> Dict[str, str]:
        """Parse vocabulary file (.txt or .docx) and return dictionary of definition -> word."""
        vocab = {}
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
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read file: {e}")
        return vocab

    def import_file(self) -> Optional[str]:
        """Open file dialog to import a vocabulary file, copy it to save directory."""
        path = filedialog.askopenfilename(filetypes=[("Text/Word", "*.txt *.docx")])
        if path:
            dest_path = os.path.join(self.save_dir, os.path.basename(path))
            shutil.copy(path, dest_path)
            return dest_path
        return None

    def list_available_files(self) -> List[str]:
        """List all available vocabulary files in the save directory."""
        return [f for f in os.listdir(self.save_dir) if f.endswith(('.txt', '.docx'))]
