import flet as ft

with open("icons.txt", "w") as f:
    for icon_name in dir(ft.icons):
        if not icon_name.startswith("_"):
            f.write(icon_name + "\n")
