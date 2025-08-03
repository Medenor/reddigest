import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from reddit_digest import get_reddit_digest # Import the function from reddit_digest.py

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

        # Model selection
        self.model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.setVisible(False) # Hidden by default

        # Detail level selection
        self.detail_label = QLabel("Detail Level:")
        self.detail_combo = QComboBox()
        self.detail_combo.addItem("Concise", "concise")
        self.detail_combo.addItem("Standard", "standard")
        self.detail_combo.addItem("Detailed", "detailed")
        self.detail_combo.setVisible(False) # Hidden by default

        self.generate_button = QPushButton("Generate Digest")
        self.generate_button.clicked.connect(self.generate_digest)

        controls_layout.addWidget(self.method_label)
        controls_layout.addWidget(self.method_combo)
        controls_layout.addWidget(self.model_label)
        controls_layout.addWidget(self.model_combo)
        controls_layout.addWidget(self.detail_label)
        controls_layout.addWidget(self.detail_combo)
        controls_layout.addWidget(self.generate_button)

        # Digest display area
        self.digest_output = QTextEdit()
        self.digest_output.setReadOnly(True)

        # Copy button
        self.copy_button = QPushButton("Copy Output")
        self.copy_button.clicked.connect(self.copy_digest_output)

        # Add layouts and widgets to main layout
        main_layout.addLayout(url_input_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.digest_output)
        main_layout.addWidget(self.copy_button)

        self.setLayout(main_layout)
        self.update_model_selection(self.method_combo.currentIndex()) # Set initial visibility

    def generate_digest(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a Reddit URL.")
            return

        summarization_method = self.method_combo.currentData()
        selected_model = self.model_combo.currentText() if self.model_combo.isVisible() else None
        detail_level = self.detail_combo.currentData() if self.detail_combo.isVisible() else None

        # Call the get_reddit_digest function from reddit_digest.py
        digest_result = get_reddit_digest(url, summarization_method, selected_model, detail_level)
        self.digest_output.setText(digest_result)

    def update_model_selection(self, index):
        from reddit_digest import get_available_openai_models, get_available_gemini_models
        
        selected_method = self.method_combo.itemData(index)
        self.model_combo.clear()
        self.model_combo.setVisible(False)
        self.model_label.setVisible(False)
        self.detail_combo.setVisible(False)
        self.detail_label.setVisible(False)

        if selected_method == "openai":
            models = get_available_openai_models()
            if models:
                self.model_combo.addItems(models)
                self.model_combo.setVisible(True)
                self.model_label.setVisible(True)
                self.detail_combo.setVisible(True)
                self.detail_label.setVisible(True)
            else:
                QMessageBox.warning(self, "API Key Missing", "OpenAI API key not configured or models could not be fetched. Please check praw.ini.")
        elif selected_method == "gemini":
            models = get_available_gemini_models()
            if models:
                self.model_combo.addItems(models)
                self.model_combo.setVisible(True)
                self.model_label.setVisible(True)
                self.detail_combo.setVisible(True)
                self.detail_label.setVisible(True)
            else:
                QMessageBox.warning(self, "API Key Missing", "Google Gemini API key not configured or models could not be fetched. Please check praw.ini.")

    def copy_digest_output(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.digest_output.toPlainText())
        QMessageBox.information(self, "Copy Success", "Digest content copied to clipboard!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RedditDigestApp()
    window.show()
    sys.exit(app.exec())
