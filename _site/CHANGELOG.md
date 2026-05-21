# 블로그 개선 작업 기록 (2026-03-23)

## 세션 개요

Claude Code를 사용하여 Jekyll 블로그(menwchen.github.io)를 종합 개선한 작업 기록.

---

## 1. 환경 설정

- tmux 3.6a 설치
- Claude Code settings.json에 Agent Teams 실험 기능 및 tmux 모드 설정 추가

## 2. 디자인 개선 (브랜치: improve/design)

**파일: `_includes/head.html`, `_layouts/post.html`**

- 한글 타이포그래피 최적화: `word-break: keep-all`, `letter-spacing: -0.01em`
- 본문 `font-size: 17px`, `line-height: 1.85`, paragraph spacing `1.5em`
- 768px / 640px 이중 반응형 브레이크포인트 추가
- 모바일 터치 타겟 44px 이상, 버튼 풀 위드스
- 포스트 페이지에 "← 홈으로" 내비게이션 추가
- 이미지 반응형 처리 (`max-width: 100%`)

## 3. SEO 강화 (브랜치: improve/seo)

**파일: `_config.yml`, `_includes/og-meta.html`, `_includes/head.html`, `sitemap.xml`, `robots.txt`**

- `jekyll-sitemap`, `jekyll-seo-tag` 플러그인 추가
- Open Graph 메타 태그 (og:title, og:description, og:type, og:locale=ko_KR)
- Twitter Card 메타 태그
- JSON-LD 구조화 데이터 (BlogPosting 스키마)
- sitemap.xml 동적 생성
- robots.txt 크롤러 허용 및 사이트맵 연결
- canonical URL 태그 추가

## 4. 콘텐츠 인덱스 시스템 (브랜치: improve/content-index)

**파일: `_posts/*`, `_includes/nav.html`, `_includes/series-nav.html`, `_layouts/category.html`, `categories/`, `tags/`**

- 포스트에 `category` 필드 추가 (정치경제, 철학, 서평)
- 하버마스 관련 3편에 `series: "하버마스 추모"` 설정
- 카테고리 아카이브 페이지 6개: 정치경제, 철학, 서평, 화폐이론, 기본소득, 한국자본시장
- 태그 전체 목록 아카이브 페이지
- 시리즈 네비게이션 컴포넌트 (같은 시리즈 글 목록 자동 표시)
- 네비게이션 바에 카테고리/태그 링크 추가

## 5. 3개 브랜치 main 머지

- improve/design → main (Fast-forward)
- improve/seo → main (Auto-merge, 충돌 없음)
- improve/content-index → main (Auto-merge, 충돌 없음)

## 6. 기본소득 콘텐츠 업로드

**기존 자료 발굴 (~/기본사회/ 디렉토리)**

새 포스트 3편 추가 (기본소득 카테고리, "농어촌기본소득 논쟁" 시리즈):

1. **조선일보 칼럼** — "[동서남북] 요지경 농어촌기본소득" (2026-02-27)
   - 원본: `~/기본사회/조선일보 농어촌기본소득 비판 칼럼.rtf`
2. **노컷뉴스 기고** — "농어촌기본소득이 '제로섬'·'공짜돈'이라는 착각" (2026-03-04)
   - 원본: `~/기본사회/송종운 노컷뉴스 기고.rtfd`
3. **시뮬레이션 분석** — "신안군 농어촌기본소득 시뮬레이션 — 5가지 건설적 질문에 대한 정량적 분석" (2026-03-22)
   - 원본: `~/기본사회/sinan_simulation.py` 기반으로 작성

## 7. 메인 페이지 카테고리 그리드

- 히어로 섹션 아래에 6개 카테고리 아이콘 그리드 추가
- 각 카테고리별 글 수 표시
- hover 시 그라디언트 효과

## 8. 인터랙티브 대시보드

- `sinan-dashboard.html` — Chart.js 기반 신안군 시뮬레이션 대시보드
- 원본: `~/기본사회/sinan_dashboard.html`
- 시뮬레이션 포스트에서 링크 연결

## 9. 노컷뉴스 기고문 → 시뮬레이션 링크 연결

- 기고문 본문 상단에 시뮬레이션 분석 포스트로 가는 링크 추가

## 10. GoatCounter 방문자 분석 추가

- `_layouts/default.html`에 GoatCounter 스크립트 삽입
- 대시보드: https://menwchen.goatcounter.com (계정 생성 필요)

---

## 최종 사이트 구조

```
menwchen.github.io/
├── _config.yml (SEO 플러그인, author, lang 추가)
├── _includes/
│   ├── head.html (타이포그래피 + OG 메타 + 반응형 CSS)
│   ├── nav.html (홈, 블로그, 카테고리, 태그)
│   ├── og-meta.html (Open Graph + Twitter Card + JSON-LD)
│   └── series-nav.html (시리즈 네비게이션)
├── _layouts/
│   ├── default.html (GoatCounter 추가)
│   ├── post.html (← 홈으로 링크, 시리즈 nav)
│   └── category.html (카테고리 아카이브)
├── _posts/ (총 7편)
│   ├── 2026-02-27-rural-basic-income-criticism.md (기본소득)
│   ├── 2026-03-04-rural-basic-income-rebuttal.md (기본소득)
│   ├── 2026-03-15-us-iran-war-korea-analysis.md (정치경제)
│   ├── 2026-03-16-empires-of-ideas-habermas-review.md (서평)
│   ├── 2026-03-16-habermas-tribute.md (철학)
│   ├── 2026-03-16-habermas-tribute-en.md (철학)
│   └── 2026-03-22-sinan-basic-income-simulation.md (기본소득)
├── categories/ (6개 카테고리 페이지)
├── tags/index.html
├── sitemap.xml
├── robots.txt
├── sinan-dashboard.html (인터랙티브 대시보드)
└── index.html (카테고리 그리드 + 최근 글)
```

## 커밋 히스토리 (이번 세션)

```
ad9db4c GoatCounter 방문자 분석 추가
f3680b4 노컷뉴스 기고문에 시뮬레이션 분석 링크 추가
5de83f3 포스트에서 소스 코드 링크 제거
982b5ee 소스 코드 파일 제거
1588993 대시보드 permalink 명시 추가
2775fbb 신안군 기본소득 시뮬레이션 분석 포스트 및 대시보드 추가
6188dc9 기본소득 기고문 2편 추가 및 메인 페이지 카테고리 그리드 추가
27e384e 콘텐츠 인덱스: 카테고리 분류 시스템, 태그 아카이브, 시리즈 네비게이션
b470659 SEO 강화: Open Graph, 구조화 데이터, 사이트맵, robots.txt 추가
b5b4c62 디자인 개선: 한글 타이포그래피 최적화 및 모바일 반응형 강화
```
