import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile, QTextStream

class ThemeManager:
    def __init__(self, app: QApplication, themes_dir: str):
        self.app = app
        self.themes_dir = themes_dir
        self.current_theme = "light"
        self.load_theme(self.current_theme)

    def load_theme(self, theme_name):
        qss_file_path = os.path.join(self.themes_dir, f"{theme_name}.qss")
        qss_file = QFile(qss_file_path)
        if qss_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(qss_file)
            self.app.setStyleSheet(stream.readAll())
            qss_file.close()
            self.current_theme = theme_name
        else:
            print(f"Could not load theme: {theme_name}.qss")

    def set_light_theme(self):
        self.load_theme("light")

    def set_dark_theme(self):
        self.load_theme("dark")

    def get_current_theme(self):
        return self.current_theme
