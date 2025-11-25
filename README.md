# 미국 증시 섹터 데시보드

미국 증시 섹터별 현황, 대표 ETF 스냅샷, 당일 뉴스를 한 화면에서 확인할 수 있는 Streamlit 기반 대시보드입니다.

## 주요 기능
- **섹터 퍼포먼스**: 실시간(또는 샘플) 데이터를 기반으로 섹터별 변동률을 시각화.
- **대표 ETF 분석**: 섹터 대표 ETF의 가격, 변동률, 52주 고/저점, 거래량 확인.
- **시장 개요**: S&P 500, 다우, 나스닥 등 주요 지수의 일간 성과.
- **뉴스 피드**: 선택한 섹터(ETF 티커)에 기반한 최신 뉴스 헤드라인과 요약.

## 사전 준비
- Python 3.10 이상
- **API 키가 필요 없습니다.** (Yahoo Finance 무료 데이터 사용)

## 설치 및 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

브라우저에서 표시되는 주소(기본: http://localhost:8501)를 열어 대시보드를 확인하세요.

## 앱 사용 방법
1. 별도의 설정 없이 실행 즉시 데이터를 확인할 수 있습니다.
2. `뉴스 기사 수` 슬라이더로 뉴스 피드의 게시물 개수를 조정합니다.
3. 섹터 퍼포먼스 표가 로딩된 후, **뉴스 필터**에서 관심 섹터를 선택하면 해당 섹터 관련 뉴스만 모아서 볼 수 있습니다.

## 데이터 출처
- **Yahoo Finance (`yfinance`)**: 실시간(약 15분 지연) 주가 및 뉴스 데이터를 무료로 제공받습니다.

## 기타
- `services/yfinance_client.py`: Yahoo Finance API 연동 유틸리티.
- `data/sample_data.py`: 오프라인 모드 또는 에러 발생 시 사용하는 샘플 데이터.
- 배포 시 별도의 시크릿(Secret) 설정이 필요하지 않습니다.
