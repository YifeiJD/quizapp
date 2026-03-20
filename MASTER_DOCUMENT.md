# Master Document

This document describes the function of all components of the Quiz App, their behavior, inputs, and outputs.

## Core Components

The `core` directory contains the business logic of the application, independent of the UI framework.

### `database.py`

This module manages the student records, storing them in a JSON file.

**Class `StudentDatabase`**

*   **`__init__(self, db_path: str = "student_records.json")`**
    *   **Description:** Initializes the database, loading existing records from the specified JSON file or creating a new file if it doesn't exist.
    *   **Input:** `db_path` (optional): The path to the JSON database file. Defaults to `"student_records.json"`.
    *   **Output:** None.

*   **`load(self) -> None`**
    *   **Description:** Loads the database from the JSON file.
    *   **Input:** None.
    *   **Output:** None.

*   **`save(self) -> None`**
    *   **Description:** Saves the current state of the database to the JSON file.
    *   **Input:** None.
    *   **Output:** None.

*   **`get_student(self, name: str) -> Optional[Dict[str, Any]]`**
    *   **Description:** Retrieves a student's data by name.
    *   **Input:** `name`: The name of the student.
    *   **Output:** A dictionary containing the student's data, or `None` if the student is not found.

*   **`get_all_students(self) -> Dict[str, Any]`**
    *   **Description:** Returns a shallow copy of the entire student database.
    *   **Input:** None.
    *   **Output:** A dictionary containing all student records.

*   **`update_student(self, name: str, data: Dict[str, Any]) -> None`**
    *   **Description:** Updates a student's data. If the student does not exist, a new entry is created.
    *   **Input:**
        *   `name`: The name of the student.
        *   `data`: A dictionary containing the data to update.
    *   **Output:** None.

*   **`add_session(self, name: str, session_data: Dict[str, Any]) -> None`**
    *   **Description:** Adds a new quiz session to a student's record.
    *   **Input:**
        *   `name`: The name of the student.
        *   `session_data`: A dictionary containing the session data.
    *   **Output:** None.

*   **`delete_student(self, name: str) -> bool`**
    *   **Description:** Deletes a student and all their associated records.
    *   **Input:** `name`: The name of the student.
    *   **Output:** `True` if the student was deleted successfully, `False` otherwise.

*   **`delete_session(self, name: str, session_index: int) -> bool`**
    *   **Description:** Deletes a specific session from a student's record.
    *   **Input:**
        *   `name`: The name of the student.
        *   `session_index`: The index of the session to delete.
    *   **Output:** `True` if the session was deleted successfully, `False` otherwise.

### `admin_settings.py`

This module manages the admin settings, such as the password for the admin section.

**Class `AdminSettings`**

*   **`__init__(self, settings_path: Path = SETTINGS_PATH)`**
    *   **Description:** Initializes the admin settings, loading them from a JSON file or creating a new file with a default password if it doesn't exist.
    *   **Input:** `settings_path` (optional): The path to the JSON settings file.
    *   **Output:** None.

*   **`verify_password(self, password: str) -> bool`**
    *   **Description:** Verifies if the given password matches the stored admin password.
    *   **Input:** `password`: The password to verify.
    *   **Output:** `True` if the password is correct, `False` otherwise.

*   **`set_password(self, password: str) -> None`**
    *   **Description:** Sets a new admin password.
    *   **Input:** `password`: The new password.
    *   **Output:** None.

### `debug_report.py`

This module provides functions for logging and generating debug reports.

*   **`configure_debug_logging(log_filename: str = "flet_app.log") -> Path`**
    *   **Description:** Configures logging to both the console and a log file.
    *   **Input:** `log_filename` (optional): The name of the log file.
    *   **Output:** The path to the log file.

*   **`emit_debug_report(logger: logging.Logger, prefix: str, event: str, details: Optional[dict[str, Any]] = None, state: Optional[dict[str, Any]] = None) -> None`**
    *   **Description:** Emits a debug report to the given logger.
    *   **Input:**
        *   `logger`: The logger to use.
        *   `prefix`: A prefix for the log message.
        *   `event`: The name of the event being logged.
        *   `details` (optional): A dictionary of details about the event.
        *   `state` (optional): A dictionary representing the state of the application at the time of the event.
    *   **Output:** None.

