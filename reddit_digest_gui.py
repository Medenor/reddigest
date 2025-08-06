import sys
import praw
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox,
    QComboBox, QStackedWidget
)
from PyQt6.QtCore import Qt

from reddit_digest import get_reddit_digest as get_digest_from_backend
from reddit_digest import get_available_openai_models, get_available_gemini_models

class RedditDigestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reddit Digest App")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Input and controls layout using QGridLayout
        input_grid_layout = QGridLayout()
        
        # Row 0: URL input
        self.url_label = QLabel("Reddit URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Reddit post URL (e.g., https://www.reddit.com/r/python/comments/...)")
        input_grid_layout.addWidget(self.url_label, 0, 0)
        input_grid_layout.addWidget(self.url_input, 0, 1, 1, 3) # Span 3 columns to occupy the space

        # Row 1: Generate button
        self.generate_button = QPushButton("Generate Digest")
        self.generate_button.clicked.connect(self.generate_digest)
        input_grid_layout.addWidget(self.generate_button, 1, 0, 1, 4) # Span all 4 columns

        # Row 2: Summarization method selection
        self.method_label = QLabel("Summarization Method:")
        self.method_selector = QComboBox()
        self.method_selector.addItem("Top 5 Comments", "top5")
        self.method_selector.addItem("OpenAI Summary", "openai")
        self.method_selector.addItem("Gemini Summary", "gemini")
        self.method_selector.currentIndexChanged.connect(self.update_model_selection_visibility)
        input_grid_layout.addWidget(self.method_label, 2, 0)
        input_grid_layout.addWidget(self.method_selector, 2, 1)
        
        # Row 2, Column 2: Model selection (stacked widget)
        self.model_label = QLabel("Select Model:")
        self.openai_model_selector = QComboBox()
        self.openai_model_selector.setMaximumHeight(30) # Limit height to prevent excessive vertical expansion
        self.gemini_model_selector = QComboBox()
        self.gemini_model_selector.setMaximumHeight(30) # Limit height to prevent excessive vertical expansion

        # Populate OpenAI models
        for model in get_available_openai_models():
            self.openai_model_selector.addItem(model)
        
        # Populate Gemini models
        for model in get_available_gemini_models():
            self.gemini_model_selector.addItem(model)

        self.model_stacked_widget = QStackedWidget()
        self.empty_model_widget = QWidget() # Create a single instance for the empty widget
        self.model_stacked_widget.addWidget(self.empty_model_widget) # Empty widget for "Top 5"
        self.model_stacked_widget.addWidget(self.openai_model_selector)
        self.model_stacked_widget.addWidget(self.gemini_model_selector)
        input_grid_layout.addWidget(self.model_label, 2, 2)
        input_grid_layout.addWidget(self.model_stacked_widget, 2, 3)

        self.update_model_selection_visibility(self.method_selector.currentIndex()) # Set initial visibility

        # Digest display area
        self.digest_output = QTextEdit()
        self.digest_output.setReadOnly(True)

        # Add widgets to main layout
        main_layout.addLayout(input_grid_layout)
        main_layout.addWidget(self.digest_output)

        self.setLayout(main_layout)

    def update_model_selection_visibility(self, index):
        method = self.method_selector.itemData(index)
        if method == "openai":
            self.model_stacked_widget.setCurrentWidget(self.openai_model_selector)
            self.model_label.setVisible(True)
        elif method == "gemini":
            self.model_stacked_widget.setCurrentWidget(self.gemini_model_selector)
            self.model_label.setVisible(True)
        else:
            self.model_stacked_widget.setCurrentWidget(self.empty_model_widget) # Use the single instance
            self.model_label.setVisible(False)

    def generate_digest(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a Reddit URL.")
            return

        selected_method = self.method_selector.currentData()
        selected_model = None

        if selected_method == "openai":
            selected_model = self.openai_model_selector.currentText()
        elif selected_method == "gemini":
            selected_model = self.gemini_model_selector.currentText()
        
        # Call the backend function to get the digest
        digest_result = get_digest_from_backend(url, summarization_method=selected_method, model_name=selected_model)
        
        # Check if the result indicates an error from validation or other issues
        if digest_result.startswith("Invalid Reddit URL:"):
            QMessageBox.warning(self, "Input Error", digest_result)
        elif digest_result.startswith("An error occurred while summarizing with OpenAI.") or \
             digest_result.startswith("An error occurred while summarizing with Google Gemini.") or \
             digest_result.startswith("An unexpected error occurred while fetching Reddit content or summarizing."):
            QMessageBox.warning(self, "Processing Error", digest_result)
        else:
            self.digest_output.setText(digest_result)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RedditDigestApp()
    window.show()
    sys.exit(app.exec())
