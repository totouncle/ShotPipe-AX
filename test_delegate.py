import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QStyledItemDelegate,
    QComboBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt

# From dark_theme.py
DARK_THEME_STYLESHEET = """
/* 전체 애플리케이션 기본 스타일 - 강력한 다크 테마 */
QApplication {
    background-color: #1E1E1E !important;
    color: #E0E0E0 !important;
    font-family: "Segoe UI", "San Francisco", "Helvetica Neue", Arial, sans-serif;
    font-size: 9pt;
}

/* 메인 윈도우 */
QMainWindow {
    background-color: #1E1E1E !important;
    color: #E0E0E0 !important;
}

/* 위젯 공통 스타일 - 모든 위젯에 강제 적용 */
QWidget {
    background-color: #1E1E1E !important;
    color: #E0E0E0 !important;
    selection-background-color: #007ACC;
    selection-color: #FFFFFF;
}

/* 탭 위젯 */
QTabWidget {
    background-color: #1E1E1E !important;
    border: none;
}

QTabWidget::pane {
    border: 1px solid #3E3E42;
    background-color: #1E1E1E !important;
    top: -1px;
}

QTabWidget::tab-bar {
    alignment: left;
}

QTabBar::tab {
    background-color: #2D2D30;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #007ACC;
    color: #FFFFFF;
    border-bottom: 1px solid #007ACC;
}

QTabBar::tab:hover:!selected {
    background-color: #4A4A4F;
    color: #FFFFFF;
}

/* 라벨 */
QLabel {
    background-color: transparent;
    color: #E0E0E0;
    padding: 2px;
}

/* 라인 에디트 - 주석 처리하여 테스트 */
/*
QLineEdit {
    background-color: #383838;
    border: 1px solid #3E3E42;
    color: #E0E0E0;
    padding: 6px;
    border-radius: 3px;
    selection-background-color: #007ACC;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #007ACC;
    background-color: #404040;
}

QLineEdit:disabled {
    background-color: #2A2A2A;
    color: #808080;
    border: 1px solid #2A2A2A;
}

QLineEdit[readOnly="true"] {
    background-color: #333333;
    color: #C0C0C0;
    border: 1px solid #3E3E42;
}
*/

/* 버튼 */
QPushButton {
    background-color: #007ACC;
    color: #FFFFFF;
    border: 1px solid #007ACC;
    padding: 8px 16px;
    border-radius: 3px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1E8AD6;
    border: 1px solid #1E8AD6;
}

QPushButton:pressed {
    background-color: #005A9E;
    border: 1px solid #005A9E;
}

QPushButton:disabled {
    background-color: #4A4A4F;
    color: #808080;
    border: 1px solid #4A4A4F;
}

/* 특수 버튼 스타일 */
QPushButton[class="secondary"] {
    background-color: #3E3E42;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
}

QPushButton[class="secondary"]:hover {
    background-color: #4A4A4F;
    border: 1px solid #4A4A4F;
}

QPushButton[class="danger"] {
    background-color: #E74C3C;
    color: #FFFFFF;
    border: 1px solid #E74C3C;
}

QPushButton[class="danger"]:hover {
    background-color: #F1556C;
    border: 1px solid #F1556C;
}

/* 콤보박스 */
QComboBox {
    background-color: #383838;
    border: 1px solid #3E3E42;
    color: #E0E0E0;
    padding: 6px;
    border-radius: 3px;
    min-width: 100px;
}

QComboBox:focus {
    border: 1px solid #007ACC;
    background-color: #404040;
}

QComboBox::drop-down {
    border: none;
    background-color: transparent;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik01IDZMMCAwSDEwTDUgNloiIGZpbGw9IiNFMEUwRTAiLz4KPHN2Zz4K);
    width: 10px;
    height: 6px;
}

QComboBox QAbstractItemView {
    background-color: #383838;
    border: 1px solid #3E3E42;
    color: #E0E0E0;
    selection-background-color: #007ACC;
    selection-color: #FFFFFF;
}

/* 체크박스 */
QCheckBox {
    background-color: transparent;
    color: #E0E0E0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3E3E42;
    background-color: #383838;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #007ACC;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
}

QCheckBox::indicator:hover {
    border: 1px solid #007ACC;
}

QCheckBox::indicator:disabled {
    background-color: #2A2A2A;
    border: 1px solid #2A2A2A;
}

/* 라디오 버튼 */
QRadioButton {
    background-color: transparent;
    color: #E0E0E0;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3E3E42;
    background-color: #383838;
    border-radius: 8px;
}

QRadioButton::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #007ACC;
}

QRadioButton::indicator:checked::before {
    content: "";
    width: 6px;
    height: 6px;
    background-color: #FFFFFF;
    border-radius: 3px;
    margin: 4px;
}

QRadioButton::indicator:hover {
    border: 1px solid #007ACC;
}

/* 그룹박스 */
QGroupBox {
    background-color: #2D2D30;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #2D2D30;
    color: #E0E0E0;
}

/* 테이블 위젯 */
QTableWidget {
    background-color: #1E1E1E !important;
    alternate-background-color: #2A2A2A !important;
    color: #E0E0E0 !important;
    gridline-color: #3E3E42;
    selection-background-color: #007ACC;
    selection-color: #FFFFFF;
    border: 1px solid #3E3E42;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #3E3E42;
    color: #E0E0E0 !important;
    background-color: #1E1E1E !important;
}

QTableWidget::item:alternate {
    background-color: #2A2A2A !important;
}

QTableWidget::item:selected {
    background-color: #007ACC !important;
    color: #FFFFFF !important;
}

QTableWidget::item:hover {
    background-color: #404040 !important;
}

/* 테이블 헤더 */
QHeaderView::section {
    background-color: #2D2D30 !important;
    color: #FFFFFF !important;
    border: 1px solid #3E3E42;
    padding: 8px;
    font-weight: bold;
    text-align: left;
}

QHeaderView::section:hover {
    background-color: #404040 !important;
}

QHeaderView::section:pressed {
    background-color: #007ACC !important;
}

/* 스크롤바 */
QScrollBar:vertical {
    background-color: #2D2D30;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #4A4A4F;
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5A5A5F;
}

QScrollBar::handle:vertical:pressed {
    background-color: #007ACC;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #2D2D30;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #4A4A4F;
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5A5A5F;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #007ACC;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

/* 프로그레스바 */
QProgressBar {
    background-color: #383838;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    text-align: center;
    color: #E0E0E0;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #007ACC;
    border-radius: 2px;
}

/* 텍스트 에디트 */
QTextEdit {
    background-color: #2D2D30;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    selection-background-color: #007ACC;
    selection-color: #FFFFFF;
    font-family: "Consolas", "Monaco", "Courier New", monospace;
}

QTextEdit:focus {
    border: 1px solid #007ACC;
}

/* 스테이터스바 */
QStatusBar {
    background-color: #383838;
    color: #E0E0E0;
    border-top: 1px solid #3E3E42;
    padding: 4px;
}

QStatusBar::item {
    border: none;
}

/* 메뉴바 */
QMenuBar {
    background-color: #383838;
    color: #E0E0E0;
    border-bottom: 1px solid #3E3E42;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #007ACC;
    color: #FFFFFF;
}

QMenuBar::item:pressed {
    background-color: #005A9E;
}

/* 메뉴 */
QMenu {
    background-color: #383838;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 20px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #007ACC;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background-color: #3E3E42;
    margin: 4px 0;
}

/* 메시지박스 */
QMessageBox {
    background-color: #2D2D30;
    color: #E0E0E0;
}

QMessageBox QLabel {
    color: #E0E0E0;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 16px;
}

/* 다이얼로그 */
QDialog {
    background-color: #2D2D30;
    color: #E0E0E0;
}

/* 파일 다이얼로그는 시스템 기본 스타일을 사용하므로 별도 스타일링 불가 */

/* 툴팁 */
QToolTip {
    background-color: #383838;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    padding: 4px;
    border-radius: 2px;
}

/* 스플리터 */
QSplitter::handle {
    background-color: #3E3E42;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #007ACC;
}

/* 독 위젯 */
QDockWidget {
    background-color: #2D2D30;
    color: #E0E0E0;
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(float.png);
}

QDockWidget::title {
    background-color: #383838;
    color: #E0E0E0;
    padding: 6px;
    text-align: left;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    padding: 2px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #4A4A4F;
}

/* 스핀박스 */
QSpinBox, QDoubleSpinBox {
    background-color: #383838;
    border: 1px solid #3E3E42;
    color: #E0E0E0;
    padding: 4px;
    border-radius: 3px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #007ACC;
    background-color: #404040;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #4A4A4F;
    border: 1px solid #3E3E42;
    width: 16px;
    border-radius: 2px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #5A5A5F;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #4A4A4F;
    border: 1px solid #3E3E42;
    width: 16px;
    border-radius: 2px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #5A5A5F;
}

/* 슬라이더 */
QSlider::groove:horizontal {
    border: 1px solid #3E3E42;
    height: 6px;
    background-color: #383838;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #007ACC;
    border: 1px solid #007ACC;
    width: 16px;
    border-radius: 8px;
    margin: -5px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #1E8AD6;
    border: 1px solid #1E8AD6;
}

QSlider::groove:vertical {
    border: 1px solid #3E3E42;
    width: 6px;
    background-color: #383838;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background-color: #007ACC;
    border: 1px solid #007ACC;
    height: 16px;
    border-radius: 8px;
    margin: 0 -5px;
}

QSlider::handle:vertical:hover {
    background-color: #1E8AD6;
    border: 1px solid #1E8AD6;
}
"""

def apply_dark_theme(app):
    """Apply the dark theme to the QApplication."""
    app.setStyleSheet(DARK_THEME_STYLESHEET)

# From file_tab_temp.py
class SequenceShotDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(True)
        # combo.setInsertPolicy(QComboBox.NoInsert)  # Temporarily disable for testing
        combo.addItem("c001")
        combo.addItem("c002")
        return combo

    def setEditorData(self, editor, index):
        current_value = index.model().data(index, Qt.DisplayRole)
        if current_value:
            editor.setEditText(current_value)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delegate Test")
        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Sequence", "Shot", "Other"])
        self.setCentralWidget(self.table)

        delegate = SequenceShotDelegate(self)
        self.table.setItemDelegateForColumn(1, delegate)

        for i in range(5):
            self.table.setItem(i, 0, QTableWidgetItem(f"seq{i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"c{i*10:03d}"))
            self.table.setItem(i, 2, QTableWidgetItem("..."))

def main():
    app = QApplication(sys.argv)
    
    apply_dark_theme(app) # Enabled now
    
    window = TestWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 