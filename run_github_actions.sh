#!/bin/bash

# ============================================================================
# GitHub Actions 원격 빌드 실행 스크립트
# Mac에서 Windows/macOS/Linux 빌드를 GitHub Actions로 실행
# ============================================================================

echo "🚀 GitHub Actions 빌드 실행 스크립트"
echo "=================================="
echo ""

# GitHub CLI 인증 확인
echo "🔐 GitHub 인증 확인 중..."
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI 인증이 필요합니다."
    echo ""
    echo "다음 명령어를 실행하여 인증하세요:"
    echo "  gh auth login"
    echo ""
    echo "인증 방법:"
    echo "1. GitHub.com 선택"
    echo "2. HTTPS 선택"
    echo "3. 브라우저로 인증 (Y)"
    echo "4. 브라우저에서 코드 입력 및 승인"
    echo ""
    exit 1
fi

echo "✅ GitHub 인증 완료"
echo ""

# 저장소 확인
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "❌ Git 저장소를 찾을 수 없습니다."
    echo "현재 디렉토리가 Git 저장소인지 확인하세요."
    exit 1
fi

echo "📦 저장소: $REPO"
echo ""

# 워크플로우 선택
echo "🎯 실행할 워크플로우를 선택하세요:"
echo "1. Multi-Platform Build (Windows + macOS + Linux)"
echo "2. Windows Build Only"
echo "3. Windows Release Build"
echo "4. 모든 워크플로우 보기"
echo ""
read -p "선택 (1-4): " choice

case $choice in
    1)
        WORKFLOW="build-multiplatform.yml"
        echo "✅ Multi-Platform Build 선택"
        ;;
    2)
        WORKFLOW="build-windows.yml"
        echo "✅ Windows Build 선택"
        ;;
    3)
        WORKFLOW="windows-release.yml"
        echo "✅ Windows Release Build 선택"
        ;;
    4)
        echo "📋 사용 가능한 워크플로우:"
        gh workflow list
        echo ""
        read -p "워크플로우 파일명 입력: " WORKFLOW
        ;;
    *)
        echo "❌ 잘못된 선택"
        exit 1
        ;;
esac

echo ""
echo "🚀 워크플로우 실행 중: $WORKFLOW"
echo "=================================="

# 워크플로우 실행
if gh workflow run "$WORKFLOW"; then
    echo "✅ 워크플로우가 시작되었습니다!"
    echo ""
    
    # 실행 ID 가져오기 (잠시 대기)
    sleep 3
    
    # 최근 실행 확인
    echo "📊 최근 실행 상태:"
    gh run list --workflow="$WORKFLOW" --limit 1
    echo ""
    
    # 실시간 모니터링 옵션
    read -p "실시간으로 진행 상황을 보시겠습니까? (y/n): " watch_choice
    if [[ $watch_choice == "y" || $watch_choice == "Y" ]]; then
        # 가장 최근 실행 ID 가져오기
        RUN_ID=$(gh run list --workflow="$WORKFLOW" --limit 1 --json databaseId -q '.[0].databaseId')
        if [ -n "$RUN_ID" ]; then
            echo "🔍 실행 ID: $RUN_ID"
            echo "실시간 모니터링 중... (Ctrl+C로 종료)"
            gh run watch "$RUN_ID"
        fi
    else
        echo ""
        echo "💡 진행 상황 확인 명령어:"
        echo "  gh run list --workflow=$WORKFLOW"
        echo "  gh run view [RUN_ID]"
        echo "  gh run watch [RUN_ID]"
    fi
    
    echo ""
    echo "📦 빌드 완료 후 아티팩트 다운로드:"
    echo "  gh run download [RUN_ID]"
    echo ""
    echo "🌐 또는 브라우저에서 확인:"
    echo "  https://github.com/$REPO/actions"
    
else
    echo "❌ 워크플로우 실행 실패"
    echo "권한을 확인하거나 다시 시도하세요."
    exit 1
fi

echo ""
echo "=================================="
echo "✅ 완료!"