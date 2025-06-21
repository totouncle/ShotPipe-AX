"""
About Dialog for ShotPipe
Displays application information, including README and version.
"""
import os
import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
import markdown
from ..utils.version_utils import get_version_info

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("ShotPipe 정보")
        self.setMinimumSize(700, 500)

        main_layout = QVBoxLayout(self)

        # Content display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setOpenExternalLinks(True)

        # Version and footer info
        version_string = get_version_info()
        footer_label = QLabel(f"<b>ShotPipe</b> - {version_string}")
        footer_label.setAlignment(Qt.AlignCenter)

        # Close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        main_layout.addWidget(self.text_display)
        main_layout.addWidget(footer_label)
        main_layout.addLayout(button_layout)

        self.load_readme()

    def load_readme(self):
        """Load README.md, convert to HTML, and display it."""
        try:
            # Assuming the script is run from the project root (AX_pipe)
            readme_path = "ShotPipe/README.md"
            if not os.path.exists(readme_path):
                # Fallback for different execution contexts
                readme_path = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")

            with open(readme_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                html_content = markdown.markdown(md_content)
                self.text_display.setHtml(html_content)

        except FileNotFoundError:
            error_message = "ERROR: README.md 파일을 찾을 수 없습니다."
            self.text_display.setText(error_message)
            logger.error(error_message)
        except Exception as e:
            error_message = f"README.md 파일을 읽는 중 오류가 발생했습니다: {e}"
            self.text_display.setText(error_message)
            logger.error(error_message, exc_info=True) 