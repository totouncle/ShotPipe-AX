;=============================================================================
; ShotPipe NSIS 인스톨러 스크립트 (Mac 테스트용)
; AI Generated File → Shotgrid Automation Tool
;=============================================================================

; 기본 설정
!define PRODUCT_NAME "ShotPipe"
!define PRODUCT_VERSION "1.3.0"
!define PRODUCT_PUBLISHER "ShotPipe Team"
!define PRODUCT_WEB_SITE "https://github.com/lennonvfx/AX_pipe"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\ShotPipe.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; 모던 UI 포함
!include "MUI2.nsh"
!include "FileFunc.nsh"

; 기본 설정
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "ShotPipe_v${PRODUCT_VERSION}_Setup.exe"
InstallDir "$PROGRAMFILES64\ShotPipe"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; 압축 설정
SetCompressor /SOLID lzma

; 모던 UI 설정
!define MUI_ABORTWARNING

; 인스톨러 페이지
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 언인스톨러 페이지
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 언어 설정
!insertmacro MUI_LANGUAGE "English"

; 설치 섹션
Section "Main" SEC01
  SetOverwrite ifnewer
  SetOutPath "$INSTDIR"
  
  ; 실행 파일 복사 (임시로 Mac 실행파일 사용)
  File "dist/ShotPipe"
  Rename "$INSTDIR\ShotPipe" "$INSTDIR\ShotPipe.exe"
  
  ; shotpipe 모듈 복사
  SetOutPath "$INSTDIR\shotpipe"
  File /r "shotpipe\*.*"
  
  ; vendor 폴더 복사
  SetOutPath "$INSTDIR\vendor"
  File /r "vendor\*.*"
  
  ; 문서 파일들 복사
  SetOutPath "$INSTDIR"
  File "README.md"
  File "LICENSE.txt"
  File "WINDOWS_USER_GUIDE.md"
  
  ; 바탕화면 바로가기 생성
  CreateShortCut "$DESKTOP\ShotPipe.lnk" "$INSTDIR\ShotPipe.exe"
  
  ; 시작 메뉴 바로가기 생성
  CreateDirectory "$SMPROGRAMS\ShotPipe"
  CreateShortCut "$SMPROGRAMS\ShotPipe\ShotPipe.lnk" "$INSTDIR\ShotPipe.exe"
  CreateShortCut "$SMPROGRAMS\ShotPipe\Uninstall.lnk" "$INSTDIR\uninst.exe"
  
  ; 레지스트리 등록
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\ShotPipe.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\ShotPipe.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  
  ; 언인스톨러 생성
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

; 언인스톨 섹션
Section Uninstall
  ; 파일 삭제
  Delete "$INSTDIR\ShotPipe.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\WINDOWS_USER_GUIDE.md"
  Delete "$INSTDIR\uninst.exe"
  
  ; 폴더 삭제
  RMDir /r "$INSTDIR\shotpipe"
  RMDir /r "$INSTDIR\vendor"
  RMDir "$INSTDIR"
  
  ; 바로가기 삭제
  Delete "$DESKTOP\ShotPipe.lnk"
  Delete "$SMPROGRAMS\ShotPipe\ShotPipe.lnk"
  Delete "$SMPROGRAMS\ShotPipe\Uninstall.lnk"
  RMDir "$SMPROGRAMS\ShotPipe"
  
  ; 레지스트리 삭제
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
SectionEnd

; 언인스톨러 함수
Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name)가 성공적으로 제거되었습니다."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "$(^Name)을 완전히 제거하시겠습니까?" IDYES +2
  Abort
FunctionEnd