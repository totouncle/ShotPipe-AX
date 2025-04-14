#!/usr/bin/env python
"""
Shotgrid API 연결 상세 테스트 스크립트
"""
import os
import sys
import logging
from dotenv import load_dotenv
import traceback

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('shotgrid_test')

# 환경 변수 로드
load_dotenv()

# 호환성 패치
try:
    import six
    if not hasattr(six, 'PY38'):
        six.PY38 = sys.version_info >= (3, 8)
    
    # 필요한 모듈 패치
    import xmlrpc.client
    import http.client
    import urllib.parse
    import urllib.request
    import urllib.error
    
    # 패치 적용
    sys.modules['shotgun_api3.lib.six'] = six
    sys.modules['shotgun_api3.lib.six.moves'] = six.moves
    sys.modules['shotgun_api3.lib.six.moves.xmlrpc_client'] = xmlrpc.client
    sys.modules['shotgun_api3.lib.six.moves.http_client'] = http.client
    
    # urllib 패치
    class UrllibModule:
        parse = urllib.parse
        request = urllib.request
        error = urllib.error
    
    urllib_module = UrllibModule()
    sys.modules['shotgun_api3.lib.six.moves.urllib'] = urllib_module
    sys.modules['shotgun_api3.lib.six.moves.urllib.parse'] = urllib.parse
    sys.modules['shotgun_api3.lib.six.moves.urllib.request'] = urllib.request
    sys.modules['shotgun_api3.lib.six.moves.urllib.error'] = urllib.error
    
    logger.info("패치가 성공적으로 적용되었습니다.")
except Exception as e:
    logger.error(f"패치 적용 중 오류: {e}")
    traceback.print_exc()

# shotgun_api3 임포트 시도
try:
    import shotgun_api3
    logger.info(f"shotgun_api3 모듈을 성공적으로 불러왔습니다. 버전: {getattr(shotgun_api3, '__version__', '알 수 없음')}")
except ImportError as e:
    logger.error(f"shotgun_api3 모듈을 불러오지 못했습니다: {e}")
    traceback.print_exc()
    sys.exit(1)

# Shotgrid 연결 정보
server_url = os.getenv('SHOTGRID_URL')
script_name = os.getenv('SHOTGRID_SCRIPT_NAME')
api_key = os.getenv('SHOTGRID_API_KEY')

# 연결 정보 확인
logger.info(f"서버 URL: {server_url}")
logger.info(f"스크립트 이름: {script_name}")
if api_key:
    logger.info(f"API 키: {api_key[:4]}...{api_key[-4:]}")
else:
    logger.error("API 키가 설정되지 않았습니다.")

# Shotgrid API 연결 시도
try:
    logger.info("Shotgrid에 연결 중...")
    sg = shotgun_api3.Shotgun(
        server_url,
        script_name=script_name,
        api_key=api_key,
        http_proxy=None,
        connect=True,
        ca_certs=None
    )
    logger.info("Shotgrid 서버에 성공적으로 연결했습니다!")
    
    # 기본 API 요청 시도
    logger.info("API 키 인증 테스트 중...")
    # 간단한 쿼리로 인증 테스트
    result = sg.find_one("HumanUser", [["login", "is_not", "dummy_value"]], ["id", "login"])
    logger.info(f"인증 성공! 테스트 쿼리 결과: {result}")
    
    # 간단한 프로젝트 목록 가져오기
    logger.info("프로젝트 목록을 가져오는 중...")
    projects = sg.find("Project", [["archived", "is", False]], ["id", "name"])
    logger.info(f"{len(projects)}개의 프로젝트를 찾았습니다.")
    for project in projects:
        logger.info(f"  - ID: {project['id']}, 이름: {project['name']}")
    
    logger.info("Shotgrid API 연결 테스트 완료!")
except Exception as e:
    logger.error(f"Shotgrid 연결 또는 인증 중 오류가 발생했습니다: {e}")
    traceback.print_exc()
    
    # 자세한 오류 분석
    logger.info("오류 상세 분석 시작...")
    if "authenticate" in str(e).lower():
        logger.error("인증 실패: 스크립트 이름 또는 API 키가 올바르지 않습니다.")
        logger.error("Shotgrid 관리자 메뉴 > 스크립트에서 스크립트 이름과 API 키를 확인하세요.")
    
    if "connection" in str(e).lower():
        logger.error("연결 실패: 서버 URL이 올바르지 않거나 서버에 연결할 수 없습니다.")
        logger.error("인터넷 연결 및 Shotgrid 서버 URL을 확인하세요.")
    
    sys.exit(1)