### `file_parser.py`

This module is responsible for parsing vocabulary files.

**Class `VocabFileParser`**

*   **`__init__(self, save_dir: str = DEFAULT_SAVE_DIR)`**
    *   **Description:** Initializes the file parser, setting the directory where vocabulary files are stored.
    *   **Input:** `save_dir` (optional): The path to the directory for saved vocabulary lists.
    *   **Output:** None.

*   **`parse_file(self, path: str) -> Dict[str, str]`**
    *   **Description:** Parses a vocabulary file (.txt or .docx) and returns a dictionary of definition-word pairs.
    *   **Input:** `path`: The path to the vocabulary file.
    *   **Output:** A dictionary where keys are definitions and values are words.

*   **`parse_file_or_raise_tk_error(self, path: str) -> Dict[str, str]`**
    *   **Description:** Parses a file and shows a Tkinter message box if an error occurs.
    *   **Input:** `path`: The path to the vocabulary file.
    *   **Output:** A dictionary of definition-word pairs.

*   **`import_file(self) -> Optional[str]`**
    *   **Description:** Opens a file dialog for the user to select a vocabulary file and copies it to the save directory.
    *   **Input:** None.
    *   **Output:** The path to the imported file, or `None` if the user cancels.

*   **`list_available_files(self) -> List[str]`**
    *   **Description:** Returns a list of available vocabulary files in the save directory.
    *   **Input:** None.
    *   **Output:** A list of filenames.

### `quiz_engine.py`

This module contains the main logic for the quiz.

**Class `QuizEngine`**

*   **`__init__(self, vocab: Dict[str, str], spell_checker: SpellChecker)`**
    *   **Description:** Initializes the quiz engine with a vocabulary and a spell checker.
    *   **Input:**
        *   `vocab`: A dictionary of definition-word pairs.
        *   `spell_checker`: An instance of `SpellChecker`.
    *   **Output:** None.

*   **`start(self, question_count: Optional[int] = None, time_limit: int = 10) -> None`**
    *   **Description:** Starts a new quiz session.
    *   **Input:**
        *   `question_count` (optional): The number of questions in the quiz.
        *   `time_limit` (optional): The time limit for each question in seconds.
    *   **Output:** None.

*   **`get_current_word(self) -> Tuple[str, str]`**
    *   **Description:** Returns the current question (definition and word).
    *   **Input:** None.
    *   **Output:** A tuple containing the definition and the correct word.

*   **`get_progress(self) -> Tuple[int, int]`**
    *   **Description:** Returns the current progress in the quiz.
    *   **Input:** None.
    *   **Output:** A tuple containing the current question number and the total number of questions.

*   **`check_answer(self, user_input: str, is_timeout: bool = False, skipped: bool = False) -> Dict[str, Any]`**
    *   **Description:** Checks the user's answer and returns the result.
    *   **Input:**
        *   `user_input`: The user's answer.
        *   `is_timeout` (optional): Whether the answer was submitted due to a timeout.
        *   `skipped` (optional): Whether the question was skipped.
    *   **Output:** A dictionary containing the result of the check.

*   **`next_question(self) -> bool`**
    *   **Description:** Moves to the next question.
    *   **Input:** None.
    *   **Output:** `True` if there are more questions, `False` if the quiz is complete.

*   **`finalize(self) -> Dict[str, Any]`**
    *   **Description:** Finalizes the quiz and returns the session data.
    *   **Input:** None.
    *   **Output:** A dictionary containing the session data.

*   **`practice_mistakes(self) -> None`**
    *   **Description:** Starts a new quiz with only the questions that were answered incorrectly in the previous session.
    *   **Input:** None.
    *   **Output:** None.

*   **`timer_tick(self, ms_passed: int = 50) -> bool`**
    *   **Description:** Updates the timer for the current question.
    *   **Input:** `ms_passed` (optional): The number of milliseconds that have passed since the last tick.
    *   **Output:** `True` if the time is up, `False` otherwise.

*   **`get_timer_progress(self) -> float`**
    *   **Description:** Returns the progress of the timer for the current question.
    *   **Input:** None.
    *   **Output:** A float between 0.0 and 1.0 representing the timer progress.

## Flet App

The `flet_app` directory contains the implementation of the user interface using the Flet framework.

