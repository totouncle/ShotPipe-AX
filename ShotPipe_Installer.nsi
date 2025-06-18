;=============================================================================
; ShotPipe NSIS 인스톨러 스크립트
; AI Generated File → Shotgrid Automation Tool
;=============================================================================

; 기본 설정 - GitHub Actions 호환성 개선
!define PRODUCT_NAME "ShotPipe"
!define PRODUCT_VERSION "1.3.0"
!define PRODUCT_PUBLISHER "ShotPipe Team"
!define PRODUCT_WEB_SITE "https://github.com/lennonvfx/AX_pipe"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\ShotPipe.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; 빌드 환경 검증
!ifndef PRODUCT_NAME
  !error "PRODUCT_NAME이 정의되지 않았습니다."
!endif

; 모던 UI 포함
!include "MUI2.nsh"
!include "FileFunc.nsh"

; 기본 설정
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "ShotPipe_Setup.exe"
InstallDir "$PROGRAMFILES64\ShotPipe"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; 압축 설정
SetCompressor /SOLID lzma

; 아이콘 설정 (있는 경우)
!ifdef ICON_FILE
Icon "${ICON_FILE}"
UninstallIcon "${ICON_FILE}"
!endif

; 모던 UI 설정
!define MUI_ABORTWARNING
; 아이콘 파일이 없으므로 주석 처리 (기본 아이콘 사용)
;!define MUI_ICON "shotpipe.ico"
;!define MUI_UNICON "shotpipe.ico"

; 인스톨러 페이지
!insertmacro MUI_PAGE_WELCOME
; 라이센스 파일이 있으면 표시, 없으면 건너뛰기
!ifdef LICENSE_FILE
!insertmacro MUI_PAGE_LICENSE "${LICENSE_FILE}"
!endif
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\ShotPipe.exe"
!define MUI_FINISHPAGE_RUN_TEXT "ShotPipe 실행"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "사용자 가이드 보기"
!insertmacro MUI_PAGE_FINISH

; 언인스톨러 페이지
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 언어 설정
!insertmacro MUI_LANGUAGE "Korean"
!insertmacro MUI_LANGUAGE "English"

; 언어별 문자열
LangString WelcomePageTitle ${LANG_KOREAN} "ShotPipe 설치 마법사에 오신 것을 환영합니다"
LangString WelcomePageText ${LANG_KOREAN} "이 마법사는 AI 생성 파일을 Shotgrid로 자동 업로드하는 ShotPipe를 설치합니다.$\r$\n$\r$\n설치를 계속하려면 다음을 클릭하세요."

LangString WelcomePageTitle ${LANG_ENGLISH} "Welcome to the ShotPipe Setup Wizard"
LangString WelcomePageText ${LANG_ENGLISH} "This wizard will install ShotPipe, which automates uploading AI-generated files to Shotgrid.$\r$\n$\r$\nClick Next to continue."

