# Lotto 6/45 Django Project

Django와 Docker multi-container 환경으로 구성한 6/45 로또 웹 사이트입니다.

## 주요 기능

- 회원가입 및 로그인
- 사용자별 수동 번호 구매
- 사용자별 자동 번호 구매
- 티켓번호 기반 구매 추적
- 사용자별 구매 금액, 당첨 금액, 추첨 대기 요약
- 사용자별 구매 내역 및 당첨 결과 확인
- 관리자 판매 현황 확인
- 관리자 회차별/티켓별 판매 내역 확인
- 관리자 추첨 실행
- 회차별 1등~5등 당첨자 수, 판매액, 지급액, 이익 확인

## Docker 실행

```bash
docker compose up --build
```

웹 브라우저에서 `http://localhost:8000`으로 접속합니다.

관리자 계정은 컨테이너 실행 후 다음 명령으로 생성합니다.

```bash
docker compose exec web python manage.py createsuperuser
```

## 로컬 테스트

Django가 설치된 Python 환경에서 실행합니다.

```bash
python manage.py test
```

이 작업 공간에서는 다음 명령으로 검증했습니다.

```bash
conda run -n bys python manage.py check
conda run -n bys python manage.py test
```

## 구조

```text
lotto_project/      Django 프로젝트 설정
lotto/              로또 도메인 앱
templates/          사용자/관리자 화면 템플릿
static/css/         화면 스타일
Dockerfile          Django web 컨테이너
docker-compose.yml  web + PostgreSQL db multi-container 구성
REPORT.md           과제 보고서 초안
```
