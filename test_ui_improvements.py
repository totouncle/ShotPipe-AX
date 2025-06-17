#!/usr/bin/env python3
"""
Shotgrid UI 개선 기능 테스트 스크립트
새로 추가된 프로젝트/시퀀스/Shot 선택 기능을 테스트합니다.
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ShotPipe 모듈 import
try:
    from shotpipe.shotgrid.api_connector import ShotgridConnector
    from shotpipe.shotgrid.entity_manager import EntityManager
except ImportError as e:
    print(f"ShotPipe 모듈 import 실패: {e}")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_entity_manager():
    """향상된 EntityManager 기능 테스트"""
    print("=== 향상된 EntityManager 기능 테스트 ===")
    
    try:
        # EntityManager 생성
        entity_manager = EntityManager()
        
        if not entity_manager.connector.is_connected():
            print("❌ Shotgrid 연결 실패")
            return False
        
        print("✅ Shotgrid 연결 성공")
        
        # 1. 프로젝트 목록 가져오기
        print("\n1. 프로젝트 목록 테스트")
        projects = entity_manager.get_projects()
        print(f"✅ 총 {len(projects)}개 프로젝트 발견")
        
        if not projects:
            print("❌ 프로젝트가 없습니다")
            return False
        
        # 첫 번째 프로젝트 선택
        first_project = projects[0]
        project_name = first_project['name']
        print(f"테스트 대상 프로젝트: {project_name}")
        
        # 2. 시퀀스 목록 가져오기 테스트
        print(f"\n2. 프로젝트 '{project_name}'의 시퀀스 목록 테스트")
        sequences = entity_manager.get_sequences_in_project(first_project)
        print(f"✅ 총 {len(sequences)}개 시퀀스 발견")
        
        for i, seq in enumerate(sequences[:5]):  # 첫 5개만 표시
            print(f"   {i+1}. {seq['code']} (ID: {seq['id']})")
        
        if len(sequences) > 5:
            print(f"   ... 외 {len(sequences) - 5}개 시퀀스")
        
        # 3. 프로젝트의 모든 Shot 가져오기 테스트
        print(f"\n3. 프로젝트 '{project_name}'의 모든 Shot 테스트")
        all_shots = entity_manager.get_shots_in_project(first_project, limit=20)
        print(f"✅ 총 {len(all_shots)}개 Shot 발견 (최대 20개 표시)")
        
        shot_codes = [shot['code'] for shot in all_shots]
        print(f"Shot Codes: {shot_codes[:10]}")  # 첫 10개만 표시
        if len(shot_codes) > 10:
            print(f"... 외 {len(shot_codes) - 10}개")
        
        # 4. 특정 시퀀스의 Shot 가져오기 테스트
        if sequences:
            first_sequence = sequences[0]
            sequence_code = first_sequence['code']
            
            print(f"\n4. 시퀀스 '{sequence_code}'의 Shot 테스트")
            sequence_shots = entity_manager.get_shots_in_sequence(first_project, sequence_code)
            print(f"✅ 시퀀스 '{sequence_code}'에서 {len(sequence_shots)}개 Shot 발견")
            
            seq_shot_codes = [shot['code'] for shot in sequence_shots]
            print(f"Shot Codes: {seq_shot_codes}")
            
            # 5. get_available_shot_codes 메서드 테스트
            print(f"\n5. 사용 가능한 Shot Code 목록 테스트")
            available_shots = entity_manager.get_available_shot_codes(project_name, sequence_code)
            print(f"✅ 시퀀스 '{sequence_code}'에서 사용 가능한 {len(available_shots)}개 Shot Code")
            print(f"Available Shot Codes: {available_shots}")
            
            # 전체 프로젝트 Shot Code도 테스트
            all_available_shots = entity_manager.get_available_shot_codes(project_name)
            print(f"✅ 프로젝트 전체에서 사용 가능한 {len(all_available_shots)}개 Shot Code")
            print(f"All Available Shot Codes: {all_available_shots[:10]}")  # 첫 10개만
            if len(all_available_shots) > 10:
                print(f"... 외 {len(all_available_shots) - 10}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_workflow_simulation():
    """UI 워크플로우 시뮬레이션 테스트"""
    print("\n=== UI 워크플로우 시뮬레이션 ===")
    
    try:
        entity_manager = EntityManager()
        
        if not entity_manager.connector.is_connected():
            print("❌ Shotgrid 연결 실패")
            return False
        
        # 시나리오: 사용자가 UI에서 프로젝트를 선택하는 과정 시뮬레이션
        print("시나리오: 사용자 UI 워크플로우 시뮬레이션")
        
        # 1. 프로젝트 목록 로드 (UI의 refresh_projects와 동일)
        print("\n1단계: 프로젝트 목록 로드")
        projects = entity_manager.get_projects()
        project_options = ["-- 프로젝트 선택 --"] + [p['name'] for p in projects]
        print(f"프로젝트 옵션: {project_options[:5]}...")  # 처음 5개만 표시
        
        # 2. 사용자가 프로젝트 선택 (첫 번째 실제 프로젝트 선택)
        if len(projects) > 0:
            selected_project = projects[0]
            selected_project_name = selected_project['name']
            print(f"\n2단계: 사용자가 '{selected_project_name}' 프로젝트 선택")
            
            # 3. 시퀀스 목록 로드 (UI의 on_project_changed와 동일)
            print("3단계: 시퀀스 목록 로드")
            sequences = entity_manager.get_sequences_in_project(selected_project)
            sequence_options = ["-- 시퀀스 선택 --"] + [s['code'] for s in sequences]
            print(f"시퀀스 옵션: {sequence_options}")
            
            # 4. 사용자가 시퀀스 선택
            if len(sequences) > 0:
                selected_sequence = sequences[0]
                selected_sequence_code = selected_sequence['code']
                print(f"\n4단계: 사용자가 '{selected_sequence_code}' 시퀀스 선택")
                
                # 5. Shot 목록 로드 (UI의 on_sequence_changed와 동일)
                print("5단계: Shot 목록 로드")
                shots = entity_manager.get_shots_in_sequence(selected_project, selected_sequence_code)
                shot_options = ["-- Shot 선택 --"] + [s['code'] for s in shots]
                print(f"Shot 옵션: {shot_options}")
                
                # 6. 사용자가 Shot 선택하여 파일에 적용하는 시뮬레이션
                if len(shots) > 0:
                    selected_shot = shots[0]
                    selected_shot_code = selected_shot['code']
                    print(f"\n6단계: 사용자가 '{selected_shot_code}' Shot 선택")
                    
                    # 가상의 파일 정보 생성
                    mock_files = [
                        {"file_name": "test_image_01.png", "sequence": "", "shot": ""},
                        {"file_name": "test_video_01.mp4", "sequence": "", "shot": ""},
                        {"file_name": "test_render_01.exr", "sequence": "", "shot": ""}
                    ]
                    
                    print("7단계: 선택된 파일들에 시퀀스/Shot 적용")
                    for file_info in mock_files:
                        file_info["sequence"] = selected_sequence_code
                        file_info["shot"] = selected_shot_code
                        print(f"   파일 '{file_info['file_name']}' → {selected_sequence_code}/{selected_shot_code}")
                    
                    print("✅ UI 워크플로우 시뮬레이션 성공!")
                    return True
        
        print("❌ 충분한 데이터가 없어 전체 워크플로우를 완료할 수 없습니다")
        return False
        
    except Exception as e:
        print(f"❌ UI 워크플로우 시뮬레이션 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("Shotgrid UI 개선 기능 테스트 시작")
    print("=" * 60)
    
    success1 = test_enhanced_entity_manager()
    success2 = test_ui_workflow_simulation()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ 모든 테스트 통과!")
        print("\n새로 추가된 기능:")
        print("- ✅ 프로젝트 선택 드롭다운")
        print("- ✅ 시퀀스 선택 드롭다운") 
        print("- ✅ Shot Code 선택 및 일괄 적용")
        print("- ✅ 테이블에서 시퀀스/Shot/태스크 직접 편집")
        print("- ✅ 동적 데이터 로딩 (프로젝트 → 시퀀스 → Shot)")
    else:
        print("❌ 일부 테스트 실패")
        print("Shotgrid 연결 상태를 확인하세요.")

if __name__ == "__main__":
    main()
