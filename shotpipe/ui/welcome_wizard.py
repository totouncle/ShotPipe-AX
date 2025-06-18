"""
첫 실행 시 나타나는 환영 및 설정 마법사
"""
import os
import json
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QCheckBox, QComboBox,
    QStackedWidget, QWizard, QWizardPage, QFileDialog,
    QMessageBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from ..config import config

logger = logging.getLogger(__name__)

class WelcomeWizard(QWizard):
    """첫 실행 시 나타나는 환영 마법사"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ShotPipe 설정 마법사")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setFixedSize(700, 500)
        
        # 마법사 스타일 설정
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.HaveHelpButton, False)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        
        # 페이지들 추가
        self.addPage(WelcomePage())
        self.addPage(WorkspacePage())
        self.addPage(ShotgridPage())
        self.addPage(CompletePage())
        
        # 설정 저장용
        self.settings = {}
        
        logger.info("환영 마법사 초기화 완료")

class WelcomePage(QWizardPage):
    """환영 페이지"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("ShotPipe에 오신 것을 환영합니다! 🎬")
        self.setSubTitle("AI 생성 파일을 Shotgrid로 자동 업로드하는 도구입니다")
        
        layout = QVBoxLayout()
        
        # 환영 메시지
        welcome_text = QTextEdit()
        welcome_text.setReadOnly(True)
        welcome_text.setMaximumHeight(200)
        welcome_text.setHtml("""
        <h3>ShotPipe가 처음이신가요?</h3>
        <p>걱정하지 마세요! 이 설정 마법사가 3분 내에 모든 설정을 완료해드립니다.</p>
        
        <h4>🎯 ShotPipe로 할 수 있는 일:</h4>
        <ul>
        <li>📁 AI 생성 파일들을 자동으로 스캔하고 정리</li>
        <li>🏷️ Shotgrid 규칙에 맞게 파일명 자동 변경</li>
        <li>☁️ Shotgrid에 원클릭으로 업로드</li>
        <li>📊 처리 진행상황 실시간 모니터링</li>
        </ul>
        
        <p><b>약 3분이면 설정이 완료됩니다. 시작해볼까요?</b></p>
        """)
        layout.addWidget(welcome_text)
        
        # 체크박스
        self.show_again_cb = QCheckBox("다음에 이 마법사를 다시 표시하지 않기")
        layout.addWidget(self.show_again_cb)
        
        self.setLayout(layout)

