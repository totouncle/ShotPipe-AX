#!/usr/bin/env python
"""
Shotgrid API 키 테스트 스크립트
"""
import os
import sys
import logging
from dotenv import load_dotenv
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api_key_test')

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

# 함수 정의
def test_connection(server_url, script_name, api_key):
    """Shotgrid 연결 테스트"""
    logger.info(f"서버: {server_url}, 스크립트: {script_name}, API 키: {api_key[:4]}...{api_key[-4:]}")
    
    try:
        sg = shotgun_api3.Shotgun(
            server_url,
            script_name=script_name,
            api_key=api_key
        )
        # 간단한 테스트 쿼리 실행
        result = sg.find_one("HumanUser", [["login", "is_not", "dummy_value"]], ["id", "login"])
        logger.info(f"연결 성공! 인증 확인: {result}")
        return True
    except Exception as e:
        logger.error(f"연결 실패: {e}")
        return False

# 메인 코드
if __name__ == "__main__":
    # 명령행 인수로 API 키를 받을 수 있음
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        logger.info("명령행에서 API 키를 받았습니다.")
    else:
        # 환경 변수에서 가져오기
        api_key = os.getenv('SHOTGRID_API_KEY')
        logger.info("환경 변수에서 API 키를 가져왔습니다.")
    
    server_url = os.getenv('SHOTGRID_URL')
    script_name = os.getenv('SHOTGRID_SCRIPT_NAME')
    
    if not server_url or not script_name or not api_key:
        logger.error("서버 URL, 스크립트 이름, API 키가 모두 필요합니다.")
        sys.exit(1)
    
    # 연결 테스트
    success = test_connection(server_url, script_name, api_key)
    
    if not success:
        logger.info("\n새 API 키를 테스트하려면:")
        logger.info(f"python {sys.argv[0]} 새_API_키")
        
        # 추가 안내
        logger.info("\nShotgrid API 키 문제를 해결하려면:")
        logger.info("1. shotgrid_setup_guide.md 파일의 지침을 따르세요.")
        logger.info("2. Shotgrid 관리자 메뉴에서 API 스크립트를 확인하세요.")
        logger.info("3. 새 스크립트를 생성하거나 기존 스크립트의 API 키를 재설정하세요.")
        sys.exit(1)
    
    sys.exit(0)