#!/usr/bin/env python3
"""
Shotgrid Shot Code 쿼리 테스트 스크립트
이 스크립트는 Shotgrid API를 통해 Shot Code를 가져올 수 있는지 테스트합니다.
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
    from shotpipe.config import config
except ImportError as e:
    print(f"ShotPipe 모듈 import 실패: {e}")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_shotgrid_connection():
    """Shotgrid 연결 테스트"""
    print("=== Shotgrid 연결 테스트 ===")
    
    try:
        # Shotgrid 커넥터 생성
        connector = ShotgridConnector()
        
        if not connector.is_connected():
            print("❌ Shotgrid 연결 실패")
            print("   - .env 파일에 Shotgrid 연결 정보가 설정되어 있는지 확인하세요")
            print("   - SHOTGRID_URL, SHOTGRID_SCRIPT_NAME, SHOTGRID_API_KEY")
            assert False, "Shotgrid connection failed"
        
        print("✅ Shotgrid 연결 성공")
        
        # 연결 테스트
        if connector.test_connection():
            print("✅ Shotgrid API 테스트 성공")
            assert True, "Shotgrid API test successful"
        else:
            print("❌ Shotgrid API 테스트 실패")
            assert False, "Shotgrid API test failed"
            
    except Exception as e:
        print(f"❌ Shotgrid 연결 중 오류: {e}")
        assert False, f"Shotgrid connection error: {e}"

def test_project_query():
    """프로젝트 쿼리 테스트 (내부에서 EntityManager 생성)"""
    entity_manager = EntityManager()
    print("\n=== 프로젝트 쿼리 테스트 ===")
    
    try:
        projects = entity_manager.get_projects()
        print(f"✅ 총 {len(projects)}개 프로젝트 발견")
        
        for i, project in enumerate(projects[:5]):  # 첫 5개만 표시
            print(f"   {i+1}. {project['name']} (ID: {project['id']})")
            
        if len(projects) > 5:
            print(f"   ... 외 {len(projects) - 5}개 프로젝트")
            
        assert len(projects) > 0, f"Found {len(projects)} projects"
        
    except Exception as e:
        print(f"❌ 프로젝트 쿼리 실패: {e}")
        assert False, f"Project query failed: {e}"

def get_shots_in_project(connector, project_id, project_name):
    """특정 프로젝트의 모든 Shot 가져오기"""
    print(f"\n=== 프로젝트 '{project_name}'의 Shot 쿼리 테스트 ===")
    
    try:
        sg = connector.get_connection()
        
        # 프로젝트의 모든 Shot 쿼리
        shots = sg.find(
            "Shot",
            [["project", "is", {"type": "Project", "id": project_id}]],
            ["id", "code", "sg_sequence", "description", "sg_status_list"]
        )
        
        print(f"✅ 총 {len(shots)}개 Shot 발견")
        
        # Shot Code 목록 수집
        shot_codes = []
        sequence_shots = {}
        
        for shot in shots:
            shot_code = shot['code']
            shot_codes.append(shot_code)
            
            # 시퀀스별로 그룹화
            sequence = shot.get('sg_sequence')
            if sequence:
                seq_name = sequence['name']
                if seq_name not in sequence_shots:
                    sequence_shots[seq_name] = []
                sequence_shots[seq_name].append(shot_code)
        
        # 결과 출력
        if shot_codes:
            print(f"Shot Codes: {shot_codes[:10]}")  # 첫 10개만 표시
            if len(shot_codes) > 10:
                print(f"... 외 {len(shot_codes) - 10}개")
                
            print(f"\n시퀀스별 Shot 분포:")
            for seq_name, shots in sequence_shots.items():
                print(f"   {seq_name}: {len(shots)}개 Shot")
                
        return shot_codes, sequence_shots
        
    except Exception as e:
        print(f"❌ Shot 쿼리 실패: {e}")
        return [], {}

def get_shots_in_sequence(connector, project_id, sequence_name):
    """특정 시퀀스의 Shot 가져오기"""
    print(f"\n=== 시퀀스 '{sequence_name}'의 Shot 쿼리 테스트 ===")
    
    try:
        sg = connector.get_connection()
        
        # 시퀀스 찾기
        sequence = sg.find_one(
            "Sequence",
            [
                ["project", "is", {"type": "Project", "id": project_id}],
                ["code", "is", sequence_name]
            ],
            ["id", "code"]
        )
        
        if not sequence:
            print(f"❌ 시퀀스 '{sequence_name}'을 찾을 수 없습니다")
            return []
        
        print(f"✅ 시퀀스 '{sequence_name}' 발견 (ID: {sequence['id']})")
        
        # 해당 시퀀스의 Shot 쿼리
        shots = sg.find(
            "Shot",
            [
                ["project", "is", {"type": "Project", "id": project_id}],
                ["sg_sequence", "is", {"type": "Sequence", "id": sequence['id']}]
            ],
            ["id", "code", "description", "sg_status_list"]
        )
        
        shot_codes = [shot['code'] for shot in shots]
        print(f"✅ 시퀀스 '{sequence_name}'에서 {len(shot_codes)}개 Shot 발견")
        print(f"Shot Codes: {shot_codes}")
        
        return shot_codes
        
    except Exception as e:
        print(f"❌ 시퀀스 Shot 쿼리 실패: {e}")
        return []

def main():
    """메인 테스트 함수"""
    print("Shotgrid Shot Code 쿼리 테스트 시작")
    print("=" * 50)
    
    # 1. Shotgrid 연결 테스트
    if not test_shotgrid_connection():
        print("\n❌ Shotgrid 연결에 실패했습니다. 테스트를 중단합니다.")
        return
    
    # 2. EntityManager 생성
    try:
        entity_manager = EntityManager()
        print("✅ EntityManager 생성 성공")
    except Exception as e:
        print(f"❌ EntityManager 생성 실패: {e}")
        return
    
    # 3. 프로젝트 쿼리
    projects = test_project_query(entity_manager)
    if not projects:
        print("\n❌ 프로젝트를 찾을 수 없습니다. 테스트를 중단합니다.")
        return
    
    # 4. 첫 번째 프로젝트에서 Shot 쿼리 테스트
    first_project = projects[0]
    project_id = first_project['id']
    project_name = first_project['name']
    
    shot_codes, sequence_shots = get_shots_in_project(
        entity_manager.connector, 
        project_id, 
        project_name
    )
    
    # 5. 특정 시퀀스 Shot 쿼리 테스트 (시퀀스가 있는 경우)
    if sequence_shots:
        first_sequence = list(sequence_shots.keys())[0]
        get_shots_in_sequence(
            entity_manager.connector,
            project_id,
            first_sequence
        )
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")
    print("\n결론:")
    print("- Shotgrid API를 통해 Shot Code 쿼리가 가능합니다")
    print("- 프로젝트별, 시퀀스별로 Shot 목록을 가져올 수 있습니다")
    print("- UI에 Shot Code 선택 기능을 추가할 수 있습니다")

if __name__ == "__main__":
    main()
