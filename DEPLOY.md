# 배포 가이드 (Deployment Guide)

이 프로젝트는 **Streamlit Community Cloud**를 통해 누구나 무료로 쉽게 인터넷에 배포할 수 있습니다.

## 1. 보안 점검 (Security Check)
현재 코드베이스에는 **API Key나 비밀번호가 포함되어 있지 않습니다.**
- 데이터 소스로 사용하는 `yfinance`는 공개된 무료 데이터를 사용하므로 별도의 API Key가 필요 없습니다.
- 따라서 GitHub와 같은 공개 저장소(Public Repository)에 코드를 올려도 안전합니다.

## 2. 배포 방법 (Streamlit Community Cloud)

가장 추천하는 방법은 Streamlit에서 공식 제공하는 클라우드 서비스를 이용하는 것입니다.

### 단계 1: GitHub에 코드 업로드
1. GitHub에 로그인하고 새로운 Repository를 생성합니다 (Public으로 설정).
2. 현재 프로젝트 코드를 해당 Repository에 업로드(Push)합니다.
   - `requirements.txt` 파일이 반드시 포함되어야 합니다 (라이브러리 자동 설치용).

### 단계 2: Streamlit Cloud 연동
1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다 (GitHub 계정 연동).
2. 우측 상단의 **"New app"** 버튼을 클릭합니다.
3. **"Use existing repo"**를 선택합니다.
4. 다음 정보를 입력합니다:
   - **Repository**: 방금 업로드한 GitHub 저장소 선택
   - **Branch**: `main` (또는 업로드한 브랜치명)
   - **Main file path**: `“0_🏠_데시보드.py”` (※ 중요: 파일명이 변경되었으므로 반드시 직접 입력/선택해야 합니다)
5. **"Deploy!"** 버튼을 클릭합니다.

> **💡 이미 배포된 경우:**
> GitHub에 `git push`를 하면 자동으로 Streamlit 앱이 업데이트됩니다.
> 단, 메인 파일명이 `app.py`에서 `0_🏠_데시보드.py`로 변경되었으므로, Streamlit 대시보드의 **Settings > General > Main file path**에서 파일 경로를 수정해 주어야 합니다.

### 단계 3: 배포 완료
- 약 1~3분 정도 기다리면 배포가 완료되고, 전 세계 어디서나 접속 가능한 URL이 생성됩니다.
- 예: `https://jboard-example.streamlit.app`

## 3. 기타 배포 방법
- **Docker**: `Dockerfile`을 작성하여 AWS EC2, Google Cloud Run 등에 배포할 수 있습니다.
- **Heroku / Railway**: PaaS 서비스를 이용하여 배포할 수도 있습니다.
- 하지만 `yfinance`를 사용하는 가벼운 앱은 **Streamlit Community Cloud**가 가장 간편하고 무료입니다.
