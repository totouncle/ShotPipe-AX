#!/usr/bin/env python3
"""
특정 시퀀스 Shot 테스트 - s01 시퀀스 확인
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

def test_sequence_with_shots():
    """Shot이 있는 시퀀스로 테스트"""
    print("=== Shot이 있는 시퀀스 테스트 ===")
    
    try:
        entity_manager = EntityManager()
        
        if not entity_manager.connector.is_connected():
            print("❌ Shotgrid 연결 실패")
            return False
        
        # TEST-1 프로젝트 가져오기
        project = entity_manager.find_project("TEST-1")
        if not project:
            print("❌ TEST-1 프로젝트를 찾을 수 없습니다")
            return False
        
        print(f"✅ 프로젝트 '{project['name']}' 발견")
        
        # s01 시퀀스 테스트 (앞서 테스트에서 4개 Shot이 있다고 확인됨)
        sequence_code = "s01"
        print(f"\n시퀀스 '{sequence_code}' 테스트:")
        
        shots = entity_manager.get_shots_in_sequence(project, sequence_code)
        print(f"✅ 시퀀스 '{sequence_code}'에서 {len(shots)}개 Shot 발견")
        
        if shots:
            shot_codes = [shot['code'] for shot in shots]
            print(f"Shot Codes: {shot_codes}")
            
            # 첫 번째 Shot으로 워크플로우 완료 테스트
            selected_shot = shots[0]
            selected_shot_code = selected_shot['code']
            
            print(f"\n✅ 워크플로우 테스트 완료:")
            print(f"   프로젝트: {project['name']}")
            print(f"   시퀀스: {sequence_code}")
            print(f"   Shot: {selected_shot_code}")
            
            # 가상 파일에 적용 시뮬레이션
            mock_files = [
                {"file_name": "ai_image_001.png", "sequence": "", "shot": ""},
                {"file_name": "ai_video_001.mp4", "sequence": "", "shot": ""}
            ]
            
            print(f"\n파일에 적용 시뮬레이션:")
            for file_info in mock_files:
                file_info["sequence"] = sequence_code
                file_info["shot"] = selected_shot_code
                print(f"   '{file_info['file_name']}' → {sequence_code}/{selected_shot_code}")
            
            assert True, f"Sequence '{sequence_code}' has shots"
        else:
            print(f"❌ 시퀀스 '{sequence_code}'에 Shot이 없습니다")
            assert False, f"Sequence '{sequence_code}' has no shots"
            
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test error: {e}"

def test_all_sequences():
    """모든 시퀀스를 확인해서 Shot이 있는 시퀀스 찾기"""
    print("\n=== 모든 시퀀스 Shot 확인 ===")
    
    try:
        entity_manager = EntityManager()
        project = entity_manager.find_project("TEST-1")
        
        if not project:
            return False
        
        sequences = entity_manager.get_sequences_in_project(project)
        sequences_with_shots = []
        
        for sequence in sequences:
            seq_code = sequence['code']
            shots = entity_manager.get_shots_in_sequence(project, seq_code)
            shot_count = len(shots)
            
            if shot_count > 0:
                sequences_with_shots.append((seq_code, shot_count))
                shot_codes = [shot['code'] for shot in shots[:3]]  # 첫 3개만
                print(f"✅ {seq_code}: {shot_count}개 Shot ({shot_codes}{'...' if shot_count > 3 else ''})")
            else:
                print(f"   {seq_code}: Shot 없음")
        
        print(f"\n결과: {len(sequences_with_shots)}개 시퀀스에 Shot이 있습니다")
        assert len(sequences_with_shots) > 0, f"Found {len(sequences_with_shots)} sequences with shots"
        
    except Exception as e:
        print(f"❌ 시퀀스 확인 중 오류: {e}")
        assert False, f"Sequence check error: {e}"

def main():
    """메인 테스트"""
    print("특정 시퀀스 Shot 테스트 시작")
    print("=" * 50)
    
    # s01 시퀀스 테스트
    success1 = test_sequence_with_shots()
    
    # 모든 시퀀스 확인
    sequences_with_shots = test_all_sequences()
    
    print("\n" + "=" * 50)
    if success1:
        print("✅ Shot이 있는 시퀀스를 발견했습니다!")
        print("UI에서 프로젝트/시퀀스/Shot 선택 기능이 정상 작동할 것입니다.")
    else:
        print("⚠️ s01 시퀀스에서 Shot을 찾지 못했지만...")
        if sequences_with_shots:
            print(f"다른 시퀀스들에서 {len(sequences_with_shots)}개 시퀀스에 Shot이 있습니다.")
            print("UI 기능은 정상 작동할 것입니다.")

if __name__ == "__main__":
    main()