; 설치 섹션 - 파일 경로 검증 강화
Section "ShotPipe (필수)" SecMain
    SectionIn RO
    
    ; 설치 디렉토리 생성
    SetOutPath $INSTDIR
    
    ; 파일 존재 여부 확인 후 복사
    IfFileExists "dist\ShotPipe.exe" 0 exe_not_found
        File "dist\ShotPipe.exe"
        DetailPrint "✅ ShotPipe.exe 설치 완료"
        Goto exe_done
    exe_not_found:
        DetailPrint "❌ 오류: dist\ShotPipe.exe를 찾을 수 없습니다."
        MessageBox MB_ICONSTOP "설치 오류: 실행파일을 찾을 수 없습니다.$\nPyInstaller 빌드가 완료되었는지 확인하세요."
        Abort
    exe_done:
    
    ; 문서 파일들 - 존재 여부 확인
    IfFileExists "README.md" 0 +3
        File "README.md"
        DetailPrint "✅ README.md 설치"
    
    IfFileExists "WINDOWS_USER_GUIDE.md" 0 +3
        File "WINDOWS_USER_GUIDE.md"
        DetailPrint "✅ WINDOWS_USER_GUIDE.md 설치"
    
    IfFileExists "LICENSE.txt" 0 +3
        File "LICENSE.txt"
        DetailPrint "✅ LICENSE.txt 설치"
    
    ; 작업 폴더 생성
    CreateDirectory "$DOCUMENTS\ShotPipe"
    CreateDirectory "$DOCUMENTS\ShotPipe\input"
    CreateDirectory "$DOCUMENTS\ShotPipe\processed"
    CreateDirectory "$DOCUMENTS\ShotPipe\backup"
    
    ; 바탕화면 바로가기
    CreateShortCut "$DESKTOP\ShotPipe.lnk" "$INSTDIR\ShotPipe.exe" "" "$INSTDIR\ShotPipe.exe" 0
    
    ; 시작메뉴 바로가기
    CreateDirectory "$SMPROGRAMS\ShotPipe"
    CreateShortCut "$SMPROGRAMS\ShotPipe\ShotPipe.lnk" "$INSTDIR\ShotPipe.exe" "" "$INSTDIR\ShotPipe.exe" 0
    CreateShortCut "$SMPROGRAMS\ShotPipe\사용자 가이드.lnk" "$INSTDIR\WINDOWS_USER_GUIDE.md"
    CreateShortCut "$SMPROGRAMS\ShotPipe\ShotPipe 제거.lnk" "$INSTDIR\uninstall.exe"
    
    ; 레지스트리 등록
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\ShotPipe.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\ShotPipe.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    
    ; 파일 크기 계산
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
    
    ; 언인스톨러 생성
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "예제 파일" SecExamples
    DetailPrint "예제 파일 설치 중..."
    SetOutPath "$DOCUMENTS\ShotPipe\examples"
    
    ; 예제 파일들이 있는지 확인 후 설치
    IfFileExists "examples\*.*" 0 no_examples
        File /nonfatal /r "examples\*.*"
        DetailPrint "✅ 예제 파일 설치 완료"
        Goto examples_done
    no_examples:
        DetailPrint "ℹ️ 예제 파일이 없습니다 (선택사항)"
    examples_done:
SectionEnd

Section "Visual C++ 재배포 패키지" SecVCRedist
    DetailPrint "Visual C++ 재배포 패키지 확인 중..."
    
    ; VC++ 재배포 패키지 자동 설치 (필요한 경우)
    ; GitHub Actions에서 빌드할 때는 이미 설치되어 있으므로 건너뛰기
    IfFileExists "vcredist_x64.exe" 0 no_vcredist
        DetailPrint "Visual C++ 재배포 패키지 설치 중..."
        File "vcredist_x64.exe"
        ExecWait "$INSTDIR\vcredist_x64.exe /quiet" $0
        Delete "$INSTDIR\vcredist_x64.exe"
        ${If} $0 == 0
            DetailPrint "✅ Visual C++ 재배포 패키지 설치 완료"
        ${Else}
            DetailPrint "⚠️ Visual C++ 재배포 패키지 설치 중 문제 발생 (코드: $0)"
        ${EndIf}
        Goto vcredist_done
    no_vcredist:
        DetailPrint "ℹ️ Visual C++ 재배포 패키지 파일이 없습니다 (선택사항)"
    vcredist_done:
SectionEnd

; 섹션 설명
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "ShotPipe 메인 프로그램 및 필수 파일들입니다."
!insertmacro MUI_DESCRIPTION_TEXT ${SecExamples} "사용법을 익힐 수 있는 예제 파일들입니다."
!insertmacro MUI_DESCRIPTION_TEXT ${SecVCRedist} "프로그램 실행에 필요한 Microsoft Visual C++ 재배포 패키지입니다."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 설치 후 함수
Function .onInstSuccess
    ; Windows Defender 예외 추가 안내
    MessageBox MB_ICONINFORMATION|MB_YESNO \
    "설치가 완료되었습니다!$\r$\n$\r$\n💡 참고: Windows Defender에서 차단될 수 있습니다.$\r$\n이는 정상적인 현상이며, '추가 정보' → '실행'을 클릭하면 됩니다.$\r$\n$\r$\n지금 ShotPipe를 실행하시겠습니까?" \
    IDYES LaunchApp IDNO End
    
    LaunchApp:
        Exec "$INSTDIR\ShotPipe.exe"
    End:
