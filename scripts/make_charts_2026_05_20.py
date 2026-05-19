#!/usr/bin/env python3
"""
2026-05-20 포스트용 차트 5종 생성
- chart1: 인과 연쇄 다이어그램
- chart2: 미국 주요 금리 추이
- chart3: 미국 인플레이션 지표
- chart4: NAHB 주택시장지수 시계열 (2024~2026)
- chart5: 한미 정책금리 / 10년물 비교 (한국 종속성)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# 한글 폰트
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

# 먹사연 팔레트
C = {
    'bg':        '#FAF6F0',
    'ink':       '#1B2A4E',
    'accent':    '#A2503A',
    'secondary': '#6B5D4F',
    'light':     '#D9C9B8',
    'grid':      '#E5DDD0',
    'amber':     '#C68B59',
    'muted':     '#8A7A6A',
}

OUT_DIR = '/Users/jongunsong/menwchen.github.io/assets/images'
PREFIX  = '2026-05-20-'


# ============================================================
# Chart 1. 인과 연쇄 다이어그램
# ============================================================
def chart1():
    fig, ax = plt.subplots(figsize=(13, 6.5))
    fig.patch.set_facecolor(C['bg'])
    ax.set_facecolor(C['bg'])
    ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis('off')

    stages = [
        {'x': 7,  'title': '① 외생 충격',  'main': '이란 전쟁\n호르무즈 봉쇄', 'sub': '2026.02.28~'},
        {'x': 26, 'title': '② 1차 전이',  'main': '유가 급등',                  'sub': 'Brent $114/배럴\n(+44%)'},
        {'x': 45, 'title': '③ 2차 전이',  'main': '인플레 재점화',              'sub': 'CPI 3.8%\nPPI 6.0%'},
        {'x': 64, 'title': '④ 금융시장',  'main': '채권금리 급등',              'sub': '30년물 5.16%\n(19년래 최고)'},
        {'x': 83, 'title': '⑤ 민생 충격',  'main': '주택시장 동결',              'sub': '모기지 6.49%\nNAHB 37'},
    ]
    for i, s in enumerate(stages):
        x = s['x']
        ax.text(x, 51, s['title'], ha='center', va='center', fontsize=10.5, color=C['muted'])
        box = FancyBboxPatch((x - 8, 30), 16, 14,
                             boxstyle="round,pad=0.4,rounding_size=0.6",
                             linewidth=1.8, edgecolor=C['ink'],
                             facecolor='white' if i < 4 else C['accent'])
        ax.add_patch(box)
        ax.text(x, 37, s['main'], ha='center', va='center', fontsize=11.5,
                color=C['ink'] if i < 4 else 'white', weight='bold')
        ax.text(x, 22, s['sub'], ha='center', va='top', fontsize=10, color=C['secondary'])
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch(
                (x + 8.5, 37), (stages[i+1]['x'] - 8.5, 37),
                arrowstyle='->,head_width=4,head_length=6',
                linewidth=2, color=C['amber']))

    ax.add_patch(FancyBboxPatch((30, 5), 40, 7,
                                 boxstyle="round,pad=0.3,rounding_size=0.4",
                                 linewidth=1.5, edgecolor=C['accent'],
                                 facecolor=C['light']))
    ax.text(50, 8.5,
            '⑥ 정치적 의례 : 5/22 백악관 잔디밭에서 워시(Warsh) 의장 취임식',
            ha='center', va='center', fontsize=11, color=C['ink'], weight='bold')
    ax.add_patch(FancyArrowPatch((50, 12), (50, 22),
                                 arrowstyle='->,head_width=4,head_length=6',
                                 linewidth=1.5, color=C['accent'],
                                 linestyle=(0, (4, 3))))
    ax.text(54, 17, '인하 압박', fontsize=10, color=C['accent'], style='italic')
    ax.text(50, 58, '이란 전쟁 → 미국 주택시장 동결 → 백악관 취임식의 인과 연쇄',
            ha='center', va='center', fontsize=14.5, color=C['ink'], weight='bold')

    plt.savefig(f'{OUT_DIR}/{PREFIX}causal-chain.png',
                facecolor=C['bg'], edgecolor='none')
    plt.close()
    print('chart1 OK')


# ============================================================
# Chart 2. 미국 주요 금리 추이
# ============================================================
def chart2():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.patch.set_facecolor(C['bg'])
    ax.set_facecolor(C['bg'])

    months = ['2025.10','2025.11','2025.12','2026.01','2026.02','2026.03','2026.04','2026.05']
    x = np.arange(len(months))
    bond_30y = [4.55, 4.50, 4.62, 4.65, 4.68, 4.78, 4.88, 5.16]
    bond_10y = [4.10, 4.05, 4.18, 4.20, 4.22, 4.35, 4.48, 4.63]
    mortgage = [6.85, 6.70, 6.55, 6.45, 6.30, 6.25, 6.30, 6.49]
    fed_top  = [4.50, 4.25, 4.00, 3.75, 3.75, 3.75, 3.75, 3.75]

    ax.plot(x, mortgage, marker='o', linewidth=2.4, color=C['accent'], label='30년 고정 모기지', markersize=6.5)
    ax.plot(x, bond_30y, marker='s', linewidth=2.4, color=C['ink'], label='30년 국채 수익률', markersize=6.5)
    ax.plot(x, bond_10y, marker='^', linewidth=2.2, color=C['amber'], label='10년 국채 수익률', markersize=6.5)
    ax.plot(x, fed_top, marker='D', linewidth=1.8, color=C['secondary'], label='연준 정책금리 상단', markersize=5, linestyle='--')

    ax.axvline(4.0, color=C['accent'], linestyle=':', linewidth=1.5, alpha=0.7)
    ax.text(4.08, 7.0, '이란 전쟁 발발\n(2026.02.28)', fontsize=10, color=C['accent'], style='italic', va='top')
    ax.annotate('5.16%\n(19년래 최고)', xy=(7, 5.16), xytext=(5.8, 5.75),
                fontsize=10, color=C['ink'], weight='bold',
                arrowprops=dict(arrowstyle='->', color=C['ink'], lw=1.2))

    ax.set_xticks(x); ax.set_xticklabels(months, fontsize=10, color=C['ink'])
    ax.set_ylabel('금리 (%)', fontsize=11, color=C['ink'])
    ax.set_ylim(3.3, 7.3)
    ax.grid(True, color=C['grid'], linewidth=0.8, alpha=0.7); ax.set_axisbelow(True)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(C['muted'])
    ax.tick_params(colors=C['ink'])
    ax.legend(loc='center right', fontsize=10, frameon=True, facecolor='white', edgecolor=C['light'])
    ax.set_title('미국 주요 금리 추이 (2025.10 ~ 2026.5)', fontsize=14, color=C['ink'], weight='bold', pad=12)
    fig.text(0.13, 0.02, '자료: U.S. Treasury, Freddie Mac, MBA | 작성: 먹고사는문제연구소',
             fontsize=9, color=C['muted'])
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(f'{OUT_DIR}/{PREFIX}us-rates.png', facecolor=C['bg'], edgecolor='none')
    plt.close()
    print('chart2 OK')


# ============================================================
# Chart 3. 미국 인플레이션
# ============================================================
def chart3():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.patch.set_facecolor(C['bg'])
    ax.set_facecolor(C['bg'])

    months = ['2025.10','2025.11','2025.12','2026.01','2026.02','2026.03','2026.04','2026.Q4(전망)']
    x = np.arange(len(months))
    cpi = [2.65, 2.60, 2.55, 2.40, 2.55, 3.30, 3.80, None]
    ppi = [2.40, 2.30, 2.30, 2.50, 2.70, 4.30, 6.00, None]
    pce = [2.80, 2.75, 2.70, 2.65, 2.80, None, None, None]

    w = 0.27
    ax.bar([xi - w for xi, v in zip(x, cpi) if v is not None],
           [v for v in cpi if v is not None], w, color=C['ink'], label='헤드라인 CPI', alpha=0.95)
    ax.bar([xi for xi, v in zip(x, ppi) if v is not None],
           [v for v in ppi if v is not None], w, color=C['accent'], label='도매물가 PPI', alpha=0.95)
    ax.bar([xi + w for xi, v in zip(x, pce) if v is not None],
           [v for v in pce if v is not None], w, color=C['amber'], label='핵심 PCE', alpha=0.95)
    ax.bar(x[-1] + w, 4.0, w, color='none', edgecolor=C['amber'],
           linewidth=2.2, linestyle='--', label='핵심 PCE 전망(연말)', hatch='//')

    ax.axhline(2.0, color=C['secondary'], linestyle='--', linewidth=1.8, alpha=0.8)
    ax.text(0.1, 2.18, '연준 인플레이션 목표 (2%)', fontsize=10, color=C['secondary'], style='italic')
    ax.axvline(4.5, color=C['accent'], linestyle=':', linewidth=1.5, alpha=0.7)
    ax.text(4.55, 5.7, '이란 전쟁 발발\n(2026.02.28)', fontsize=10, color=C['accent'], style='italic', va='top')
    ax.annotate('PPI 6.0%\n(3년래 최대)', xy=(6, 6.0), xytext=(5.3, 6.9),
                fontsize=10, color=C['accent'], weight='bold',
                arrowprops=dict(arrowstyle='->', color=C['accent'], lw=1.2))

    ax.set_xticks(x); ax.set_xticklabels(months, fontsize=9.5, color=C['ink'], rotation=12)
    ax.set_ylabel('전년 동월 대비 변화율 (%, YoY)', fontsize=11, color=C['ink'])
    ax.set_ylim(0, 7.5)
    ax.grid(True, axis='y', color=C['grid'], linewidth=0.8, alpha=0.7); ax.set_axisbelow(True)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(C['muted'])
    ax.tick_params(colors=C['ink'])
    ax.legend(loc='upper left', fontsize=10, frameon=True, facecolor='white', edgecolor=C['light'])
    ax.set_title('미국 인플레이션 지표 — 이란 전쟁 전후 (2025.10 ~ 2026)',
                 fontsize=14, color=C['ink'], weight='bold', pad=12)
    fig.text(0.13, 0.02, '자료: BLS, BEA, Cato Institute (PCE 연말 전망) | 작성: 먹고사는문제연구소',
             fontsize=9, color=C['muted'])
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(f'{OUT_DIR}/{PREFIX}us-inflation.png', facecolor=C['bg'], edgecolor='none')
    plt.close()
    print('chart3 OK')


# ============================================================
# Chart 4. NAHB 주택시장지수 시계열 (2024.04 ~ 2026.05)
# ============================================================
def chart4():
    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor(C['bg'])
    ax.set_facecolor(C['bg'])

    months = [
        '2024.04','2024.05','2024.06','2024.07','2024.08','2024.09',
        '2024.10','2024.11','2024.12','2025.01','2025.02','2025.03',
        '2025.04','2025.05','2025.06','2025.07','2025.08','2025.09',
        '2025.10','2025.11','2025.12','2026.01','2026.02','2026.03',
        '2026.04','2026.05'
    ]
    hmi = [
        51, 45, 43, 42, 39, 41,
        43, 46, 46, 47, 42, 39,
        40, 34, 32, 33, 32, 32,
        37, 38, 39, 39, 37, 38,
        34, 37
    ]
    x = np.arange(len(months))

    # 50 미만 영역 음영
    ax.fill_between(x, 0, 50, where=[h < 50 for h in hmi],
                    color=C['accent'], alpha=0.08, interpolate=True)
    # 50 기준선
    ax.axhline(50, color=C['secondary'], linestyle='--', linewidth=1.8, alpha=0.85)
    ax.text(0.3, 50.6, '기준선 50 (이상=시장 호조)',
            fontsize=10, color=C['secondary'], style='italic')

    # 이란 전쟁 발발
    war_idx = months.index('2026.02')
    ax.axvline(war_idx, color=C['accent'], linestyle=':', linewidth=1.5, alpha=0.7)
    ax.text(war_idx + 0.15, 52.5, '이란 전쟁\n(2026.02.28)',
            fontsize=9.5, color=C['accent'], style='italic', va='top')

    # 라인
    ax.plot(x, hmi, marker='o', linewidth=2.4, color=C['ink'], markersize=6.5,
            markerfacecolor=C['accent'], markeredgecolor=C['ink'])

    # 5월 37 강조
    ax.annotate('5월: 37\n(50 미만 25개월 연속)',
                xy=(len(x)-1, 37), xytext=(len(x)-5.5, 22),
                fontsize=10.5, color=C['ink'], weight='bold',
                arrowprops=dict(arrowstyle='->', color=C['ink'], lw=1.2))

    # 24년 4월: 50선 마지막 돌파
    ax.annotate('2024년 4월\n50선 마지막 돌파',
                xy=(0, 51), xytext=(2, 60),
                fontsize=9.5, color=C['secondary'], style='italic',
                arrowprops=dict(arrowstyle='->', color=C['secondary'], lw=1.0, alpha=0.7))

    # 축 라벨 — 25개씩으로 나눠서 보기 좋게
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=8.5, color=C['ink'], rotation=45, ha='right')
    ax.set_ylabel('NAHB/Wells Fargo HMI', fontsize=11, color=C['ink'])
    ax.set_ylim(15, 65)
    ax.grid(True, axis='y', color=C['grid'], linewidth=0.8, alpha=0.7); ax.set_axisbelow(True)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(C['muted'])
    ax.tick_params(colors=C['ink'])

    ax.set_title('NAHB 주택시장지수 — 50 미만 25개월 연속 (2024.04 ~ 2026.05)',
                 fontsize=14, color=C['ink'], weight='bold', pad=12)
    fig.text(0.13, 0.02, '자료: NAHB/Wells Fargo Housing Market Index | 작성: 먹고사는문제연구소',
             fontsize=9, color=C['muted'])
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(f'{OUT_DIR}/{PREFIX}nahb-timeseries.png', facecolor=C['bg'], edgecolor='none')
    plt.close()
    print('chart4 OK')


# ============================================================
# Chart 5. 한미 정책금리 / 10년물 비교
# ============================================================
def chart5():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5))
    fig.patch.set_facecolor(C['bg'])
    for ax in [ax1, ax2]:
        ax.set_facecolor(C['bg'])
        for s in ['top','right']: ax.spines[s].set_visible(False)
        for s in ['left','bottom']: ax.spines[s].set_color(C['muted'])
        ax.tick_params(colors=C['ink'])

    months = ['2025.10','2025.11','2025.12','2026.01','2026.02','2026.03','2026.04','2026.05']
    x = np.arange(len(months))

    # (A) 정책금리
    kr_base = [3.25, 3.00, 3.00, 2.75, 2.50, 2.50, 2.50, 2.50]
    us_top  = [4.50, 4.25, 4.00, 3.75, 3.75, 3.75, 3.75, 3.75]

    ax1.plot(x, us_top, marker='s', linewidth=2.4, color=C['ink'],
             label='美 연준 정책금리 상단', markersize=6.5)
    ax1.plot(x, kr_base, marker='o', linewidth=2.4, color=C['accent'],
             label='韓 한국은행 기준금리', markersize=6.5)
    ax1.fill_between(x, kr_base, us_top, color=C['amber'], alpha=0.18,
                     label='한미 금리차 (역전)')

    ax1.axvline(4.0, color=C['secondary'], linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(4.1, 4.9, '이란 전쟁\n발발', fontsize=9.5, color=C['secondary'],
             style='italic', va='top')

    # 금리차 annotation
    ax1.annotate('1.25%p\n역전 지속',
                 xy=(7, (3.75+2.50)/2), xytext=(5.5, 3.4),
                 fontsize=10, color=C['accent'], weight='bold',
                 arrowprops=dict(arrowstyle='->', color=C['accent'], lw=1.2))

    ax1.set_xticks(x); ax1.set_xticklabels(months, fontsize=9, color=C['ink'], rotation=20)
    ax1.set_ylabel('정책금리 (%)', fontsize=11, color=C['ink'])
    ax1.set_ylim(2.0, 5.0)
    ax1.grid(True, axis='y', color=C['grid'], linewidth=0.8, alpha=0.7); ax1.set_axisbelow(True)
    ax1.legend(loc='upper right', fontsize=9.5, frameon=True, facecolor='white', edgecolor=C['light'])
    ax1.set_title('한미 정책금리 — 42개월째 이어진 역전',
                  fontsize=12.5, color=C['ink'], weight='bold', pad=10)

    # (B) 10년물 국채 수익률
    kr_10y = [2.95, 2.90, 3.10, 3.20, 3.30, 3.55, 3.75, 4.25]
    us_10y = [4.10, 4.05, 4.18, 4.20, 4.22, 4.35, 4.48, 4.63]

    ax2.plot(x, us_10y, marker='s', linewidth=2.4, color=C['ink'],
             label='美 10년 국채', markersize=6.5)
    ax2.plot(x, kr_10y, marker='o', linewidth=2.4, color=C['accent'],
             label='韓 국고채 10년', markersize=6.5)

    ax2.axvline(4.0, color=C['secondary'], linestyle=':', linewidth=1.5, alpha=0.7)
    ax2.text(4.1, 4.5, '이란 전쟁\n발발', fontsize=9.5, color=C['secondary'],
             style='italic', va='top')

    ax2.annotate('韓 10년물\n4.25%\n(2년반래 최고)',
                 xy=(7, 4.25), xytext=(5.0, 3.2),
                 fontsize=10, color=C['accent'], weight='bold',
                 arrowprops=dict(arrowstyle='->', color=C['accent'], lw=1.2))

    ax2.set_xticks(x); ax2.set_xticklabels(months, fontsize=9, color=C['ink'], rotation=20)
    ax2.set_ylabel('10년 만기 국채 수익률 (%)', fontsize=11, color=C['ink'])
    ax2.set_ylim(2.5, 5.0)
    ax2.grid(True, axis='y', color=C['grid'], linewidth=0.8, alpha=0.7); ax2.set_axisbelow(True)
    ax2.legend(loc='upper left', fontsize=9.5, frameon=True, facecolor='white', edgecolor=C['light'])
    ax2.set_title('한미 10년물 동반 급등 — 韓의 미국 종속성',
                  fontsize=12.5, color=C['ink'], weight='bold', pad=10)

    fig.suptitle('한미 금리 비교 — 준주변부 화폐 거버넌스의 협착',
                 fontsize=14.5, color=C['ink'], weight='bold', y=0.995)
    fig.text(0.13, 0.02,
             '자료: 한국은행 ECOS, U.S. Treasury, Investing.com | 작성: 먹고사는문제연구소',
             fontsize=9, color=C['muted'])
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(f'{OUT_DIR}/{PREFIX}kr-us-rates.png', facecolor=C['bg'], edgecolor='none')
    plt.close()
    print('chart5 OK')


if __name__ == '__main__':
    chart1()
    chart2()
    chart3()
    chart4()
    chart5()
    print('\n5개 차트 생성 완료 →', OUT_DIR)
