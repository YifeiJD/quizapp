import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import time
import random
import json
from spellchecker import SpellChecker

try:
    from docx import Document
except ImportError:
    Document = None

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class VocabQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocab Master Dashboard")
        self.root.geometry("1000x700") # Wider for Desktop
        self.root.minsize(900, 600)
        
        # --- Session State ---
        self.save_dir = "saved_lists"
        os.makedirs(self.save_dir, exist_ok=True)
        self.spell = SpellChecker()
        self.student_name = ""
        self.session_history = []
        self.db_path = "student_records.json"
        self._load_database()
        self.current_student_data = None
        
        # --- Quiz State ---
        self.vocab = {}
        self.questions = []
        self.session_mistakes = []
        self.results_log = []
        self.word_time_limit = 10
        self.word_time_left_ms = 0
        self.timer_job = None
        self.timer_running = False
        self.is_waiting_for_next = False
        self.current_idx = 0
        self.score = 0

        # --- Grid Layout Configuration ---
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Persistent)
        self.sidebar_frame = ctk.CTkFrame(self.root, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1) # Push bottom items down

        # 2. Main Workspace
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)

        self._init_sidebar()
        self.show_welcome_screen()

    def _load_database(self):
        """Load or create the persistent JSON database."""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.database = json.load(f)
        else:
            self.database = {}

    def _save_database(self):
        """Save all student records to the local file."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.database, f, indent=4)

    def _init_sidebar(self):
        """Builds the persistent left-hand navigation."""
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        logo = ctk.CTkLabel(self.sidebar_frame, text="VOCAB\nMASTER", font=("Inter", 24, "bold"), text_color="#3b82f6")
        logo.pack(pady=(30, 40))

        # Identity Section
        self.name_display = ctk.CTkLabel(self.sidebar_frame, text="No Student Active", font=("Inter", 12, "italic"), text_color="gray")
        self.name_display.pack(pady=10)

        # Stats Section
        self.stats_label = ctk.CTkLabel(self.sidebar_frame, text="Session Stats\n--", font=("Inter", 13), justify="center")
        self.stats_label.pack(pady=20)

        # Navigation Buttons
        self.btn_home = ctk.CTkButton(self.sidebar_frame, text="🏠 Home", fg_color="transparent", 
                                       text_color=("black", "white"), anchor="w", command=self.show_welcome_screen)
        self.btn_home.pack(pady=5, padx=20, fill="x")

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙️ Settings", fg_color="transparent", 
                                           text_color=("black", "white"), anchor="w", command=self.show_settings)
        self.btn_settings.pack(pady=5, padx=20, fill="x")

        # Bottom Sidebar Items
        self.appearance_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", command=self._toggle_appearance)
        if ctk.get_appearance_mode() == "Dark": self.appearance_switch.select()
        self.appearance_switch.pack(side="bottom", pady=20)

    # --- UI LOGIC ---

    def _clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.stop_timer()

    def _toggle_appearance(self):
        ctk.set_appearance_mode("dark" if self.appearance_switch.get() == 1 else "light")

    # --- SCREENS ---

    def show_welcome_screen(self):
        """The Main Dashboard. Handles both new login and returning users."""
        self.stop_timer()
        self.is_waiting_for_next = False
        self._clear_main()
        
        header_text = "Study Dashboard" if self.student_name else "Welcome to Vocab Master"
        header = ctk.CTkLabel(self.main_frame, text=header_text, font=("Inter", 32, "bold"))
        header.pack(anchor="w", pady=(0, 10))
        
        # If student is logged in, show a greeting
        if self.student_name:
            greet = f"Ready for another round, {self.student_name}?"
            ctk.CTkLabel(self.main_frame, text=greet, font=("Inter", 18), text_color="#3b82f6").pack(anchor="w", pady=(0, 30))
        else:
            ctk.CTkLabel(self.main_frame, text="Please identify yourself to begin.", font=("Inter", 16), text_color="gray").pack(anchor="w", pady=(0, 40))

        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        form_frame.pack(fill="x")

        # Identity Section
        if not self.student_name:
            ctk.CTkLabel(form_frame, text="Your Name", font=("Inter", 13, "bold")).pack(anchor="w")
            self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="e.g. Yifei Zhang", height=45)
            self.entry_name.pack(pady=(5, 20), fill="x")
        
        # List Selection (Always visible)
        ctk.CTkLabel(form_frame, text="Select Vocabulary List", font=("Inter", 13, "bold")).pack(anchor="w")
        self.saved_files = [f for f in os.listdir(self.save_dir) if f.endswith(('.txt', '.docx'))]
        self.combo_lists = ctk.CTkComboBox(form_frame, values=self.saved_files, height=45)
        if self.saved_files: self.combo_lists.set(self.saved_files[0])
        self.combo_lists.pack(pady=(5, 20), fill="x")

        # Start Button
        ctk.CTkButton(form_frame, text="Configure Quiz →", command=self.go_to_step_2,
                      height=50, font=("Inter", 14, "bold")).pack(fill="x", pady=20)
        
        # Mini-Stats (If user exists)
        if self.student_name and self.student_name in self.database:
            total = self.database[self.student_name]["total_words_learned"]
            ctk.CTkLabel(self.main_frame, text=f"Cumulative Words Learned: {total}", font=("Inter", 12, "italic")).pack(pady=10)

    def show_settings(self):
        self._clear_main()
        ctk.CTkLabel(self.main_frame, text="Settings & Records", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 20))

        # Personal History Button
        ctk.CTkButton(self.main_frame, text="📜 View My Personal History",
                      fg_color="#3b82f6", height=45,
                      command=self.show_personal_history).pack(fill="x", pady=10)

        ctk.CTkLabel(self.main_frame, text="Window Resolution", font=("Inter", 16, "bold")).pack(anchor="w", pady=(20, 10))
        ctk.CTkLabel(self.main_frame, text="Choose a layout that fits your screen best.", font=("Inter", 13), text_color="gray").pack(anchor="w", pady=(0, 15))

        self.res_options = {
            "Standard (1024 x 720)": (1024, 720),
            "Compact (960 x 640)": (960, 640),
            "Wide HD (1280 x 800)": (1280, 800),
            "Large (1152 x 864)": (1152, 864)
        }

        self.res_dropdown = ctk.CTkComboBox(self.main_frame, values=list(self.res_options.keys()), width=300, height=40)
        current_res = f"{self.root.winfo_width()} x {self.root.winfo_height()}"
        self.res_dropdown.set("Standard (1024 x 720)")
        self.res_dropdown.pack(anchor="w", pady=10)

        ctk.CTkButton(self.main_frame, text="Apply Resolution", command=self._change_resolution, width=200, height=40).pack(anchor="w", pady=20)

        ctk.CTkLabel(self.main_frame, text="Session Management", font=("Inter", 16, "bold")).pack(anchor="w", pady=(30, 10))
        ctk.CTkButton(self.main_frame, text="Reset Entire Session", fg_color="#dc2626", hover_color="#b91c1c",
                      command=self._full_reset, width=200).pack(anchor="w")

    def _change_resolution(self):
        choice = self.res_dropdown.get()
        new_w, new_h = self.res_options[choice]

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w / 2) - (new_w / 2)
        y = (screen_h / 2) - (new_h / 2)

        self.root.geometry(f"{new_w}x{new_h}+{int(x)}+{int(y)}")
        messagebox.showinfo("Success", f"Resolution updated to {choice}")

    def _full_reset(self):
        if messagebox.askyesno("Confirm Reset", "This will wipe all session history and mistakes. Continue?"):
            self.session_history = []
            self.student_name = ""
            self._update_sidebar_stats()
            self.show_welcome_screen()

    def go_to_step_2(self):
        # 1. Capture the name if it's the first time
        if not self.student_name:
            self.student_name = self.entry_name.get().strip()
        
        if not self.student_name:
            messagebox.showwarning("Name Required", "Please enter your name before proceeding.")
            return
            
        # 2. Update the sidebar now that we have a name
        self.name_display.configure(text=f"Student: {self.student_name}", font=("Inter", 14, "bold"), text_color="#3b82f6")
        
        # 3. Load the vocab list
        list_file = self.combo_lists.get()
        if not list_file:
            messagebox.showwarning("No List", "Please select or import a word list.")
            return
            
        self.vocab = self._parse_file(os.path.join(self.save_dir, list_file))
        
        if not self.vocab:
            messagebox.showerror("Error", "The selected file is empty or formatted incorrectly (use: word, definition).")
            return

        # 4. Move to settings
        self.show_step_2()

    def show_step_2(self):
        self._clear_main()
        ctk.CTkLabel(self.main_frame, text="Quiz Configuration", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 40))

        # Retrieve saved settings if they exist
        config = self.database.get(self.student_name, {}).get("last_config", {})

        settings_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        settings_row.pack(fill="x")

        # --- Timer Column ---
        timer_col = ctk.CTkFrame(settings_row, fg_color="transparent")
        timer_col.pack(side="left", expand=True, fill="both", padx=(0, 20))
        
        ctk.CTkLabel(timer_col, text="Time Limit per Word", font=("Inter", 14, "bold")).pack(anchor="w")
        self.seg_timer = ctk.CTkSegmentedButton(timer_col, values=["5s", "10s", "15s", "∞", "Custom"],
                                                command=self._timer_choice_handler, height=40)
        
        # Set saved timer or default to 10s
        saved_timer = config.get("timer_choice", "10s")
        self.seg_timer.set(saved_timer)
        self.seg_timer.pack(pady=10, fill="x")

        self.custom_timer_entry = ctk.CTkEntry(timer_col, placeholder_text="Seconds...", height=40)
        if saved_timer == "Custom":
            self.custom_timer_entry.insert(0, config.get("custom_time", ""))
            self.custom_timer_entry.pack(pady=5, fill="x")

        # --- Word Count Column ---
        count_col = ctk.CTkFrame(settings_row, fg_color="transparent")
        count_col.pack(side="left", expand=True, fill="both", padx=(20, 0))
        
        ctk.CTkLabel(count_col, text="Word Count", font=("Inter", 14, "bold")).pack(anchor="w")
        self.entry_count = ctk.CTkEntry(count_col, height=40, font=("Inter", 16))
        
        # Set saved word count or default to total list size
        saved_count = config.get("word_count", str(len(self.vocab)))
        self.entry_count.insert(0, saved_count)
        self.entry_count.pack(pady=10, fill="x")

        ctk.CTkButton(self.main_frame, text="Begin Quiz Session", font=("Inter", 16, "bold"),
                      height=60, command=self.validate_and_start).pack(side="bottom", fill="x", pady=20)

    def show_quiz_ui(self):
        self._clear_main()
        
        # Header
        header_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))
        self.progress_lbl = ctk.CTkLabel(header_row, text="", font=("Inter", 14, "bold"))
        self.progress_lbl.pack(side="left")

        # Timer Bar
        self.timer_bar = ctk.CTkProgressBar(self.main_frame, height=12)
        self.timer_bar.pack(fill="x", pady=(0, 20))

        # --- THE CARD (Container) ---
        self.card_container = ctk.CTkFrame(self.main_frame, height=300, fg_color="transparent")
        self.card_container.pack(fill="x", pady=20)
        self.card_container.pack_propagate(False) # Keep height fixed during flip

        self.quiz_card = ctk.CTkFrame(self.card_container, corner_radius=20,
                                      fg_color=("#ffffff", "#1e293b"),
                                      border_width=2, border_color=("#e2e8f0", "#334155"))
        self.quiz_card.pack(expand=True, fill="both")

        # Central Label
        self.label_main = ctk.CTkLabel(self.quiz_card, text="", font=("Microsoft YaHei", 56, "bold"))
        self.label_main.place(relx=0.5, rely=0.5, anchor="center")

        # --- INPUT AREA ---
        self.entry_ans = ctk.CTkEntry(self.main_frame, font=("Inter", 24), height=70,
                                      placeholder_text="Type answer here...", justify="center")
        self.entry_ans.pack(pady=10, fill="x")
        self.entry_ans.focus_set()

        # Submit Button (Now just a button, not the primary feedback display)
        self.btn_submit = ctk.CTkButton(self.main_frame, text="Check Answer",
                                        font=("Inter", 16, "bold"), height=50,
                                        command=self.handle_enter)
        self.btn_submit.pack(fill="x", pady=5)

    # --- CORE LOGIC ---

    def handle_enter(self, event=None):
        # We disable the Enter key while waiting for the next word
        # to prevent accidental double-skipping.
        if not self.is_waiting_for_next:
            self.check_answer()

    def animate_card_flip(self, new_text, new_color, is_correct):
        """Simulates a card flip by shrinking and expanding the frame."""
        # Step 1: Shrink
        for w in range(100, 0, -10):
            self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=w/100, relheight=1)
            self.root.update_idletasks()
            time.sleep(0.01)

        # Update Content while 'invisible'
        self.label_main.configure(text=new_text, text_color="white")
        self.quiz_card.configure(fg_color=new_color)
        
        # Step 2: Expand
        for w in range(0, 105, 10):
            self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=w/100, relheight=1)
            self.root.update_idletasks()
            time.sleep(0.01)

    def stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def run_timer_tick(self):
        if not self.timer_running:
            return
            
        if self.word_time_limit > 0 and not self.is_waiting_for_next:
            self.word_time_left_ms -= 50
            # Update the UI bar
            self.timer_bar.set(max(0, self.word_time_left_ms / (self.word_time_limit * 1000)))
            
            if self.word_time_left_ms <= 0:
                # When time is up, trigger the check.
                # We no longer pass 'timeout=True' as a penalty,
                # we just let the function evaluate what's in the box.
                self.check_answer(is_timeout=True)
                return
        
        # Schedule next tick
        self.timer_job = self.root.after(50, self.run_timer_tick)

    def next_question(self):
        """Resets the card to the 'Front' (Chinese) side."""
        if self.current_idx >= len(self.questions):
            self.finalize_quiz()
            return
            
        self.is_waiting_for_next = False
        self.word_time_left_ms = self.word_time_limit * 1000
        
        chi, _ = self.questions[self.current_idx]
        
        # Reset card appearance before showing
        self.quiz_card.configure(fg_color=("#ffffff", "#1e293b"))
        self.label_main.configure(text=chi, text_color=("black", "white"))
        self.quiz_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        
        self.progress_lbl.configure(text=f"Question {self.current_idx + 1} of {len(self.questions)}")
        self.entry_ans.delete(0, 'end')
        self.entry_ans.focus_set()
        self.btn_submit.configure(text="Check Answer", fg_color="#3b82f6")

    def check_answer(self, is_timeout=False, skipped=False):
        if self.is_waiting_for_next: return
        chi, correct = self.questions[self.current_idx]
        user_input = self.entry_ans.get().strip()
        self.is_waiting_for_next = True
        
        # Evaluation
        words = correct.lower().split()
        is_common = all(bool(self.spell.known([w])) for w in words)
        is_correct = (user_input.lower() == correct.lower()) if is_common else (user_input == correct)

        # Prepare Feedback
        if skipped:
            feedback_color = "#64748b" # Slate
            status = "⏭️"
        elif is_correct:
            self.score += 1
            feedback_color = "#16a34a" # Green
            status = "✅"
        else:
            feedback_color = "#dc2626" # Red
            status = "❌"

        # PERFORM THE FLIP
        # Show the English word on the back of the card
        display_text = f"{correct}"
        self.animate_card_flip(display_text, feedback_color, is_correct)

        # Logging
        self.results_log.append({"chi": chi, "correct": correct, "user": user_input, "status": status})
        self.current_idx += 1
        
        # Auto-advance
        self.root.after(1500, self.next_question)


    def finalize_quiz(self):
        """Logs results into the persistent record before showing results."""
        quiz_data = {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "score": self.score,
            "total": len(self.questions),
            "mistakes": self.session_mistakes, # List of (chi, eng)
            "accuracy": round((self.score / len(self.questions)) * 100, 1)
        }
        
        # Update Database
        if self.student_name not in self.database:
            self.database[self.student_name] = {"sessions": [], "total_words_learned": 0}
        
        self.database[self.student_name]["sessions"].append(quiz_data)
        self.database[self.student_name]["total_words_learned"] += self.score
        self._save_database()
        
        # Keep the existing session history functionality
        old_quiz_data = {"score": self.score, "total": len(self.questions), "log": list(self.results_log), "time": time.strftime("%H:%M")}
        self.session_history.append(old_quiz_data)
        self._update_sidebar_stats()
        
        self.show_results()

    def show_results(self):
        """Displays the report for the round just completed."""
        self._clear_main()
        
        # 1. Round Header
        ctk.CTkLabel(self.main_frame, text="Round Summary", font=("Inter", 32, "bold")).pack(anchor="w")
        
        acc = (self.score / len(self.questions) * 100) if self.questions else 0
        stats_text = f"Student: {self.student_name}  |  Score: {self.score}/{len(self.questions)}  |  Accuracy: {acc:.1f}%"
        ctk.CTkLabel(self.main_frame, text=stats_text, font=("Inter", 16), text_color="#3b82f6").pack(anchor="w", pady=(5, 20))

        # 2. Results List (Scrollable)
        ctk.CTkLabel(self.main_frame, text="Detailed Word Report:", font=("Inter", 14, "bold")).pack(anchor="w")
        txt_box = ctk.CTkTextbox(self.main_frame, fg_color=("#f1f5f9", "#0f172a"), font=("Inter", 13), corner_radius=10)
        
        # results_log was populated during check_answer
        for r in self.results_log:
            txt_box.insert("end", f"{r['status']} {r['chi']} -> {r['correct']} (You typed: '{r['user']}')\n")
        
        txt_box.configure(state="disabled")
        txt_box.pack(fill="both", expand=True, pady=(10, 20))

        # 3. Action Buttons
        btn_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", pady=10)
        
        ctk.CTkButton(btn_row, text="🏠 Return to Home", fg_color="#64748b",
                      command=self.show_welcome_screen, height=50).pack(side="right", expand=True, padx=5)

        if self.session_mistakes:
            ctk.CTkButton(btn_row, text="🔁 Practice Mistakes Only", fg_color="#16a34a",
                          command=self.practice_mistakes, height=50).pack(side="left", expand=True, padx=5)

    def practice_mistakes(self):
        """Special mode that takes the mistakes from the LAST round and starts a new quiz."""
        if not self.session_mistakes:
            return
        
        # Convert mistakes list back into a dictionary for the quiz engine
        self.vocab = {chi: eng for chi, eng in self.session_mistakes}
        self.questions = list(self.vocab.items())
        random.shuffle(self.questions)
        
        self.current_idx = 0
        self.score = 0
        self.results_log = []
        self.session_mistakes = []
        
        self.show_quiz_ui()
        self.next_question()
        self.timer_running = True
        self.run_timer_tick()

    def show_session_summary(self):
        self._clear_main()
        ctk.CTkLabel(self.main_frame, text="Session Dashboard", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 30))
        
        total_correct = sum(q['score'] for q in self.session_history)
        total_attempted = sum(q['total'] for q in self.session_history)
        acc = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        
        stats_frame = ctk.CTkFrame(self.main_frame, height=100)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        # Grid inside stats frame
        ctk.CTkLabel(stats_frame, text=f"Total Accuracy\n{acc:.1f}%", font=("Inter", 16, "bold")).place(relx=0.2, rely=0.5, anchor="center")
        ctk.CTkLabel(stats_frame, text=f"Words Tested\n{total_attempted}", font=("Inter", 16, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(stats_frame, text=f"Quizzes\n{len(self.session_history)}", font=("Inter", 16, "bold")).place(relx=0.8, rely=0.5, anchor="center")

        ctk.CTkButton(self.main_frame, text="📥 Download Complete Session Report (.txt)", height=50, command=self.save_session_report).pack(pady=20, fill="x")
        ctk.CTkButton(self.main_frame, text="← Return to Menu", fg_color="transparent", command=self.show_welcome_screen).pack()

    # --- HISTORY PORTAL ---

    def show_personal_history(self):
        if not self.student_name or self.student_name not in self.database:
            messagebox.showinfo("No Records", "No history found for the current student.")
            return

        self._clear_main()
        ctk.CTkLabel(self.main_frame, text=f"History: {self.student_name}", font=("Inter", 28, "bold")).pack(anchor="w")
        
        history_frame = ctk.CTkScrollableFrame(self.main_frame, height=400)
        history_frame.pack(fill="both", expand=True, pady=20)

        records = self.database[self.student_name]["sessions"]
        for idx, session in enumerate(reversed(records)):
            color = "#1e293b" if idx % 2 == 0 else "transparent"
            row = ctk.CTkFrame(history_frame, fg_color=color)
            row.pack(fill="x", pady=2)
            
            lbl_text = f"📅 {session['date']}  |  🎯 Score: {session['score']}/{session['total']} ({session['accuracy']}%)"
            ctk.CTkLabel(row, text=lbl_text, font=("Inter", 13)).pack(side="left", padx=10, pady=5)
            
            # Show mistakes button
            if session['mistakes']:
                btn = ctk.CTkButton(row, text="View Mistakes", width=100, height=24,
                                     command=lambda m=session['mistakes']: self._show_mistake_popup(m))
                btn.pack(side="right", padx=10)

        ctk.CTkButton(self.main_frame, text="Back to Settings", command=self.show_settings).pack(pady=10)

    def _show_mistake_popup(self, mistakes):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Mistake Review")
        popup.geometry("400x500")
        txt = ctk.CTkTextbox(popup, font=("Inter", 14))
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        
        content = "WORDS TO REVIEW:\n" + "-"*20 + "\n"
        for m in mistakes:
            content += f"❌ {m[0]} -> {m[1]}\n"
        txt.insert("0.0", content)
        txt.configure(state="disabled")

    # --- HELPERS ---

    def _update_sidebar_stats(self):
        if not self.session_history:
            self.stats_label.configure(text="No quizzes completed yet.")
            return

        total_correct = sum(q['score'] for q in self.session_history)
        total_attempted = sum(q['total'] for q in self.session_history)
        self.stats_label.configure(text=f"Session Progress\n{total_correct}/{total_attempted} Correct")
        
        if self.student_name:
            self.name_display.configure(text=f"Student: {self.student_name}", text_color="#3b82f6")

    def _timer_choice_handler(self, val):
        if val == "Custom": self.custom_timer_entry.pack(pady=5, fill="x")
        else: self.custom_timer_entry.pack_forget()

    def validate_and_start(self):
        try:
            # --- 1. Capture Settings ---
            choice = self.seg_timer.get()
            custom_val = self.custom_timer_entry.get().strip()
            count_val = self.entry_count.get().strip()
            total_available = len(self.vocab)

            # Timer Logic
            if choice == "Custom":
                self.word_time_limit = int(custom_val) if custom_val else 10
            elif choice == "∞":
                self.word_time_limit = 0
            else:
                self.word_time_limit = int(choice.replace("s", ""))

            # Count Logic
            count = int(count_val) if count_val else total_available
            if count > total_available or count <= 0:
                messagebox.showwarning("Invalid Amount", f"Please enter a number between 1 and {total_available}.")
                return

            # --- 2. Save Settings to Database for next time ---
            if self.student_name in self.database:
                self.database[self.student_name]["last_config"] = {
                    "timer_choice": choice,
                    "custom_time": custom_val,
                    "word_count": count_val
                }
                self._save_database()

            # --- 3. Start Quiz ---
            self.questions = random.sample(list(self.vocab.items()), count)
            self.current_idx = 0
            self.score = 0
            self.results_log = []
            self.session_mistakes = []
            self.show_quiz_ui()
            self.root.bind("<Return>", self.handle_enter)
            self.next_question()
            self.timer_running = True
            self.run_timer_tick()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")

    def import_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text/Word", "*.txt *.docx")])
        if path:
            shutil.copy(path, os.path.join(self.save_dir, os.path.basename(path)))
            self.show_welcome_screen()

    def _parse_file(self, path):
        v = {}
        try:
            if path.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ',' in line:
                            word, defn = line.strip().split(',', 1)
                            v[defn.strip()] = word.strip()
            elif path.endswith('.docx') and Document:
                doc = Document(path)
                for para in doc.paragraphs:
                    if ',' in para.text:
                        word, defn = para.text.strip().split(',', 1)
                        v[defn.strip()] = word.strip()
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read file: {e}")
        return v

    def skip_question(self):
        if not self.is_waiting_for_next:
            # Mark it skipped in the log (check_answer handles auto-advance)
            self.check_answer(skipped=True)

    def save_session_report(self):
        report = f"STUDENT SESSION REPORT\nName: {self.student_name}\n"
        for i, q in enumerate(self.session_history):
            report += f"\nQUIZ #{i+1} [{q['time']}]\nScore: {q['score']}/{q['total']}\n"
            for item in q['log']: report += f"[{item['status']}] {item['chi']} -> {item['correct']}\n"
        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"{self.student_name}_Report.txt")
        if f:
            with open(f, 'w', encoding='utf-8') as file: file.write(report)
            messagebox.showinfo("Success", "Report Saved")

if __name__ == "__main__":
    root = ctk.CTk()
    app = VocabQuizApp(root)
    root.mainloop()