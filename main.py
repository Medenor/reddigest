import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox, QComboBox, QDialog, QFormLayout, QListWidget, QListWidgetItem, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QAction
from reddit_digest import get_reddit_digest, load_model_preferences, save_model_preferences, get_available_openai_models, get_available_gemini_models, load_api_keys
from digest_history import add_digest_to_history, load_digest_history, delete_digest_from_history
from theme_manager import ThemeManager

class RedditDigestApp(QMainWindow): # Changed from QWidget to QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reddigest - Reddit Threads Summarizer")
        self.setGeometry(100, 100, 800, 600)

        # Initialize ThemeManager
        current_dir = os.path.dirname(os.path.abspath(__file__))
        themes_path = os.path.join(current_dir, "themes")
        QDir.addSearchPath("themes", themes_path) # Register themes directory as a Qt resource path
        self.theme_manager = ThemeManager(QApplication.instance(), themes_path)
        self.theme_manager.load_theme("light") # Set initial theme

        self.init_ui()

    def init_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Pass central_widget to QVBoxLayout

        # Create the menu bar
        menubar = self.menuBar()

        # Create the File menu (existing functionality)
        file_menu = menubar.addMenu('File')
        
        # Add existing File menu actions (Import/Export if they were there, or add new ones)
        # For now, assuming no existing File menu actions in this app, but if there were, they'd go here.
        # Example:
        # import_action = QAction('Import', self)
        # import_action.triggered.connect(self.some_import_method)
        # file_menu.addAction(import_action)

        # Create the View menu for themes
        view_menu = menubar.addMenu('View')

        # Create Light Theme action
        light_theme_action = QAction('Light Theme', self)
        light_theme_action.triggered.connect(self.theme_manager.set_light_theme)
        view_menu.addAction(light_theme_action)

        # Create Dark Theme action
        dark_theme_action = QAction('Dark Theme', self)
        dark_theme_action.triggered.connect(self.theme_manager.set_dark_theme)
        view_menu.addAction(dark_theme_action)

        # Add separator
        view_menu.addSeparator()

        # Create Toggle Fullscreen action
        self.fullscreen_action = QAction('Toggle Fullscreen', self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

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

        controls_layout.addWidget(self.method_label)
        controls_layout.addWidget(self.method_combo)
        controls_layout.addWidget(self.detail_label)
        controls_layout.addWidget(self.detail_combo)
        
        # New row for text analysis checkbox
        text_analysis_layout = QHBoxLayout()
        self.enable_text_analysis_checkbox = QCheckBox("Enable Text Analysis (Keywords && Sentiment)")
        self.enable_text_analysis_checkbox.setChecked(False) # Default to disabled
        self.enable_text_analysis_checkbox.setVisible(False) # Hidden by default, only for AI methods
        text_analysis_layout.addWidget(self.enable_text_analysis_checkbox)
        text_analysis_layout.addStretch(1) # Push checkbox to the left

        self.generate_button = QPushButton("Generate Digest")
        self.generate_button.clicked.connect(self.generate_digest)

        # Digest display area
        self.digest_output = QTextEdit()
        self.digest_output.setReadOnly(True)

        # History button
        self.history_button = QPushButton("View History")
        self.history_button.clicked.connect(self.open_history)

        # Copy button
        self.copy_button = QPushButton("Copy Output")
        self.copy_button.clicked.connect(self.copy_digest_output)

        # Preferences button
        self.preferences_button = QPushButton("Preferences")
        self.preferences_button.clicked.connect(self.open_preferences)

        # Add layouts and widgets to main layout
        main_layout.addLayout(url_input_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(text_analysis_layout) # Add the new checkbox row
        main_layout.addWidget(self.generate_button) # Move generate button before output
        main_layout.addWidget(self.digest_output)
        
        # Add copy and preferences buttons in a horizontal layout at the bottom
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.copy_button)
        bottom_buttons_layout.addWidget(self.preferences_button)
        bottom_buttons_layout.addWidget(self.history_button) # Add history button
        main_layout.addLayout(bottom_buttons_layout)
        
        # Set the layout on the central widget
        central_widget.setLayout(main_layout)
        
        self.model_preferences = load_model_preferences() # Load preferences on startup
        self.update_model_selection(self.method_combo.currentIndex()) # Set initial visibility

    def open_preferences(self):
        dialog = PreferencesDialog(self.model_preferences, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model_preferences = dialog.get_preferences()
            save_model_preferences(self.model_preferences)
            # Re-apply model selection to reflect new defaults
            self.update_model_selection(self.method_combo.currentIndex())

    def open_history(self):
        dialog = HistoryDialog(self)
        dialog.exec()

    def generate_digest(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a Reddit URL.")
            return

        summarization_method = self.method_combo.currentData()
        # Model selection is now handled by preferences, not a direct dropdown
        selected_model = None 
        detail_level = self.detail_combo.currentData() if self.detail_combo.isVisible() else None
        enable_text_analysis = self.enable_text_analysis_checkbox.isChecked() and self.enable_text_analysis_checkbox.isVisible()

        # Call the get_reddit_digest function from reddit_digest.py
        digest_content, actual_model_used, submission_title = get_reddit_digest(url, summarization_method, selected_model, detail_level, enable_text_analysis)
        
        # Check if the result indicates an error from validation or other issues
        if digest_content.startswith("Invalid Reddit URL:"):
            QMessageBox.warning(self, "Input Error", digest_content)
        elif digest_content.startswith("An error occurred while summarizing with OpenAI.") or \
             digest_content.startswith("An error occurred while summarizing with Google Gemini.") or \
             digest_content.startswith("An unexpected error occurred while fetching Reddit content or summarizing."):
            QMessageBox.warning(self, "Processing Error", digest_content)
        else:
            self.digest_output.setText(digest_content)
            # Add to history after successful generation
            add_digest_to_history(url, summarization_method, actual_model_used, detail_level, digest_content, submission_title)

    def update_model_selection(self, index):
        selected_method = self.method_combo.itemData(index)
        self.detail_combo.setVisible(False)
        self.detail_label.setVisible(False)
        self.enable_text_analysis_checkbox.setVisible(False) # Hide by default

        if selected_method in ["openai", "gemini"]:
            self.detail_combo.setVisible(True)
            self.detail_label.setVisible(True)
            self.enable_text_analysis_checkbox.setVisible(True) # Show for AI methods
            
            api_keys = load_api_keys()
            if selected_method == "openai":
                if not api_keys.get('openai_api_key') or api_keys.get('openai_api_key') == "YOUR_OPENAI_API_KEY":
                    QMessageBox.warning(self, "API Key Missing", "OpenAI API key not configured. Please check your .env or praw.ini file.")
            elif selected_method == "gemini":
                if not api_keys.get('google_gemini_api_key') or api_keys.get('google_gemini_api_key') == "YOUR_GOOGLE_GEMINI_API_KEY":
                    QMessageBox.warning(self, "API Key Missing", "Google Gemini API key not configured. Please check your .env or praw.ini file.")

    def copy_digest_output(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.digest_output.toPlainText())
        QMessageBox.information(self, "Copy Success", "Digest content copied to clipboard!")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self.fullscreen_action.setChecked(True)

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

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digest History")
        self.setGeometry(250, 250, 700, 500)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        self.history_list_widget = QListWidget()
        self.history_list_widget.itemClicked.connect(self.display_selected_digest)
        main_layout.addWidget(self.history_list_widget)

        self.digest_display = QTextEdit()
        self.digest_display.setReadOnly(True)
        main_layout.addWidget(self.digest_display)

        self.copy_history_output_button = QPushButton("Copy Output")
        self.copy_history_output_button.clicked.connect(self.copy_history_digest_output)
        
        self.delete_all_history_button = QPushButton("Delete All")
        self.delete_all_history_button.clicked.connect(self.delete_all_history_entries)

        history_buttons_layout = QHBoxLayout()
        history_buttons_layout.addWidget(self.copy_history_output_button)
        history_buttons_layout.addWidget(self.delete_all_history_button)
        main_layout.addLayout(history_buttons_layout)

        self.load_history_entries()

        self.setLayout(main_layout)

    def copy_history_digest_output(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.digest_display.toPlainText())
        QMessageBox.information(self, "Copy Success", "Digest content copied to clipboard!")

    def load_history_entries(self):
        self.history_list_widget.clear()
        self.history_data = load_digest_history()
        for entry in self.history_data:
            list_item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 0, 0, 0)
            
            # Use the title if available, otherwise fallback to URL
            display_text = f"{entry['timestamp']} - {entry.get('title', entry['url'])} ({entry['method']})"
            label = QLabel(display_text)
            label.setWordWrap(True)
            
            delete_button = QPushButton("Delete")
            delete_button.setFixedSize(80, 24)
            # Use a lambda to pass the timestamp to the delete function
            delete_button.clicked.connect(lambda _, ts=entry['timestamp']: self.delete_history_entry(ts))
            
            item_layout.addWidget(label, 1) # Give the label a stretch factor of 1
            item_layout.addWidget(delete_button)
            list_item_widget.setLayout(item_layout)
            
            list_item = QListWidgetItem(self.history_list_widget)
            list_item.setSizeHint(list_item_widget.sizeHint())
            self.history_list_widget.addItem(list_item)
            self.history_list_widget.setItemWidget(list_item, list_item_widget)

    def display_selected_digest(self, item):
        index = self.history_list_widget.row(item)
        if 0 <= index < len(self.history_data):
            selected_entry = self.history_data[index]
            self.digest_display.setText(selected_entry['digest_content'])

    def delete_history_entry(self, timestamp):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     'Are you sure you want to delete this history entry?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            delete_digest_from_history(timestamp)
            self.load_history_entries() # Refresh the list
            self.digest_display.clear() # Clear the display

    def delete_all_history_entries(self):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     'Are you sure you want to delete ALL history entries? This action cannot be undone.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            from digest_history import clear_all_history
            clear_all_history()
            self.load_history_entries() # Refresh the list
            self.digest_display.clear() # Clear the display

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RedditDigestApp()
    window.show()
    sys.exit(app.exec())
