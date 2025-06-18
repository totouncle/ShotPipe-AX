# 🤖 GitHub Actions 자동 빌드 가이드

## 🎯 이제 Windows PC 없이도 exe 파일을 만들 수 있습니다!

### ✨ 어떻게 작동하나요?

1. **코드를 푸시**하면 → GitHub에서 **자동으로 Windows 가상머신** 생성
2. **자동으로 빌드** 실행 → **ShotPipe_Setup.exe** 생성
3. **다운로드** 받아서 바로 사용! 🎉

---

## 🚀 사용 방법

### **방법 1: 자동 빌드 (코드 변경 시)**
```bash
# 코드를 수정하고 푸시하면 자동 빌드
git add .
git commit -m "업데이트"
git push
```
→ 5-10분 후 자동으로 exe 파일 생성됨

### **방법 2: 수동 빌드 (언제든지)**
```
1. GitHub 저장소 → "Actions" 탭 클릭
2. "🚀 Windows 배포 빌드" 클릭
3. "Run workflow" 버튼 클릭
4. 5-10분 대기
5. 완료!
```

---

## 📁 빌드 결과 다운로드 방법

### **Step 1: Actions 페이지로 이동**
```
GitHub 저장소 → Actions 탭 → 최신 빌드 클릭
```

### **Step 2: Artifacts 다운로드**
```
페이지 하단 "Artifacts" 섹션에서:
📦 "ShotPipe-Windows-Build" 클릭 → ZIP 다운로드
```

### **Step 3: 압축 해제**
```
다운로드한 ZIP 파일 압축 해제하면:
├── ShotPipe_Setup.exe          ← 초보자용 인스톨러
├── ShotPipe_v1.3.0_Portable.zip ← 포터블 버전
└── ShotPipe.exe                ← 실행파일
```

---

## 🎯 실제 사용 예시

### **시나리오: 코드 수정 후 새 exe 필요**

```bash
# 1. 코드 수정
git add .
git commit -m "버그 수정"
git push

# 2. GitHub Actions 자동 실행 (5-10분)
# 3. 완료 후 다운로드
```

### **시나리오: 지금 당장 exe 필요**

```
1. https://github.com/lennonvfx/AX_pipe/actions 접속
2. "🚀 Windows 배포 빌드" 클릭
3. "Run workflow" → "Run workflow" 클릭
4. 커피 한 잔 ☕ (5-10분 대기)
5. Artifacts에서 다운로드
```

---

## 📊 빌드 상태 확인

### **실시간 진행상황**
```
Actions 탭에서 빌드 진행상황을 실시간으로 확인 가능:
🟡 진행 중  🟢 성공  🔴 실패
```

### **로그 확인**
```
각 단계별 상세 로그 확인 가능:
- Python 설치
- 의존성 설치  
- PyInstaller 실행
- NSIS 인스톨러 생성
- 파일 압축
```

---

## 🛠️ 문제 해결

### **빌드 실패 시**
```
1. Actions 탭에서 실패한 빌드 클릭
2. 실패한 단계의 로그 확인
3. 오류 메시지 기반으로 코드 수정
4. 다시 푸시하면 자동 재빌드
```

### **일반적인 오류들**
```
❌ "requirements.txt 없음"
   → requirements.txt 파일 확인

❌ "PyInstaller 실패"  
   → shotpipe.spec 파일 확인

❌ "NSIS 오류"
   → ShotPipe_Installer.nsi 파일 확인
```

---

## 🎁 추가 기능

### **릴리즈 자동 생성**
```bash
# 태그를 푸시하면 자동으로 릴리즈 생성
git tag v1.3.1
git push origin v1.3.1
```
→ GitHub Releases에 자동으로 exe 파일 업로드

### **버전 관리**
```
수동 빌드 시 버전 번호 지정 가능:
Actions → Run workflow → Version 입력
```

---

## 💡 꿀팁

### **효율적인 사용법**
1. **자주 빌드하지 마세요** - GitHub Actions 무료 한도 (월 2000분)
2. **테스트 후 빌드** - 로컬에서 충분히 테스트 후 푸시
3. **배치 작업** - 여러 변경사항을 모아서 한 번에 커밋

### **빌드 시간 단축**
- 불필요한 파일 변경 시 빌드 안 함
- 캐시 활용으로 의존성 설치 시간 단축
- 병렬 처리로 전체 빌드 시간 최적화

---

## 🎉 이제 완전 자동화!

**더 이상 Windows PC가 필요 없습니다!**

1. **macOS에서 개발** → GitHub에 푸시
2. **GitHub Actions가 자동 빌드** → Windows exe 생성  
3. **다운로드 받아서 배포** → 사용자에게 전달

**개발도 편하고 배포도 편한 완벽한 시스템 완성! 🚀**