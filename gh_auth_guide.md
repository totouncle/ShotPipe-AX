# 🔐 GitHub CLI 인증 가이드

## 빠른 인증 (1분 소요)

### 1. 터미널에서 인증 시작
```bash
gh auth login
```

### 2. 옵션 선택
```
? What account do you want to log into?
> GitHub.com  ← 선택

? What is your preferred protocol for Git operations?
> HTTPS  ← 선택

? Authenticate Git with your GitHub credentials?
> Yes  ← 선택

? How would you like to authenticate GitHub CLI?
> Login with a web browser  ← 선택
```

### 3. 브라우저 인증
- 터미널에 표시된 8자리 코드 복사
- Enter 키 누르면 브라우저 열림
- 코드 붙여넣기
- "Authorize github" 클릭

### 4. 완료!
```bash
✓ Authentication complete.
```

## 인증 확인
```bash
gh auth status
```

## 인증 후 GitHub Actions 실행
```bash
# 스크립트 실행
./run_github_actions.sh

# 또는 직접 실행
gh workflow run build-multiplatform.yml
```

## 문제 해결

### 인증 초기화
```bash
gh auth logout
gh auth login
```

### Personal Access Token 사용
```bash
gh auth login --with-token < token.txt
```

---
**5분이면 설정 완료! GitHub Actions로 Windows 빌드를 실행해보세요!** 🚀