FunctionEnd

; 설치 전 체크 - 개선된 검증
Function .onInit
    ; 디버그 정보 출력
    DetailPrint "설치 프로그램 초기화 중..."
    
    ; Windows 버전 확인
    ${If} ${AtLeastWin10}
        DetailPrint "✅ Windows 버전: 10 이상 (권장)"
    ${ElseIf} ${AtLeastWin7}
        DetailPrint "⚠️ Windows 버전: 7-8 (호환 가능하지만 10 이상 권장)"
        MessageBox MB_ICONEXCLAMATION "Windows 10 이상을 권장합니다. 일부 기능이 제한될 수 있습니다."
    ${Else}
        DetailPrint "❌ Windows 버전: 7 미만 (지원되지 않음)"
        MessageBox MB_ICONSTOP "Windows 7 이상이 필요합니다."
        Abort
    ${EndIf}
    
    ; 관리자 권한 확인 - 더 유연하게 처리
    UserInfo::GetAccountType
    pop $0
    DetailPrint "사용자 권한: $0"
    ${If} $0 == "admin"
        DetailPrint "✅ 관리자 권한으로 실행 중"
    ${ElseIf} $0 == "power"
        DetailPrint "✅ Power User 권한으로 실행 중"
    ${Else}
        DetailPrint "⚠️ 제한된 사용자 권한"
        MessageBox MB_ICONQUESTION|MB_YESNO "관리자 권한이 아닙니다. 일부 기능이 제한될 수 있습니다.$\n계속 진행하시겠습니까?" IDYES +2
        Abort
    ${EndIf}
    
    ; 기존 설치 확인
    ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_ICONQUESTION|MB_YESNOCANCEL|MB_DEFBUTTON2 \
    "ShotPipe $R1이 이미 설치되어 있습니다.$\r$\n기존 버전을 제거하고 새로 설치하시겠습니까?" \
    IDYES uninst IDNO done
    Abort
    
    uninst:
        ClearErrors
        ExecWait '$R0 /S _?=$INSTDIR'
        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:
    
    done:
FunctionEnd

; 언인스톨 섹션
Section Uninstall
    ; 파일 삭제
    Delete "$INSTDIR\ShotPipe.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\WINDOWS_USER_GUIDE.md"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\uninstall.exe"
    
    ; 바로가기 삭제
    Delete "$DESKTOP\ShotPipe.lnk"
    Delete "$SMPROGRAMS\ShotPipe\ShotPipe.lnk"
    Delete "$SMPROGRAMS\ShotPipe\사용자 가이드.lnk"
    Delete "$SMPROGRAMS\ShotPipe\ShotPipe 제거.lnk"
    RMDir "$SMPROGRAMS\ShotPipe"
    
    ; 설치 디렉토리 삭제
    RMDir "$INSTDIR"
    
    ; 레지스트리 삭제
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
    
    ; 사용자 데이터는 보존하고 확인
    MessageBox MB_ICONQUESTION|MB_YESNO \
    "사용자 데이터 폴더($DOCUMENTS\ShotPipe)도 삭제하시겠습니까?$\r$\n$\r$\n'아니오'를 선택하면 설정과 작업 파일이 보존됩니다." \
    IDYES DeleteUserData IDNO KeepUserData
    
    DeleteUserData:
        RMDir /r "$DOCUMENTS\ShotPipe"
        Goto End
    
    KeepUserData:
        MessageBox MB_ICONINFORMATION "사용자 데이터가 보존되었습니다: $DOCUMENTS\ShotPipe"
    
    End:
        MessageBox MB_ICONINFORMATION "ShotPipe가 성공적으로 제거되었습니다."
SectionEnd

; 언인스톨 전 체크
Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNOCANCEL|MB_DEFBUTTON2 \
    "ShotPipe를 완전히 제거하시겠습니까?" IDYES +2
    Abort
FunctionEnd