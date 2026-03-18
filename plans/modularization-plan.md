
# Quiz App Modularization Plan

## Current Problem
The `quiz_app.py` file is 674 lines long with a single `VocabQuizApp` class containing all functionality.

## Proposed Architecture

### Directory Structure
```
quizapp/
├── main.py                 # Entry point
├── core/
│   ├── __init__.py
│   ├── database.py         # Database management
│   ├── file_parser.py      # Vocabulary file parsing
│   └── quiz_engine.py      # Core quiz logic
└── ui/
    ├── __init__.py
    ├── app.py              # Main app class
    ├── sidebar.py          # Sidebar component
    └── screens/
        ├── __init__.py
        ├── welcome.py      # Welcome screen
        ├── settings.py     # Settings screen
        ├── quiz_config.py  # Quiz configuration screen
        ├── quiz.py         # Quiz UI
        ├── results.py      # Results screen
        ├── session_summary.py  # Session summary
        └── personal_history.py # Personal history
```

## Module Breakdown

### 1. core/database.py
**Responsibilities:**
- Load/save student records from JSON
- Handle student data persistence

**Classes/Functions:**
- `StudentDatabase` class
  - `__init__(db_path)`
  - `load()`
  - `save()`
  - `get_student(name)`
  - `update_student(name, data)`

**Easy to extend:** Add new methods like `export_to_csv()`, `get_statistics()`, etc.

### 2. core/file_parser.py
**Responsibilities:**
- Parse vocabulary files (.txt, .docx)
- Handle file imports

**Classes/Functions:**
- `VocabFileParser` class
  - `__init__(save_dir)`
  - `parse_file(path)`
  - `import_file(source_path)`
  - `list_available_files()`

**Easy to extend:** Add support for new file formats (.csv, .xlsx, etc.) by adding new `parse_*()` methods.

### 3. core/quiz_engine.py
**Responsibilities:**
- Manage quiz state
- Check answers
- Handle timer
- Track mistakes

**Classes/Functions:**
- `QuizEngine` class
  - `__init__(vocab, spell_checker)`
  - `start(question_count, time_limit)`
  - `check_answer(user_input, is_timeout=False, skipped=False)`
  - `next_question()`
  - `get_current_word()`
  - `get_progress()`
  - `finalize()`

**Easy to extend:** Add new quiz modes (multiple choice, matching, etc.) by adding new methods.

### 4. ui/
**Responsibilities:**
- All UI-related code
- Screen management
- Component reuse

**Easy to extend:** Add new screens by creating new files in `ui/screens/`.

## Benefits
- Better code organization
- Easier testing
- Reusable components
- Clear separation of concerns
- Easier to maintain and extend

## Extensibility Guide

### Where to Add New Features

| New Feature | Module to Add To |
|-------------|------------------|
| New quiz mode (multiple choice, matching) | `core/quiz_engine.py` |
| New file format support (.csv, .xlsx) | `core/file_parser.py` |
| New student data field (e.g., preferences) | `core/database.py` |
| New screen (e.g., progress charts) | `ui/screens/` |
| New sidebar button | `ui/sidebar.py` |
| New report format (PDF, Excel) | `core/database.py` or new `core/exporter.py` |

### Example: Adding Multiple Choice Quiz Mode

```python
# In core/quiz_engine.py
class QuizEngine:
    # ... existing methods ...
    
    def check_answer_multiple_choice(self, user_choice):
        """New method for multiple choice questions"""
        # Implementation here
        pass
```

### Example: Adding CSV Export

```python
# In core/database.py
class StudentDatabase:
    # ... existing methods ...
    
    def export_to_csv(self, student_name, output_path):
        """New method to export student data to CSV"""
        # Implementation here
        pass
```

## Next Steps
1. Create directory structure
2. Extract database module
3. Extract file parser module
4. Extract quiz engine module
5. Refactor UI into separate screens
6. Update main app to use new modules

