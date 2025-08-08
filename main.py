import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox, QComboBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from reddit_digest import get_reddit_digest, load_model_preferences, save_model_preferences, get_available_openai_models, get_available_gemini_models, load_api_keys # Import necessary functions

class RedditDigestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reddit Digest App")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # URL input layout
        url_input_layout = QHBoxLayout()
        self.url_label = QLabel("Reddit URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Reddit post URL (e.g., https://www.reddit.com/r/python/comments/...)")
        url_input_layout.addWidget(self.url_label)
        url_input_layout.addWidget(self.url_input)

        # Summarization method and model selection layout
        controls_layout = QHBoxLayout()
        self.method_label = QLabel("Summarization Method:")
        self.method_combo = QComboBox()
        self.method_combo.addItem("Top 5 Comments", "top5")
        self.method_combo.addItem("OpenAI Summary", "openai")
        self.method_combo.addItem("Google Gemini Summary", "gemini")
        self.method_combo.currentIndexChanged.connect(self.update_model_selection)

        # Detail level selection
        self.detail_label = QLabel("Detail Level:")
        self.detail_combo = QComboBox()
        self.detail_combo.addItem("Concise", "concise")
        self.detail_combo.addItem("Standard", "standard")
        self.detail_combo.addItem("Detailed", "detailed")
        self.detail_combo.setCurrentText("Standard") # Set "Standard" as default
        self.detail_combo.setVisible(False) # Hidden by default

        self.generate_button = QPushButton("Generate Digest")
        self.generate_button.clicked.connect(self.generate_digest)

        controls_layout.addWidget(self.method_label)
        controls_layout.addWidget(self.method_combo)
        controls_layout.addWidget(self.detail_label)
        controls_layout.addWidget(self.detail_combo)
        controls_layout.addWidget(self.generate_button)

        # Digest display area
        self.digest_output = QTextEdit()
        self.digest_output.setReadOnly(True)

        # Copy button
        self.copy_button = QPushButton("Copy Output")
        self.copy_button.clicked.connect(self.copy_digest_output)

        # Preferences button
        self.preferences_button = QPushButton("Preferences")
        self.preferences_button.clicked.connect(self.open_preferences)

        # Add layouts and widgets to main layout
        main_layout.addLayout(url_input_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.digest_output)
        
        # Add copy and preferences buttons in a horizontal layout at the bottom
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.copy_button)
        bottom_buttons_layout.addWidget(self.preferences_button)
        main_layout.addLayout(bottom_buttons_layout)

        self.setLayout(main_layout)
        
        self.model_preferences = load_model_preferences() # Load preferences on startup
        self.update_model_selection(self.method_combo.currentIndex()) # Set initial visibility

    def open_preferences(self):
        dialog = PreferencesDialog(self.model_preferences, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model_preferences = dialog.get_preferences()
            save_model_preferences(self.model_preferences)
            # Re-apply model selection to reflect new defaults
            self.update_model_selection(self.method_combo.currentIndex())

    def generate_digest(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a Reddit URL.")
            return

        summarization_method = self.method_combo.currentData()
        # Model selection is now handled by preferences, not a direct dropdown
        selected_model = None 
        detail_level = self.detail_combo.currentData() if self.detail_combo.isVisible() else None

        # Call the get_reddit_digest function from reddit_digest.py
        digest_result = get_reddit_digest(url, summarization_method, selected_model, detail_level)
        
        # Check if the result indicates an error from validation or other issues
        if digest_result.startswith("Invalid Reddit URL:"):
            QMessageBox.warning(self, "Input Error", digest_result)
        elif digest_result.startswith("An error occurred while summarizing with OpenAI.") or \
             digest_result.startswith("An error occurred while summarizing with Google Gemini.") or \
             digest_result.startswith("An unexpected error occurred while fetching Reddit content or summarizing."):
            QMessageBox.warning(self, "Processing Error", digest_result)
        else:
            self.digest_output.setText(digest_result)

    def update_model_selection(self, index):
        selected_method = self.method_combo.itemData(index)
        self.detail_combo.setVisible(False)
        self.detail_label.setVisible(False)

        if selected_method == "openai":
            self.detail_combo.setVisible(True)
            self.detail_label.setVisible(True)
            # No need to fetch models here, as selection is done in preferences
            # Check if API key is configured
            api_keys = load_api_keys()
            if not api_keys.get('openai_api_key') or api_keys.get('openai_api_key') == "YOUR_OPENAI_API_KEY":
                QMessageBox.warning(self, "API Key Missing", "OpenAI API key not configured. Please check your .env or praw.ini file.")
        elif selected_method == "gemini":
            self.detail_combo.setVisible(True)
            self.detail_label.setVisible(True)
            # No need to fetch models here, as selection is done in preferences
            # Check if API key is configured
            api_keys = load_api_keys()
            if not api_keys.get('google_gemini_api_key') or api_keys.get('google_gemini_api_key') == "YOUR_GOOGLE_GEMINI_API_KEY":
                QMessageBox.warning(self, "API Key Missing", "Google Gemini API key not configured. Please check your .env or praw.ini file.")

    def copy_digest_output(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.digest_output.toPlainText())
        QMessageBox.information(self, "Copy Success", "Digest content copied to clipboard!")

class PreferencesDialog(QDialog):
    def __init__(self, current_preferences, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setGeometry(200, 200, 400, 200)
        self.current_preferences = current_preferences.copy() # Work with a copy

        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # OpenAI Default Model
        self.openai_models = get_available_openai_models()
        self.openai_default_combo = QComboBox()
        self.openai_default_combo.addItems(["None"] + self.openai_models)
        default_openai = self.current_preferences.get('openai_default_model')
        if default_openai and default_openai in self.openai_models:
            self.openai_default_combo.setCurrentText(default_openai)
        else:
            self.openai_default_combo.setCurrentText("gpt-4.1-nano" if "gpt-4.1-nano" in self.openai_models else "None")
        layout.addRow("Default OpenAI Model:", self.openai_default_combo)

        # Google Gemini Default Model
        self.gemini_models = get_available_gemini_models()
        self.gemini_default_combo = QComboBox()
        self.gemini_default_combo.addItems(["None"] + self.gemini_models)
        default_gemini = self.current_preferences.get('gemini_default_model')
        if default_gemini and default_gemini in self.gemini_models:
            self.gemini_default_combo.setCurrentText(default_gemini)
        else:
            self.gemini_default_combo.setCurrentText("gemini-2.5-flash" if "gemini-2.5-flash" in self.gemini_models else "None")
        layout.addRow("Default Gemini Model:", self.gemini_default_combo)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def get_preferences(self):
        openai_model = self.openai_default_combo.currentText()
        gemini_model = self.gemini_default_combo.currentText()
        
        if openai_model == "None":
            self.current_preferences.pop('openai_default_model', None)
        else:
            self.current_preferences['openai_default_model'] = openai_model

        if gemini_model == "None":
            self.current_preferences.pop('gemini_default_model', None)
        else:
            self.current_preferences['gemini_default_model'] = gemini_model
            
        return self.current_preferences

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RedditDigestApp()
    window.show()
    sys.exit(app.exec())
