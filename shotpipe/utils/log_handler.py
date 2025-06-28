"""
로그 핸들러 모듈
"""
import logging

class QTextEditLogger(logging.Handler):
    """로그 메시지를 QTextEdit으로 리다이렉트하는 로그 핸들러"""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
    def emit(self, record):
        msg = self.format(record)
        
        # 이모지와 색상을 사용한 로그 레벨 구분
        if record.levelno >= logging.ERROR:
            msg = f'<span style="color: #FF4444; font-weight: bold;">❌ {msg}</span>'
        elif record.levelno >= logging.WARNING:
            msg = f'<span style="color: #FFB347; font-weight: bold;">⚠️ {msg}</span>'
        elif record.levelno >= logging.INFO:
            # 진행 상황 관련 로그는 더 눈에 띄게
            if any(keyword in msg for keyword in ['🚀', '📋', '📁', '✅', '🎉', '⏳']):
                msg = f'<span style="color: #00FF88; font-weight: bold;">{msg}</span>'
            else:
                msg = f'<span style="color: #7CE8E6;">{msg}</span>'
        elif record.levelno >= logging.DEBUG:
            msg = f'<span style="color: #9B9B9B;">{msg}</span>'
        
        self.text_edit.append(msg)
        # 스크롤을 항상 최신 로그로 이동 (개선된 방식)
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # 스크롤이 제대로 작동하도록 약간의 딩레이 추가
        self.text_edit.ensureCursorVisible() 