# Shotgrid API 연결 설정 가이드

## 문제 진단

현재 `AX_shotPipe` 스크립트로 Shotgrid에 인증할 수 없습니다. 이는 다음과 같은 원인일 수 있습니다:

1. 스크립트가 Shotgrid에 등록되지 않음
2. API 키가 잘못됨
3. 스크립트 권한이 충분하지 않음

## 해결 방법

### 1. Shotgrid에서 새 API 스크립트 생성하기

1. Shotgrid 사이트(`https://lennon.shotgunstudio.com`)에 관리자 계정으로 로그인합니다.

2. 우측 상단의 아바타를 클릭하고 **관리자** 메뉴로 이동합니다.

3. 왼쪽 메뉴에서 **스크립트**를 선택합니다.

4. **+ 새 스크립트** 버튼을 클릭합니다.

5. 다음 정보를 입력합니다:
   - **스크립트 이름**: `AX_shotPipe` (또는 다른 이름)
   - **설명**: `ShotPipe application for file processing and uploading`
   - **상태**: `활성`
   - **권한**: `관리자` (또는 적절한 권한)

6. **저장** 버튼을 클릭하여 스크립트를 생성합니다.

7. 생성된 스크립트 정보 화면에서 **API 키**를 확인합니다. 이 키는 한 번만 표시되므로 안전한 곳에 저장하세요.

### 2. 새 API 키로 애플리케이션 설정 업데이트하기

1. `.env` 파일을 다음과 같이 업데이트합니다:

```
# Shotgrid 연결 정보
SHOTGRID_URL=https://lennon.shotgunstudio.com
SHOTGRID_SCRIPT_NAME=AX_shotPipe  # 또는 새로 생성한 스크립트 이름
SHOTGRID_API_KEY=<새로 생성된 API 키>
```

2. 애플리케이션을 다시 시작하고 연결을 테스트합니다.

### 3. 새 스크립트 생성이 어려운 경우

만약 관리자 권한이 없거나 새 스크립트를 생성할 수 없는 경우:

1. Shotgrid 관리자에게 문의하여 기존 `AX_shotPipe` 스크립트의 API 키를 초기화하거나 새 스크립트를 생성하도록 요청하세요.

2. 필요한 스크립트 권한 목록:
   - 프로젝트, 샷, 버전 읽기/쓰기 권한
   - 미디어 업로드 권한
   - 작업 관리 권한

## 테스트 방법

1. API 키를 업데이트한 후, 다음 명령어를 실행하여 테스트합니다:

```bash
cd /Users/onset/AX_pipe/ShotPipe
python test_sg_detailed.py
```

2. 연결이 성공하면 다음과 같은 출력이 표시됩니다:
   ```
   Shotgrid 서버에 성공적으로 연결했습니다!
   인증 성공! 테스트 쿼리 결과: ...
   ```