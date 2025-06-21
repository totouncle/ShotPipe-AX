"""
Project settings dialog for managing fixed project configuration.
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QFormLayout, QGroupBox, QComboBox,
    QMessageBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from ..config import config

logger = logging.getLogger(__name__)

try:
    from ..shotgrid.api_connector import ShotgridConnector
    from ..shotgrid.entity_manager import EntityManager
    SHOTGRID_AVAILABLE = True
except ImportError:
    SHOTGRID_AVAILABLE = False
    logger.warning("Shotgrid modules not available for project settings")

class ProjectSettingsDialog(QDialog):
    """Dialog for configuring fixed project settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로젝트 설정")
        
        # Shotgrid 연동 관련 초기화
        self.shotgrid_connector = None
        self.shotgrid_entity_manager = None
        self.projects = []
        
        if SHOTGRID_AVAILABLE:
            try:
                self.shotgrid_connector = ShotgridConnector()
                self.shotgrid_entity_manager = EntityManager(self.shotgrid_connector)
            except Exception as e:
                logger.warning(f"Shotgrid 연동 초기화 실패: {e}")
        
        self._init_ui()
        self._load_current_settings()
        self._load_projects()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # 고정 프로젝트 설정 그룹
        project_group = QGroupBox("고정 프로젝트 설정")
        project_form = QFormLayout()
        
        # 현재 고정 프로젝트
        self.current_project_combo = QComboBox()
        self.current_project_combo.setEditable(True)
        project_form.addRow("현재 고정 프로젝트:", self.current_project_combo)
        
        # 자동 선택 옵션
        self.auto_select_cb = QCheckBox("앱 시작 시 자동으로 프로젝트 선택")
        project_form.addRow(self.auto_select_cb)
        
        # 프로젝트 선택기 표시 옵션
        self.show_selector_cb = QCheckBox("프로젝트 선택기 표시 (숨김 권장)")
        project_form.addRow(self.show_selector_cb)
        
        project_group.setLayout(project_form)
        layout.addWidget(project_group)
        
        # Shotgrid 연결 상태 그룹
        status_group = QGroupBox("Shotgrid 연결 상태")
        status_layout = QVBoxLayout()
        
        self.connection_status_label = QLabel("확인 중...")
        status_layout.addWidget(self.connection_status_label)
        
        # 버튼들을 담을 QHBoxLayout 생성
        button_layout = QHBoxLayout()

        # 연결 테스트 버튼
        self.test_connection_btn = QPushButton("연결 테스트")
        self.test_connection_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_connection_btn)
        
        # 프로젝트 새로고침 버튼
        self.refresh_projects_btn = QPushButton("목록 새로고침")
        self.refresh_projects_btn.clicked.connect(self._load_projects)
        button_layout.addWidget(self.refresh_projects_btn)

        status_layout.addLayout(button_layout)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 초기 연결 상태 확인
        self._update_connection_status()
    
    def _load_current_settings(self):
        """현재 설정값들을 UI에 로드합니다."""
        try:
            # 현재 고정 프로젝트
            default_project = config.get("shotgrid", "default_project")
            
            # 자동 선택 옵션
            auto_select_str = config.get("shotgrid", "auto_select_project")
            auto_select = auto_select_str.lower() == 'true' if isinstance(auto_select_str, str) else True

            self.auto_select_cb.setChecked(auto_select)
            
            # 프로젝트 선택기 표시 옵션
            show_selector_str = config.get("shotgrid", "show_project_selector")
            show_selector = show_selector_str.lower() == 'true' if isinstance(show_selector_str, str) else False
            self.show_selector_cb.setChecked(show_selector)
            
            logger.debug(f"현재 설정 로드됨: project={default_project}, auto_select={auto_select}, show_selector={show_selector}")
            
            # 콤보박스에 현재 프로젝트 설정 (프로젝트 목록 로드 전이라도)
            if default_project:
                self.current_project_combo.setCurrentText(default_project)

        except Exception as e:
            logger.error(f"설정 로드 중 오류: {e}")
            # 기본값 설정
            self.auto_select_cb.setChecked(True)
            self.show_selector_cb.setChecked(False)
    
    def _load_projects(self):
        """Shotgrid에서 프로젝트 목록을 로드합니다."""
        if not SHOTGRID_AVAILABLE or not self.shotgrid_entity_manager:
            self.current_project_combo.clear()
            self.current_project_combo.addItem("ShotGrid 연결 안됨")
            return
        
        try:
            # 연결 상태 확인
            if not self.shotgrid_connector or not self.shotgrid_connector.is_connected():
                self.current_project_combo.clear()
                self.current_project_combo.addItem("ShotGrid 연결 안됨")
                return
            
            # 프로젝트 목록 가져오기
            self.projects = self.shotgrid_entity_manager.get_projects()
            
            # 콤보박스 업데이트
            current_text = config.get("shotgrid", "default_project") or ""
            self.current_project_combo.clear()
            
            project_names = [p['name'] for p in self.projects]
            self.current_project_combo.addItems(project_names)
            
            # 기존 선택값 복원
            if current_text in project_names:
                self.current_project_combo.setCurrentText(current_text)
            elif project_names:
                 self.current_project_combo.setCurrentIndex(0)
            
            logger.info(f"Shotgrid에서 {len(self.projects)}개 프로젝트 로드됨")
            
        except Exception as e:
            logger.error(f"프로젝트 목록 로드 중 오류: {e}")
            self.current_project_combo.clear()
            self.current_project_combo.addItem("목록 로드 실패")
    
    def _update_connection_status(self):
        """연결 상태를 업데이트합니다."""
        if not SHOTGRID_AVAILABLE:
            self.connection_status_label.setText("❌ Shotgrid 모듈을 사용할 수 없습니다")
            self.connection_status_label.setStyleSheet("color: #E74C3C;")
            self.test_connection_btn.setEnabled(False)
            self.refresh_projects_btn.setEnabled(False)
            return
        
        if not self.shotgrid_connector:
            self.connection_status_label.setText("❌ Shotgrid 커넥터를 초기화할 수 없습니다")
            self.connection_status_label.setStyleSheet("color: #E74C3C;")
            self.test_connection_btn.setEnabled(False)
            self.refresh_projects_btn.setEnabled(False)
            return
        
        try:
            if self.shotgrid_connector.is_connected():
                self.connection_status_label.setText("✅ Shotgrid에 연결됨")
                self.connection_status_label.setStyleSheet("color: #27AE60;")
                self.test_connection_btn.setEnabled(True)
                self.refresh_projects_btn.setEnabled(True)
            else:
                self.connection_status_label.setText("❌ Shotgrid에 연결되지 않음")
                self.connection_status_label.setStyleSheet("color: #E74C3C;")
                self.test_connection_btn.setEnabled(True)
                self.refresh_projects_btn.setEnabled(False)
        except Exception as e:
            self.connection_status_label.setText(f"❌ 연결 상태 확인 오류: {str(e)}")
            self.connection_status_label.setStyleSheet("color: #E74C3C;")
            self.test_connection_btn.setEnabled(True)
            self.refresh_projects_btn.setEnabled(False)
    
    def _test_connection(self):
        """Shotgrid 연결을 테스트합니다."""
        if not SHOTGRID_AVAILABLE or not self.shotgrid_connector:
            QMessageBox.warning(self, "경고", "Shotgrid 연결을 사용할 수 없습니다.")
            return
        
        try:
            # 연결 테스트
            if self.shotgrid_connector.test_connection():
                QMessageBox.information(self, "연결 테스트", "✅ Shotgrid 연결이 성공했습니다!")
                self._update_connection_status()
                self._load_projects()
            else:
                QMessageBox.warning(self, "연결 테스트", "❌ Shotgrid 연결에 실패했습니다.\n설정을 확인해주세요.")
                self._update_connection_status()
                
        except Exception as e:
            logger.error(f"연결 테스트 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"연결 테스트 중 오류가 발생했습니다:\n{str(e)}")
            self._update_connection_status()
    
    def _apply_settings(self):
        """설정을 적용합니다."""
        try:
            # 현재 UI 값들 가져오기
            project_name = self.current_project_combo.currentText().strip()
            auto_select = self.auto_select_cb.isChecked()
            show_selector = self.show_selector_cb.isChecked()
            
            # 입력 검증
            if not project_name or "연결" in project_name or "실패" in project_name:
                QMessageBox.warning(self, "경고", "유효한 프로젝트를 선택해주세요.")
                return
            
            # 설정 저장
            config.set("shotgrid", "default_project", project_name)
            config.set("shotgrid", "auto_select_project", str(auto_select))
            config.set("shotgrid", "show_project_selector", str(show_selector))
            
            logger.info(f"프로젝트 설정 저장됨: {project_name}, auto_select={auto_select}, show_selector={show_selector}")
            QMessageBox.information(self, "저장됨", "설정이 적용되었습니다.")
            
        except Exception as e:
            logger.error(f"설정 저장 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def accept(self):
        """OK 버튼 클릭 시 설정 저장 후 대화상자 닫기."""
        self._apply_settings()
        super().accept()

    def get_settings(self):
        """현재 UI에 설정된 값들을 반환합니다."""
        return {
            "project_name": self.current_project_combo.currentText(),
            "auto_select": self.auto_select_cb.isChecked(),
            "show_selector": self.show_selector_cb.isChecked()
        }
