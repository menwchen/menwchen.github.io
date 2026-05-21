# menwchen.github.io 배포 가이드 — WhoWin 송영길 라이브 대시보드

이 폴더 구조를 **menwchen.github.io 레포의 루트 위에 그대로 덮어쓰기**하면 됩니다.

## 추가되는 파일

```
_posts/2026-05-17-whowin-songyounggil.md       Jekyll 블로그 글 (스냅샷 본문)
whowin-songyounggil-dashboard.html             실시간 대시보드 (루트 경로)
data/whowin/songyounggil.json                  데이터 (자동 갱신 대상)
scripts/whowin_update.py                       텍스트 마이닝 스크립트 (stdlib only)
.github/workflows/whowin-update.yml            cron 3시간 워크플로우
```

## 1회만 하면 되는 작업

```bash
# 1. 레포 클론
git clone git@github.com:menwchen/menwchen.github.io.git
cd menwchen.github.io

# 2. 이 폴더 내용을 그대로 복사
cp -R "/Users/jongunsong/클로드 코드 샘플/menwchen-github-io-additions/." .

# 3. 커밋 & 푸시
git add _posts whowin-songyounggil-dashboard.html data scripts .github
git commit -m "feat(whowin): 송영길 인천 연수갑 실시간 텍스트 마이닝 대시보드"
git push
```

## GitHub Actions 권한 (한 번 확인 필요)

`Settings → Actions → General → Workflow permissions` 에서
**Read and write permissions** 가 켜져 있어야 봇이 `data/whowin/songyounggil.json` 을 커밋할 수 있습니다.
대부분의 사용자 페이지 레포는 기본으로 켜져 있습니다.

## 동작 흐름

1. 매 3시간마다 (`cron: "5 */3 * * *"`) GitHub Actions 가 `scripts/whowin_update.py` 실행
2. 스크립트가 Google News RSS 에서 "송영길 연수갑" 등 4개 쿼리의 최신 기사를 수집
3. 키워드 빈도(TF) + 룰 기반 감성 분류 후 `data/whowin/songyounggil.json` 갱신
4. 변경분이 있으면 봇 계정이 자동 커밋
5. `whowin-songyounggil-dashboard.html` 은 페이지 로드 시 + 5분마다 JSON 을 다시 fetch

## 결과 페이지

- 블로그 글: `https://menwchen.github.io/blog/2026-05-17-whowin-songyounggil/` (퍼머링크 규칙에 따름)
- 대시보드: `https://menwchen.github.io/whowin-songyounggil-dashboard.html`
- 데이터 (raw): `https://menwchen.github.io/data/whowin/songyounggil.json`

## 즉시 한 번 돌리고 싶다면

레포에 push 후 `Actions → WhoWin · 송영길 데이터 갱신 → Run workflow` 로 수동 트리거.

## 추가 후보·선거구 확장

`scripts/whowin_update.py` 의 `QUERIES`, `KEYWORDS`, `OUT_PATH` 만 바꿔서
`data/whowin/<slug>.json` 형태로 여러 선거구를 병렬로 운영할 수 있습니다.
워크플로우 매트릭스로 묶으면 한 번에 N개 선거구 동시 갱신도 가능.
