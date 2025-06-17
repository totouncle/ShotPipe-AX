#!/usr/bin/env python3
"""
ShotPipe 고정 프로젝트 기능 테스트 스크립트

이 스크립트는 새로 추가된 고정 프로젝트 기능들을 테스트합니다:
1. 고정 프로젝트 설정 로드/저장
2. 프로젝트 설정 다이얼로그
3. Shotgrid 연동 상태 확인
4. 시퀀스/샷 편집 기능
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_config():
    """설정 기능 테스트"""
    print("=" * 50)
    print("1. 설정 기능 테스트")
    print("=" * 50)
    
    try:
        from shotpipe.config import config
        
        # 현재 설정 출력
        print(f"현재 고정 프로젝트: {config.get('shotgrid', 'default_project')}")
        print(f"자동 선택: {config.get('shotgrid', 'auto_select_project')}")
        print(f"프로젝트 선택기 표시: {config.get('shotgrid', 'show_project_selector')}")
        
        # 설정 변경 테스트
        print("\n설정 변경 테스트...")
        original_project = config.get('shotgrid', 'default_project')
        config.set('shotgrid', 'default_project', 'TEST-PROJECT')
        print(f"변경된 프로젝트: {config.get('shotgrid', 'default_project')}")
        
        # 원래 설정 복원
        config.set('shotgrid', 'default_project', original_project)
        print(f"복원된 프로젝트: {config.get('shotgrid', 'default_project')}")
        
        print("✅ 설정 기능 테스트 통과")
        
    except Exception as e:
        print(f"❌ 설정 기능 테스트 실패: {e}")
        logger.error(f"설정 테스트 오류: {e}", exc_info=True)

def test_shotgrid_connection():
    """Shotgrid 연결 테스트"""
    print("\n" + "=" * 50)
    print("2. Shotgrid 연결 테스트")
    print("=" * 50)
    
    try:
        from shotpipe.shotgrid.api_connector import ShotgridConnector
        from shotpipe.shotgrid.entity_manager import EntityManager
        
        print("Shotgrid 커넥터 초기화 중...")
        connector = ShotgridConnector()
        
        if connector.is_connected():
            print("✅ Shotgrid 연결 성공")
            
            # 엔티티 매니저 테스트
            entity_manager = EntityManager(connector)
            
            # 프로젝트 목록 가져오기
            projects = entity_manager.get_projects()
            print(f"✅ {len(projects)}개 프로젝트 발견")
            
            # 처음 3개 프로젝트만 표시
            for i, project in enumerate(projects[:3]):
                print(f"  - {project['name']} (ID: {project['id']})")
            
            if len(projects) > 3:
                print(f"  ... 외 {len(projects) - 3}개 프로젝트")
                
            # 기본 프로젝트 찾기
            from shotpipe.config import config
            default_project_name = config.get('shotgrid', 'default_project')
            default_project = entity_manager.find_project(default_project_name)
            
            if default_project:
                print(f"✅ 기본 프로젝트 '{default_project_name}' 발견 (ID: {default_project['id']})")
                
                # 시퀀스 목록 가져오기
                sequences = entity_manager.get_sequences_in_project(default_project)
                print(f"✅ {len(sequences)}개 시퀀스 발견")
                
                for i, seq in enumerate(sequences[:3]):
                    print(f"  - {seq['code']}")
                
                if len(sequences) > 3:
                    print(f"  ... 외 {len(sequences) - 3}개 시퀀스")
                    
            else:
                print(f"⚠️ 기본 프로젝트 '{default_project_name}'을 찾을 수 없음")
                
        else:
            print("❌ Shotgrid 연결 실패")
            print("환경 변수를 확인하세요:")
            print("  - SHOTGRID_URL")
            print("  - SHOTGRID_SCRIPT_NAME")
            print("  - SHOTGRID_API_KEY")
            
    except ImportError:
        print("⚠️ Shotgrid 모듈을 사용할 수 없습니다")
    except Exception as e:
        print(f"❌ Shotgrid 연결 테스트 실패: {e}")
        logger.error(f"Shotgrid 테스트 오류: {e}", exc_info=True)

def test_ui_imports():
    """UI 모듈 import 테스트"""
    print("\n" + "=" * 50)
    print("3. UI 모듈 Import 테스트")
    print("=" * 50)
    
    ui_modules = [
        ('shotpipe.ui.main_window', 'MainWindow'),
        ('shotpipe.ui.file_tab', 'FileTab'),
        ('shotpipe.ui.shotgrid_tab', 'ShotgridTab'),
        ('shotpipe.ui.project_settings_dialog', 'ProjectSettingsDialog'),
        ('shotpipe.ui.about_dialog', 'AboutDialog'),
    ]
    
    for module_name, class_name in ui_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")

def test_task_assignment():
    """자동 태스크 할당 테스트"""
    print("\n" + "=" * 50)
    print("4. 자동 태스크 할당 테스트")
    print("=" * 50)
    
    try:
        from shotpipe.ui.file_tab import FileTab
        
        # FileTab 인스턴스 생성 (UI 없이)
        file_tab = FileTab()
        
        # 테스트 파일 경로들
        test_files = [
            "/path/to/image.png",
            "/path/to/video.mp4", 
            "/path/to/audio.wav",
            "/path/to/model.obj",
            "/path/to/unknown.xyz"
        ]
        
        for file_path in test_files:
            task = file_tab._assign_task_automatically(file_path)
            file_ext = os.path.splitext(file_path)[1]
            print(f"  {file_ext} → {task}")
        
        print("✅ 자동 태스크 할당 테스트 통과")
        
    except Exception as e:
        print(f"❌ 자동 태스크 할당 테스트 실패: {e}")
        logger.error(f"태스크 할당 테스트 오류: {e}", exc_info=True)

def main():
    """메인 테스트 함수"""
    print("ShotPipe 고정 프로젝트 기능 테스트")
    print("=" * 60)
    
    # 각 테스트 실행
    test_config()
    test_shotgrid_connection()
    test_ui_imports()
    test_task_assignment()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("\nUI를 실제로 테스트하려면 다음 명령을 실행하세요:")
    print("  python main.py")
    print("\n새로운 기능들:")
    print("  1. 설정 → 프로젝트 설정... (Ctrl+,)")
    print("  2. 파일 처리 탭의 '프로젝트 설정' 버튼")
    print("  3. 시퀀스/샷 컬럼 더블클릭으로 Shotgrid에서 선택")
    print("  4. 고정 프로젝트가 자동으로 로드됨")

if __name__ == "__main__":
    main()
