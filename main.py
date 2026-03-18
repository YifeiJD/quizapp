import customtkinter as ctk
from ui.app import VocabQuizApp

# Set appearance mode and color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    root = ctk.CTk()
    app = VocabQuizApp(root)
    root.mainloop()
