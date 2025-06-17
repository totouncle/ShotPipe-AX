"""
Manual dialog for ShotPipe application.
사용자 매뉴얼을 표시하는 다이얼로그
"""
import os
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QTabWidget, QWidget, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

logger = logging.getLogger(__name__)

class ManualDialog(QDialog):
    """사용자 매뉴얼을 표시하는 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ShotPipe 사용자 매뉴얼")
        self.setModal(True)
        self.resize(1000, 700)
        
        self._init_ui()
        self._load_manual_content()
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def _load_manual_content(self):
        """매뉴얼 콘텐츠 로드"""
        try:
            # 애플리케이션 루트 디렉토리에서 문서 찾기
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # PRD 문서 로드
            prd_path = os.path.join(app_root, "ShotPipe - AI 생성 파일 자동화 Shotgrid 업로드 솔루션 PRD.md")
            if os.path.exists(prd_path):
                self._add_manual_tab("제품 개요", prd_path)
            
            # 태스크 매핑 문서 로드
            mapping_path = os.path.join(app_root, "AI 서비스 태스크 매핑 표.md")
            if os.path.exists(mapping_path):
                self._add_manual_tab("태스크 매핑", mapping_path)
            
            # 사용법 가이드 탭 추가
            self._add_usage_guide_tab()
            
            # 단축키 가이드 탭 추가
            self._add_shortcuts_tab()
            
        except Exception as e:
            logger.error(f"매뉴얼 콘텐츠 로드 중 오류: {e}")
            self._add_error_tab()
    
    def _add_manual_tab(self, title, file_path):
        """매뉴얼 탭 추가"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 텍스트 에디트 위젯 생성
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(content)
            
            # 마크다운 스타일 폰트 설정
            font = QFont("Consolas", 10)
            text_edit.setFont(font)
            
            self.tab_widget.addTab(text_edit, title)
            
        except Exception as e:
            logger.error(f"매뉴얼 탭 추가 중 오류 ({file_path}): {e}")
    
    def _add_usage_guide_tab(self):
        """사용법 가이드 탭 추가"""
        usage_content = """
# ShotPipe 사용법 가이드

## 1. 기본 워크플로우

### 파일 처리 단계
1. **소스 디렉토리 선택**: AI 생성 파일들이 있는 폴더를 선택합니다
2. **출력 폴더 설정**: 처리된 파일들이 저장될 위치를 지정합니다
3. **파일 스캔**: 선택한 디렉토리에서 지원되는 미디어 파일을 검색합니다
4. **파일 선택**: 처리할 파일들을 선택합니다
5. **시퀀스 설정**: 파일들이 속할 시퀀스를 설정합니다
6. **처리 실행**: 선택한 파일들을 처리하여 Shotgrid 업로드 준비를 완료합니다

### Shotgrid 업로드 단계
1. **연결 설정**: Shotgrid 서버 연결을 확인하고 설정합니다
2. **파일 확인**: 처리된 파일 목록을 확인합니다
3. **태스크 수정**: 필요시 자동 할당된 태스크를 수정합니다
4. **업로드 실행**: 선택한 파일들을 Shotgrid에 업로드합니다

## 2. 주요 기능

### 자동 태스크 할당
- **이미지 파일**: txtToImage (텍스트-이미지 생성)
- **비디오 파일**: imgToVideo (이미지-비디오 변환)
- **기타 파일**: comp (컴포지팅)

### 시퀀스 관리
- 자동 감지: 파일명에서 시퀀스 정보를 자동으로 추출
- 수동 설정: 사용자가 직접 시퀀스를 입력하고 저장
- 최근 사용: 최근에 사용한 시퀀스를 기억하여 빠른 선택 가능

### 파일 이력 관리
- 처리된 파일 추적: 중복 처리 방지
- 이력 통계: 처리된 파일들의 통계 정보 제공
- 이력 내보내기: CSV 형태로 이력 데이터 내보내기

## 3. 옵션 설정

### 파일 처리 옵션
- **하위 폴더 포함**: 선택한 디렉토리의 하위 폴더까지 스캔
- **이미 처리된 파일 제외**: 이전에 처리된 파일들을 스캔에서 제외
- **processed 폴더 생성**: 처리된 파일을 별도 폴더에 저장

### 업로드 옵션
- **파일 타입 필터**: 이미지, 비디오 파일별로 필터링
- **선택적 업로드**: 원하는 파일만 선택하여 업로드

## 4. 문제 해결

### 일반적인 문제
- **파일이 스캔되지 않음**: 지원되는 파일 형식인지 확인 (.png, .jpg, .mp4, .mov 등)
- **시퀀스가 감지되지 않음**: 파일명이 표준 명명 규칙을 따르는지 확인
- **업로드 실패**: Shotgrid 연결 설정과 권한을 확인

### 로그 확인
- 하단의 로그 창에서 자세한 오류 정보를 확인할 수 있습니다
- 문제 발생 시 로그 내용을 참고하여 문제를 해결하세요

## 5. 팁과 트릭

### 효율적인 사용법
- **배치 처리**: 비슷한 시퀀스의 파일들을 함께 처리
- **태스크 미리 확인**: 자동 할당된 태스크가 올바른지 처리 전에 확인
- **정기적인 이력 정리**: 이력이 너무 많이 쌓이면 성능에 영향을 줄 수 있음

### 명명 규칙 권장사항
- 파일명: `[시퀀스]_c001_[태스크]_v0001.확장자`
- 예시: `LIG_c001_txtToImage_v0001.png`
        """
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMarkdown(usage_content)
        
        self.tab_widget.addTab(text_edit, "사용법")
    
    def _add_shortcuts_tab(self):
        """단축키 가이드 탭 추가"""
        shortcuts_content = """
# ShotPipe 단축키 가이드

## 파일 처리 탭

### 파일 관리
- **Ctrl + O**: 소스 디렉토리 선택
- **F5**: 파일 스캔 새로고침
- **Ctrl + A**: 모든 파일 선택
- **Ctrl + D**: 모든 파일 선택 해제
- **Ctrl + U**: 미처리 파일만 선택

### 시퀀스 관리
- **Ctrl + S**: 현재 시퀀스 저장
- **Ctrl + R**: 최근 시퀀스 불러오기

### 처리 작업
- **F9**: 파일 처리 시작/중지
- **Ctrl + N**: 새 배치 시작

## Shotgrid 업로드 탭

### 파일 관리
- **Ctrl + L**: 처리된 파일 로드
- **Ctrl + Shift + L**: 파일에서 로드

### 필터링
- **F1**: 모든 파일 표시
- **F2**: 이미지 파일만 표시
- **F3**: 비디오 파일만 표시

### 업로드
- **F10**: Shotgrid 업로드 시작
- **Ctrl + T**: 연결 테스트

## 전역 단축키

### 일반
- **F1**: 도움말 (이 창)
- **Ctrl + Q**: 애플리케이션 종료
- **Ctrl + ,**: 설정 열기

### 로그 관리
- **Ctrl + Shift + C**: 로그 지우기
- **Ctrl + Shift + S**: 로그 저장

### 창 관리
- **Ctrl + Tab**: 탭 전환
- **F11**: 전체화면 전환
- **Esc**: 대화상자 닫기

## 마우스 동작

### 테이블 조작
- **더블클릭**: 파일 세부 정보 보기
- **우클릭**: 컨텍스트 메뉴 열기
- **Shift + 클릭**: 범위 선택
- **Ctrl + 클릭**: 다중 선택

### 헤더 조작
- **드래그**: 컬럼 너비 조절
- **우클릭**: 컬럼 옵션 메뉴
- **더블클릭**: 컬럼 자동 크기 조절

## 팁

- 대부분의 작업은 마우스로도 쉽게 할 수 있습니다
- 단축키를 외우면 작업 속도가 크게 향상됩니다
- 툴팁을 보려면 버튼 위에 마우스를 올려놓으세요
        """
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMarkdown(shortcuts_content)
        
        self.tab_widget.addTab(text_edit, "단축키")
    
    def _add_error_tab(self):
        """오류 발생 시 기본 탭 추가"""
        error_content = """
# ShotPipe 매뉴얼

매뉴얼 파일을 로드하는 중 오류가 발생했습니다.

## 기본 사용법

1. **파일 처리**: 왼쪽 탭에서 AI 생성 파일들을 처리합니다
2. **Shotgrid 업로드**: 오른쪽 탭에서 처리된 파일들을 Shotgrid에 업로드합니다

## 도움이 필요하시면

- 로그 창을 확인하여 자세한 오류 정보를 확인하세요
- 개발팀에 문의하시기 바랍니다
        """
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(error_content)
        
        self.tab_widget.addTab(text_edit, "매뉴얼")