### `main_flet.py`

This is the entry point for the Flet application. It initializes the application, manages the overall state, and handles navigation between different screens.

*   **`main(page: ft.Page)`**: The main function that sets up the application.
    *   **Description:** Initializes the Flet page, configures logging, creates instances of core services (`StudentDatabase`, `FileParser`, `AdminSettings`), and sets up the application state (`AppState`). It defines the navigation logic and the functions for displaying each screen.
    *   **Input:** `page`: The Flet `Page` object.
    *   **Output:** None.

### `ui_flet/layout.py`

This module defines the main layout of the Flet application.

**Class `AppLayout`**

*   **`__init__(self, page: ft.Page, on_nav_change: Callable, on_theme_toggle: Callable[[bool], None], surface_size: tuple[int, int])`**
    *   **Description:** Creates the main layout, which consists of a sidebar with navigation and a main content area.
    *   **Input:**
        *   `page`: The Flet `Page` object.
        *   `on_nav_change`: A callback function to handle navigation events.
        *   `on_theme_toggle`: A callback function to handle theme changes.
        *   `surface_size`: The initial size of the application surface.
    *   **Output:** None.

*   **`set_content(self, control: ft.Control, centered: bool = True) -> None`**: Sets the content of the main workspace.
*   **`set_student(self, name: str)`**: Updates the student name displayed in the sidebar.
*   **`update_stats(self, total_correct: int = 0, total_attempted: int = 0) -> None`**: Updates the session statistics in the sidebar.
*   **`set_nav_enabled(self, enabled: bool) -> None`**: Enables or disables the navigation rail.

### Flet Screens (`flet_app/ui_flet/screens/`)

Each screen is a function that returns a Flet control to be displayed in the main content area.

*   **`NameEntryScreen`**: The initial screen where the user enters their name.
*   **`WelcomeScreen`**: The dashboard screen, shown after the user enters their name. It allows the user to select a vocabulary list and start a quiz.
*   **`QuizConfigScreen`**: Allows the user to configure the number of questions and the time limit for the quiz.
*   **`QuizScreen`**: The main quiz interface where the user answers questions.
*   **`ResultsScreen`**: Displays the results of the quiz, including the score and a list of correct and incorrect answers.
*   **`SettingsScreen`**: Provides options to change the application's resolution, reset the session, and view personal history.
*   **`PersonalHistoryScreen`**: Shows a student's complete history of saved sessions and performance statistics.
*   **`SessionSummaryScreen`**: Displays a summary of the current session's performance.
*   **`AdminDatabaseScreen`**: A password-protected screen for administrators to manage student records and application settings.

## CustomTkinter App

The `customtk_app` directory contains the implementation of the user interface using the CustomTkinter framework.

### `main.py`

This is the entry point for the CustomTkinter application. It initializes the main window and the `VocabQuizApp` class.

### `ui/app.py`

This module contains the main application class for the CustomTkinter UI.

**Class `VocabQuizApp`**

*   **`__init__(self, root: ctk.CTk)`**: The constructor for the main application class.
    *   **Description:** Initializes the main application window, core services, session state, and the main layout. It sets up the sidebar and the main frame where screens are displayed.
    *   **Input:** `root`: The root CustomTkinter window.
    *   **Output:** None.

*   **Screen Navigation Methods (`show_*_screen`)**: The class contains several methods like `show_welcome_screen`, `show_settings`, `show_quiz_ui`, etc. These methods are responsible for clearing the main frame and displaying the appropriate screen.

### CustomTkinter Screens (`customtk_app/ui/screens/`)

Each screen is a class that inherits from `ctk.CTkFrame` and is displayed in the main frame of the `VocabQuizApp`.

*   **`WelcomeScreen`**: The initial screen for entering a name and selecting a vocabulary list.
*   **`SettingsScreen`**: Provides options to change the window resolution and reset the session.
*   **`QuizConfigScreen`**: Allows the user to configure the quiz settings.
*   **`QuizScreen`**: The main interface for taking the quiz.
*   **`ResultsScreen`**: Displays the results after a quiz is completed.
*   **`SessionSummaryScreen`**: Shows a summary of the current session.
*   **`PersonalHistoryScreen`**: Displays the user's saved quiz history.
