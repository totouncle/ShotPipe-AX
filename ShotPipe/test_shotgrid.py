#!/usr/bin/env python
"""
Shotgrid API 연결 테스트 스크립트
"""
import os
import sys
import logging
import xmlrpc.client
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('shotgrid_test')

# 환경 변수 로드
load_dotenv()

# Six 문제 해결을 위한 임시 조치
import six
import importlib

# xmlrpc_client patching
sys.modules['xmlrpc.client'] = xmlrpc.client
sys.modules['shotgun_api3.lib.six'] = six
sys.modules['shotgun_api3.lib.six.moves'] = six.moves
sys.modules['shotgun_api3.lib.six.moves.xmlrpc_client'] = xmlrpc.client

logger.info("모듈 패치 완료")

# Python API를 상대 경로에서 확인
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 먼저 직접 필요한 모듈을 가져와 봅니다
    logger.info("직접 shotgun_api3 내부 모듈 import 시도...")
    import shotgun_api3
    logger.info("shotgun_api3 모듈을 성공적으로 가져왔습니다. 버전: %s", getattr(shotgun_api3, '__version__', 'unknown'))
except ImportError as e:
    logger.error("shotgun_api3 모듈을 가져오지 못했습니다: %s", e)
    sys.exit(1)

# Shotgrid 연결 정보
server_url = os.getenv('SHOTGRID_URL')
script_name = os.getenv('SHOTGRID_SCRIPT_NAME')
api_key = os.getenv('SHOTGRID_API_KEY')

logger.info("Shotgrid 서버 URL: %s", server_url)
logger.info("Shotgrid 스크립트 이름: %s", script_name)
logger.info("Shotgrid API 키: %s", api_key[:4] + "..." + api_key[-4:])

# Shotgrid API 연결
try:
    sg = shotgun_api3.Shotgun(
        server_url,
        script_name=script_name,
        api_key=api_key
    )
    logger.info("Shotgrid 서버에 성공적으로 연결했습니다!")
    
    # 간단한 연결 테스트: 프로젝트 목록 가져오기
    logger.info("프로젝트 목록을 가져오는 중...")
    projects = sg.find(
        "Project",
        [["archived", "is", False]],
        ["id", "name", "sg_status"]
    )
    
    logger.info("%d개의 프로젝트를 찾았습니다:", len(projects))
    for project in projects:
        logger.info("  - ID: %d, 이름: %s", project['id'], project['name'])
    
    logger.info("Shotgrid API 연결 테스트 완료!")
except Exception as e:
    logger.error("Shotgrid 연결 중 오류가 발생했습니다: %s", e)
    sys.exit(1)