class WorkspacePage(QWizardPage):
    """작업공간 설정 페이지"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("작업 폴더 설정 📁")
        self.setSubTitle("ShotPipe가 사용할 작업 폴더를 설정합니다")
        
        layout = QVBoxLayout()
        
        # 설명
        info_label = QLabel("""
        <b>작업 폴더란?</b><br>
        • <b>입력 폴더</b>: AI로 생성한 파일들을 넣는 곳<br>
        • <b>출력 폴더</b>: 처리된 파일들이 저장되는 곳<br>
        • <b>백업 폴더</b>: 원본 파일들의 백업이 저장되는 곳
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 기본 경로 설정
        default_workspace = str(Path.home() / "Documents" / "ShotPipe")
        
        # 작업공간 경로
        workspace_group = QGroupBox("작업공간 위치")
        workspace_layout = QVBoxLayout()
        
        self.workspace_edit = QLineEdit(default_workspace)
        workspace_layout.addWidget(self.workspace_edit)
        
        browse_layout = QHBoxLayout()
        browse_btn = QPushButton("📁 찾아보기")
        browse_btn.clicked.connect(self.browse_workspace)
        browse_layout.addWidget(browse_btn)
        browse_layout.addStretch()
        workspace_layout.addLayout(browse_layout)
        
        workspace_group.setLayout(workspace_layout)
        layout.addWidget(workspace_group)
        
        # 자동 생성 체크박스들
        options_group = QGroupBox("폴더 자동 생성")
        options_layout = QVBoxLayout()
        
        self.create_input_cb = QCheckBox("📥 input 폴더 (AI 생성 파일용)")
        self.create_input_cb.setChecked(True)
        options_layout.addWidget(self.create_input_cb)
        
        self.create_processed_cb = QCheckBox("📤 processed 폴더 (처리된 파일용)")
        self.create_processed_cb.setChecked(True)
        options_layout.addWidget(self.create_processed_cb)
        
        self.create_backup_cb = QCheckBox("💾 backup 폴더 (백업용)")
        self.create_backup_cb.setChecked(True)
        options_layout.addWidget(self.create_backup_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def browse_workspace(self):
        """작업공간 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "작업공간 폴더 선택",
            self.workspace_edit.text()
        )
        if folder:
            self.workspace_edit.setText(folder)
    
    def validatePage(self):
        """페이지 검증 및 폴더 생성"""
        workspace_path = Path(self.workspace_edit.text())
        
        try:
            # 작업공간 폴더 생성
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # 하위 폴더들 생성
            if self.create_input_cb.isChecked():
                (workspace_path / "input").mkdir(exist_ok=True)
            
            if self.create_processed_cb.isChecked():
                (workspace_path / "processed").mkdir(exist_ok=True)
                
            if self.create_backup_cb.isChecked():
                (workspace_path / "backup").mkdir(exist_ok=True)
            
            # 설정 저장
            self.wizard().settings['workspace'] = str(workspace_path)
            
            QMessageBox.information(
                self, 
                "성공", 
                f"작업 폴더가 생성되었습니다:\n{workspace_path}"
            )
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "오류", 
                f"폴더 생성 중 오류가 발생했습니다:\n{str(e)}"
            )
            return False

class ShotgridPage(QWizardPage):
    """Shotgrid 연결 설정 페이지"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Shotgrid 연결 설정 ☁️")
        self.setSubTitle("Shotgrid 서버 연결을 설정합니다 (선택사항)")
        
        layout = QVBoxLayout()
        
        # 설명
        info_label = QLabel("""
        <b>Shotgrid 연결이란?</b><br>
        처리된 파일들을 Shotgrid 서버에 자동으로 업로드하는 기능입니다.<br>
        지금 설정하지 않아도 나중에 프로그램에서 설정할 수 있습니다.
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 설정 여부 선택
        self.setup_now_cb = QCheckBox("지금 Shotgrid 연결 설정하기")
        self.setup_now_cb.toggled.connect(self.toggle_settings)
        layout.addWidget(self.setup_now_cb)
        
        # 연결 설정 그룹
        self.settings_group = QGroupBox("연결 정보")
        settings_layout = QVBoxLayout()
        
        # 서버 URL
        settings_layout.addWidget(QLabel("서버 URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://your-studio.shotgunstudio.com")
        settings_layout.addWidget(self.url_edit)
        
        # 스크립트 이름
        settings_layout.addWidget(QLabel("스크립트 이름:"))
        self.script_edit = QLineEdit()
        self.script_edit.setPlaceholderText("ShotPipe_API")
        settings_layout.addWidget(self.script_edit)
        
        # API 키
        settings_layout.addWidget(QLabel("API 키:"))
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.Password)
        self.api_edit.setPlaceholderText("API 키를 입력하세요")
        settings_layout.addWidget(self.api_edit)
        
        # 연결 테스트 버튼
        test_btn = QPushButton("🔗 연결 테스트")
        test_btn.clicked.connect(self.test_connection)
        settings_layout.addWidget(test_btn)
        
        self.settings_group.setLayout(settings_layout)
        self.settings_group.setEnabled(False)
        layout.addWidget(self.settings_group)
        
        # 도움말
        help_label = QLabel("""
        <b>💡 도움이 필요하신가요?</b><br>
        • 연결 정보는 Shotgrid 관리자에게 문의하세요<br>
        • 나중에 프로그램 메뉴에서도 설정할 수 있습니다<br>
        • F1 키를 누르면 상세한 도움말을 볼 수 있습니다
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def toggle_settings(self, checked):
        """설정 그룹 활성화/비활성화"""
        self.settings_group.setEnabled(checked)
    
    def test_connection(self):
        """연결 테스트"""
        if not all([self.url_edit.text(), self.script_edit.text(), self.api_edit.text()]):
            QMessageBox.warning(self, "경고", "모든 필드를 입력해주세요.")
            return
        
        # 간단한 연결 테스트 (실제 구현은 shotgrid 모듈 사용)
        QMessageBox.information(self, "연결 테스트", "연결 테스트 기능은 메인 프로그램에서 이용하세요.")
    
    def validatePage(self):
        """페이지 검증"""
        if self.setup_now_cb.isChecked():
            if not all([self.url_edit.text(), self.script_edit.text(), self.api_edit.text()]):
                QMessageBox.warning(self, "경고", "모든 연결 정보를 입력해주세요.")
                return False
            
            # 설정 저장
            self.wizard().settings['shotgrid'] = {
                'url': self.url_edit.text(),
                'script_name': self.script_edit.text(),
                'api_key': self.api_edit.text()
            }
        
        return True

class CompletePage(QWizardPage):
    """완료 페이지"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("설정 완료! 🎉")
        self.setSubTitle("ShotPipe 사용 준비가 완료되었습니다")
        
        layout = QVBoxLayout()
        
        # 완료 메시지
        complete_text = QTextEdit()
        complete_text.setReadOnly(True)
        complete_text.setMaximumHeight(250)
        complete_text.setHtml("""
        <h3>🎉 축하합니다! 설정이 완료되었습니다.</h3>
        
        <h4>📋 다음 단계:</h4>
        <ol>
        <li><b>AI 생성 파일 준비</b>: input 폴더에 처리할 파일들을 넣으세요</li>
        <li><b>파일 스캔</b>: "파일 처리" 탭에서 "스캔" 버튼을 클릭</li>
        <li><b>설정 확인</b>: 시퀀스, 샷 등의 정보를 확인하고 수정</li>
        <li><b>처리 실행</b>: "처리 시작" 버튼으로 파일 처리</li>
        <li><b>업로드</b>: "Shotgrid 업로드" 탭에서 업로드 진행</li>
        </ol>
        
        <h4>💡 유용한 팁:</h4>
        <ul>
        <li><b>F1 키</b>: 언제든 도움말을 볼 수 있습니다</li>
        <li><b>로그 창</b>: 하단에서 실시간 진행상황을 확인하세요</li>
        <li><b>설정 변경</b>: 메뉴 → 설정에서 언제든 변경 가능</li>
        </ul>
        """)
        layout.addWidget(complete_text)
        
        # 바로 시작 체크박스
        self.start_now_cb = QCheckBox("마법사를 닫고 바로 ShotPipe 시작하기")
        self.start_now_cb.setChecked(True)
        layout.addWidget(self.start_now_cb)
        
        self.setLayout(layout)
    
    def validatePage(self):
        """설정 저장 및 완료"""
        wizard = self.wizard()
        
        # 설정을 파일에 저장
        try:
            settings_path = Path.home() / ".shotpipe" / "wizard_settings.json"
            settings_path.parent.mkdir(exist_ok=True)
            
            settings_data = {
                "wizard_completed": True,
                "completion_date": str(Path.ctime(Path.now())),
                **wizard.settings
            }
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"마법사 설정 저장 완료: {settings_path}")
            return True
            
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            QMessageBox.warning(self, "경고", f"설정 저장에 실패했습니다: {str(e)}")
            return True  # 그래도 진행

def should_show_wizard():
    """마법사를 표시해야 하는지 확인"""
    settings_path = Path.home() / ".shotpipe" / "wizard_settings.json"
    
    try:
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return not settings.get("wizard_completed", False)
        else:
            return True  # 첫 실행
    except Exception as e:
        logger.warning(f"마법사 설정 확인 실패: {e}")
        return True  # 오류 시 표시

def show_welcome_wizard(parent=None):
    """환영 마법사 표시"""
    if should_show_wizard():
        wizard = WelcomeWizard(parent)
        return wizard.exec_() == QDialog.Accepted
    return False