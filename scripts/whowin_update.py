#!/usr/bin/env python3
"""
WhoWin · 송영길/인천 연수갑 미디어 텍스트 마이닝 데이터 갱신 스크립트.
GitHub Actions cron 에서 3시간마다 실행되어 data/whowin/songyounggil.json 을 갱신한다.
의존성: 표준 라이브러리만 사용 (urllib, xml.etree, json, re, datetime).
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT_PATH = "data/whowin/songyounggil.json"

QUERIES = [
    "송영길 연수갑",
    "박종진 연수갑",
    "정승연 개혁신당 연수갑",
    "인천 연수구 재보선",
]

KEYWORDS = [
    "KTX 송도역", "GTX-B", "청학역", "재개발", "재건축", "송도유원지",
    "제2경인선", "주안지선", "인천공항", "이재명", "박찬대", "용적률",
    "초선 심정", "돈봉투", "올드보이", "험지", "전대", "전당대회",
    "발상의 전환", "원도심",
]

POSITIVE_WORDS = ["당선", "우세", "복귀", "재기", "압승", "공약",
                  "성장", "발전", "무죄", "지지율", "선두"]
NEGATIVE_WORDS = ["돈봉투", "올드보이", "구설", "험지", "기소", "유죄",
                  "패배", "탈당", "논란", "비판", "공격"]


def fetch_rss(query: str) -> list[dict]:
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=ko&gl=KR&ceid=KR:ko"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "whowin-bot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    root = ET.fromstring(data)
    out = []
    for item in root.iter("item"):
        title_raw = item.findtext("title") or ""
        title = html.unescape(title_raw)
        title = re.sub(r"\s*-\s*[^-]+$", "", title)  # trailing source 제거
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        src_el = item.find("source")
        source = (src_el.text or "") if src_el is not None else ""
        out.append({
            "title": title.strip(),
            "link": link,
            "pubDate": pub,
            "source": source,
            "query": query,
        })
    return out


def dedupe(articles: list[dict]) -> list[dict]:
    seen, out = set(), []
    for a in articles:
        key = a["title"][:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def keyword_freq(corpus: str) -> list[dict]:
    rows = []
    for k in KEYWORDS:
        n = corpus.count(k)
        if n > 0:
            rows.append({"k": k, "n": n})
    rows.sort(key=lambda r: r["n"], reverse=True)
    return rows


def sentiment(articles: list[dict]) -> dict:
    pos = neg = neu = 0
    for a in articles:
        t = a["title"]
        p = sum(t.count(w) for w in POSITIVE_WORDS)
        n = sum(t.count(w) for w in NEGATIVE_WORDS)
        if p > n:
            pos += 1
        elif n > p:
            neg += 1
        else:
            neu += 1
    total = max(1, pos + neg + neu)
    return {
        "positive": pos, "negative": neg, "neutral": neu,
        "positive_pct": round(pos / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
        "neutral_pct": round(neu / total * 100, 1),
    }


def main() -> int:
    all_articles: list[dict] = []
    for q in QUERIES:
        try:
            all_articles.extend(fetch_rss(q))
        except Exception as e:
            print(f"[warn] query failed: {q} -> {e}", file=sys.stderr)
    articles = dedupe(all_articles)[:80]

    corpus = " ".join(a["title"] for a in articles)
    payload = {
        "updated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "district": "인천 연수구갑",
        "election_date": "2026-06-03",
        "candidates": [
            {"name": "송영길", "party": "더불어민주당",
             "color": "#004EA2", "note": "전 대표·전 인천시장·5선"},
            {"name": "박종진", "party": "국민의힘",
             "color": "#E61E2B", "note": "인천시당위원장"},
            {"name": "정승연", "party": "개혁신당",
             "color": "#FF7920", "note": "전 국힘 연수갑 당협위원장"},
        ],
        # 여론조사: 자체 추정이 아니라 최근 공개 조사(뉴스토마토 2026.05) 인용.
        # 실제 API 가 있다면 여기서 갱신하도록 확장 가능.
        "poll": {
            "source": "뉴스토마토 (2026-05)",
            "two_way": {"송영길": 51.7, "박종진": 32.6, "모름": 15.7},
            "active_voters": {"송영길": 60.6, "박종진": 29.3},
            "swing": {"송영길": 53.0, "박종진": 24.5},
        },
        "n_articles": len(articles),
        "keywords": keyword_freq(corpus),
        "sentiment": sentiment(articles),
        "articles": articles[:30],
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[ok] wrote {OUT_PATH} · articles={len(articles)} · "
          f"keywords={len(payload['keywords'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
