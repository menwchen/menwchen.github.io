"""
신안군 농어촌기본소득 시뮬레이션
=================================
5가지 건설적 질문에 대한 정량적 분석

모델 구성:
  1) 인구 동태 시뮬레이션 (반사실적 추론 포함)
  2) 지역경제 승수효과 분석
  3) 월 15만 원 임계점 분석
  4) 지역상품권 소비 제약 분석
  5) 공공서비스 인프라 부하 분석
"""

import numpy as np
import pandas as pd
import json, os

np.random.seed(42)

# ═══════════════════════════════════════════════
# 기초 데이터 (언론 보도 및 공개 통계 기반)
# ═══════════════════════════════════════════════

# 신안군 기초 데이터
SINAN_POP_BASE = 39_500        # 기본소득 선정 전 인구 (2025년말 추정)
SINAN_POP_AFTER_4M = 42_500    # 선정 후 4개월 (+3,000명, +7.6%)
MOKPO_POP_BASE = 215_000       # 목포 기초인구
MOKPO_POP_CHANGE = -3_300      # 같은 기간 목포 인구 변화

# 청산면 참조 데이터 (5년 실험)
CHEONGSAN_POP_BASE = 2_800
CHEONGSAN_INITIAL_SPIKE = 0.10   # 초기 10% 인구 증가
CHEONGSAN_FINAL_CHANGE = -0.014  # 5년 후 -1.4%
YEONCHEON_FINAL_CHANGE = -0.006  # 연천군 전체 같은 기간 -0.6%

# 농어촌 기본소득 정책 파라미터
MONTHLY_PAYMENT = 150_000      # 월 15만 원
EXPERIMENT_MONTHS = 24         # 2년
TOTAL_BUDGET_2Y = 1.2e12       # 1조 2천억 원 (2년)

# 농어촌 구조적 감소율 (연간)
RURAL_ANNUAL_DECLINE = -0.025   # 농어촌 평균 연간 -2.5%
SINAN_ANNUAL_DECLINE = -0.030   # 신안 자체 감소율 (도서 지역, 더 가파름)

# ═══════════════════════════════════════════════
# Q1: 실험 설계 — 반사실적 추론 시뮬레이션
# ═══════════════════════════════════════════════

def simulate_population_dynamics(months=60):
    """
    신안군 인구 동태를 3개 시나리오로 시뮬레이션:
      A) 기본소득 없는 반사실적 세계 (counterfactual)
      B) 기본소득 있는 현실 세계 (실제 관측에 근사)
      C) 목포 인구 동태 (독립적 추세 vs 제로섬 검증)
    """
    t = np.arange(months + 1)  # 0 ~ 60개월

    # ── 시나리오 A: 반사실적 세계 (기본소득 없음) ──
    # 신안은 도서 지역 특성상 연간 -3% 구조적 감소
    monthly_decline_sinan = (1 + SINAN_ANNUAL_DECLINE) ** (1/12) - 1
    pop_counterfactual = SINAN_POP_BASE * (1 + monthly_decline_sinan) ** t
    # 약간의 랜덤 노이즈 추가 (계절성 등)
    noise_cf = np.random.normal(0, 30, len(t))
    noise_cf[0] = 0
    pop_counterfactual = pop_counterfactual + np.cumsum(noise_cf)

    # ── 시나리오 B: 기본소득 시행 세계 ──
    pop_with_bi = np.copy(pop_counterfactual)

    # Phase 1: 초기 급증 (0~4개월) - 주민등록 이동 효과
    # 실제 관측: +3,000명 in 4 months
    initial_influx_total = 3000
    # 유입 유형 분해 (추정)
    admin_registration = 0.35   # 행정상 주소 정리 (35%)
    actual_relocation = 0.25    # 실제 거주지 이전 (25%)
    accelerated_return = 0.25   # 귀농귀촌 앞당김 (25%)
    opportunistic = 0.15        # 기회주의적 이동 (15%)

    for m in range(1, min(5, months+1)):
        influx = initial_influx_total * (1 - np.exp(-1.2 * m)) / (1 - np.exp(-1.2 * 4))
        pop_with_bi[m] = pop_counterfactual[m] + influx

    # Phase 2: 안정화 (5~24개월) - 일부 이탈, 일부 정착
    # 기회주의적 이동자: 상품권 기간 끝나면 대부분 이탈
    # 행정 정리: 유지
    # 실제 이전: 70% 정착
    # 귀농귀촌: 60% 정착
    for m in range(5, min(25, months+1)):
        months_since_start = m
        # 기회주의적 이동자 점진 이탈 (월 5%씩)
        opportunistic_remain = max(0, initial_influx_total * opportunistic * (1 - 0.05 * (m - 4)))
        # 행정 정리: 대부분 유지
        admin_remain = initial_influx_total * admin_registration * 0.95
        # 실제 이전: 서서히 일부 이탈
        actual_remain = initial_influx_total * actual_relocation * max(0.6, 1 - 0.015 * (m - 4))
        # 귀농귀촌: 일부 정착 실패
        return_remain = initial_influx_total * accelerated_return * max(0.5, 1 - 0.02 * (m - 4))
        # 추가 자연 유입 (기본소득 효과로 인한 추가 유입, 월 20~50명)
        natural_additional = 30 * np.log(1 + m/6)

        total_net = opportunistic_remain + admin_remain + actual_remain + return_remain + natural_additional
        pop_with_bi[m] = pop_counterfactual[m] + total_net

    # Phase 3: 기본소득 종료 후 (25~60개월)
    if months >= 25:
        net_at_end = pop_with_bi[24] - pop_counterfactual[24]
        for m in range(25, months+1):
            months_after_end = m - 24
            # 기회주의적: 모두 이탈
            # 행정 정리: 유지 (90%)
            # 실제 이전: 정착자 (50~60%)
            # 귀농귀촌: 정착자 (40~50%)
            retention_rate = 0.45 + 0.10 * np.exp(-0.05 * months_after_end)
            retained = net_at_end * retention_rate
            pop_with_bi[m] = pop_counterfactual[m] + retained

    # ── 목포 인구 동태 ──
    # 목포는 독자적 감소 추세 (-1.5%/년) + 신안 효과 일부
    mokpo_monthly_decline = (1 + (-0.015)) ** (1/12) - 1
    pop_mokpo = MOKPO_POP_BASE * (1 + mokpo_monthly_decline) ** t
    noise_mokpo = np.random.normal(0, 80, len(t))
    noise_mokpo[0] = 0
    pop_mokpo = pop_mokpo + np.cumsum(noise_mokpo)

    # 신안 기본소득 발표 후 목포→신안 이동 효과 (전체 감소의 약 30~40% 추정)
    pop_mokpo_with_effect = np.copy(pop_mokpo)
    for m in range(1, min(5, months+1)):
        sinan_effect_on_mokpo = -initial_influx_total * 0.35 * (1 - np.exp(-1.2 * m)) / (1 - np.exp(-1.2 * 4))
        pop_mokpo_with_effect[m] = pop_mokpo[m] + sinan_effect_on_mokpo
    for m in range(5, months+1):
        pop_mokpo_with_effect[m] = pop_mokpo[m] - initial_influx_total * 0.35 * max(0.3, np.exp(-0.02 * (m-4)))

    return {
        'months': t,
        'sinan_counterfactual': pop_counterfactual,
        'sinan_with_bi': pop_with_bi,
        'mokpo_independent': pop_mokpo,
        'mokpo_with_sinan_effect': pop_mokpo_with_effect,
        'influx_decomposition': {
            'admin_registration': admin_registration,
            'actual_relocation': actual_relocation,
            'accelerated_return': accelerated_return,
            'opportunistic': opportunistic,
        }
    }


# ═══════════════════════════════════════════════
# Q2: 2년 vs 5년 — 정착률 시뮬레이션
# ═══════════════════════════════════════════════

def simulate_retention_by_duration():
    """실험 기간에 따른 인구 정착률 추정"""
    durations = [12, 24, 36, 48, 60]  # months
    results = []

    for dur in durations:
        # 기간이 길수록 정착 인프라 구축, 커뮤니티 형성 가능
        # 로지스틱 함수로 정착률 모델링
        base_retention = 0.30  # 1년이면 30% 정착
        max_retention = 0.65   # 최대 65% (5년)
        k = 0.06  # 성장률
        retention = base_retention + (max_retention - base_retention) * (1 - np.exp(-k * dur))

        # 유형별 정착률
        admin_ret = min(0.95, 0.85 + 0.003 * dur)  # 행정 정리: 높은 유지율
        actual_ret = min(0.80, 0.40 + 0.008 * dur)  # 실제 이전: 기간에 비례
        return_ret = min(0.70, 0.30 + 0.008 * dur)  # 귀농귀촌: 기간에 비례
        opportunistic_ret = max(0.05, 0.20 - 0.004 * dur)  # 기회주의: 급감

        total_ret = (0.35 * admin_ret + 0.25 * actual_ret +
                     0.25 * return_ret + 0.15 * opportunistic_ret)

        results.append({
            'duration_months': dur,
            'duration_years': dur / 12,
            'overall_retention': total_ret,
            'admin_retention': admin_ret,
            'actual_retention': actual_ret,
            'return_retention': return_ret,
            'opportunistic_retention': opportunistic_ret,
            'estimated_permanent_pop_gain': int(3000 * total_ret),
        })

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════
# Q3: 월 15만 원 임계점 분석
# ═══════════════════════════════════════════════

def analyze_payment_threshold():
    """월 지급액에 따른 행동 변화 임계점 분석"""
    amounts = [50000, 100000, 150000, 200000, 300000, 500000]
    results = []

    for amt in amounts:
        # 2인 가구 기준 월 소득 보충 비율 (농어촌 평균 가구소득 ~250만원 추정)
        rural_avg_income = 2_500_000
        household_2p = amt * 2  # 2인 수령
        income_supplement_ratio = household_2p / rural_avg_income

        # 행동 변화 확률 (로지스틱 모델)
        # 임계점: 소득 보충 비율 10% 전후에서 유의미한 변화 시작
        k_behavior = 15
        midpoint = 0.12  # 12% 소득 보충이 행동 변화 전환점
        prob_behavior_change = 1 / (1 + np.exp(-k_behavior * (income_supplement_ratio - midpoint)))

        # 주소 이전 의향 (더 낮은 임계점)
        prob_registration = min(0.95, 1 / (1 + np.exp(-25 * (income_supplement_ratio - 0.04))))

        # 실제 거주 이전 의향 (더 높은 임계점)
        prob_actual_move = 1 / (1 + np.exp(-12 * (income_supplement_ratio - 0.18)))

        # 지역 내 소비 증가율
        local_spending_increase = min(0.30, income_supplement_ratio * 0.8)

        results.append({
            'monthly_amount': amt,
            'monthly_amount_만원': amt // 10000,
            'household_2p_monthly': household_2p,
            'income_supplement_ratio': income_supplement_ratio,
            'prob_registration_move': prob_registration,
            'prob_behavior_change': prob_behavior_change,
            'prob_actual_relocation': prob_actual_move,
            'local_spending_increase': local_spending_increase,
        })

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════
# Q3-2: 지역경제 승수효과 분석
# ═══════════════════════════════════════════════

def simulate_economic_multiplier():
    """신안군 지역경제 승수효과 시뮬레이션"""
    pop_receiving = SINAN_POP_AFTER_4M  # 수령 인구
    monthly_injection = pop_receiving * MONTHLY_PAYMENT  # 월 투입액

    # 지역상품권 특성
    local_spending_rate = 1.0   # 100% 지역 내 사용 (상품권 특성)
    leakage_first_round = 0.40  # 1차 소비 후 40%는 지역 외 유출 (도매 구매, 원자재 등)
    leakage_subsequent = 0.55   # 이후 라운드 유출률

    # 승수 계산 (케인지안 승수)
    # 1차 라운드: 전액 지역 소비
    # 2차 라운드: (1 - leakage_first) × 소비성향(0.7)
    # 3차+ 라운드: 점차 감소
    rounds = 10
    spending_by_round = np.zeros(rounds)
    spending_by_round[0] = monthly_injection * local_spending_rate
    for r in range(1, rounds):
        leakage = leakage_first_round if r == 1 else leakage_subsequent
        mpc = 0.70  # 한계소비성향
        spending_by_round[r] = spending_by_round[r-1] * (1 - leakage) * mpc

    total_economic_effect = np.sum(spending_by_round)
    multiplier = total_economic_effect / monthly_injection

    # 연간 효과
    annual_injection = monthly_injection * 12
    annual_total_effect = total_economic_effect * 12

    # 신안군 GRDP 대비 (추정: 농어촌 군 단위 ~5,000억~8,000억)
    sinan_grdp_estimate = 6_000e8  # 6,000억 원
    grdp_impact_ratio = annual_total_effect / sinan_grdp_estimate

    return {
        'monthly_injection': monthly_injection,
        'annual_injection': annual_injection,
        'spending_by_round': spending_by_round.tolist(),
        'multiplier': multiplier,
        'annual_total_effect': annual_total_effect,
        'sinan_grdp_estimate': sinan_grdp_estimate,
        'grdp_impact_ratio': grdp_impact_ratio,
        'leakage_analysis': {
            'first_round_leakage': leakage_first_round,
            'subsequent_leakage': leakage_subsequent,
            'effective_local_retention': total_economic_effect / (monthly_injection * rounds) if monthly_injection > 0 else 0,
        }
    }


# ═══════════════════════════════════════════════
# Q4: 지역상품권 소비 제약 분석
# ═══════════════════════════════════════════════

def analyze_voucher_constraints():
    """지역상품권의 소비 자유도 분석"""
    # 신안군 업종 분포 추정 (도서 지역 특성)
    expenditure_categories = {
        '식료품·생필품': {'share_of_need': 0.35, 'voucher_usable': 0.95, 'adequacy': 'high'},
        '의료·약국': {'share_of_need': 0.15, 'voucher_usable': 0.30, 'adequacy': 'low'},
        '교통·연료': {'share_of_need': 0.12, 'voucher_usable': 0.60, 'adequacy': 'medium'},
        '교육·학원': {'share_of_need': 0.08, 'voucher_usable': 0.10, 'adequacy': 'very_low'},
        '의류·생활용품': {'share_of_need': 0.10, 'voucher_usable': 0.70, 'adequacy': 'medium'},
        '외식·카페': {'share_of_need': 0.08, 'voucher_usable': 0.85, 'adequacy': 'high'},
        '통신·공과금': {'share_of_need': 0.07, 'voucher_usable': 0.20, 'adequacy': 'low'},
        '기타 서비스': {'share_of_need': 0.05, 'voucher_usable': 0.40, 'adequacy': 'low'},
    }

    # 가중 평균 사용가능률
    total_usability = sum(
        v['share_of_need'] * v['voucher_usable']
        for v in expenditure_categories.values()
    )

    # 소비 자유도 지수 (0~1)
    freedom_index = total_usability

    # 비사용 금액 추정 (월 15만원 중)
    effective_spending = MONTHLY_PAYMENT * freedom_index
    constrained_spending = MONTHLY_PAYMENT - effective_spending

    return {
        'categories': expenditure_categories,
        'weighted_usability': total_usability,
        'freedom_index': freedom_index,
        'monthly_effective': effective_spending,
        'monthly_constrained': constrained_spending,
        'monthly_payment': MONTHLY_PAYMENT,
    }


# ═══════════════════════════════════════════════
# Q5: 인프라 부하 분석
# ═══════════════════════════════════════════════

def analyze_infrastructure_load():
    """인구 급증 시 공공서비스 인프라 부하 분석"""
    # 신안군 기존 인프라 수용 능력 (추정)
    infra = {
        '의료기관': {
            'capacity_base': 39_500,  # 기존 인구 대상 설계
            'current_load': 0.75,     # 현재 가동률 75%
            'pop_after': 42_500,
            'expansion_needed': True,
        },
        '초중고교': {
            'capacity_base': 39_500,
            'current_load': 0.45,     # 인구 감소로 여유
            'pop_after': 42_500,
            'expansion_needed': False,  # 학생 유입은 제한적
        },
        '대중교통(여객선)': {
            'capacity_base': 39_500,
            'current_load': 0.80,     # 도서 지역 특성상 높음
            'pop_after': 42_500,
            'expansion_needed': True,
        },
        '주거': {
            'capacity_base': 39_500,
            'current_load': 0.60,     # 빈집 존재하나 거주적합성 문제
            'pop_after': 42_500,
            'expansion_needed': True,
        },
        '상하수도': {
            'capacity_base': 39_500,
            'current_load': 0.65,
            'pop_after': 42_500,
            'expansion_needed': False,  # 여유 있음
        },
    }

    results = {}
    for name, data in infra.items():
        pop_increase_ratio = data['pop_after'] / data['capacity_base']
        new_load = data['current_load'] * pop_increase_ratio
        overload = max(0, new_load - 1.0)
        stress_level = 'critical' if new_load > 0.95 else ('warning' if new_load > 0.85 else 'ok')

        results[name] = {
            'current_load_pct': data['current_load'] * 100,
            'projected_load_pct': new_load * 100,
            'overload_pct': overload * 100,
            'stress_level': stress_level,
            'expansion_needed': data['expansion_needed'],
        }

    return results


# ═══════════════════════════════════════════════
# 제로섬 검증
# ═══════════════════════════════════════════════

def analyze_zero_sum():
    """제로섬 가설 검증: 목포 감소분이 순전히 신안 이동인가"""
    # 목포 자연 감소 추세 (연간 -1.5%, 4개월분)
    mokpo_natural_decline_4m = MOKPO_POP_BASE * ((1 - 0.015) ** (4/12) - 1)
    # = 약 -1,073명

    # 신안으로 실제 이동한 것으로 추정되는 목포 주민
    # 전체 3,000명 유입 중 목포 출신 비율 추정: 35% (가장 가까운 도시)
    sinan_influx_from_mokpo = 3000 * 0.35  # = 1,050명

    # 목포 총 감소: -3,300명
    # 자연 감소: ~-1,073명
    # 신안 효과: ~-1,050명
    # 기타 요인: ~-1,177명 (타 지역 이동, 경제적 이유 등)

    return {
        'mokpo_total_decline': MOKPO_POP_CHANGE,
        'mokpo_natural_decline_4m': int(mokpo_natural_decline_4m),
        'sinan_effect_on_mokpo': int(sinan_influx_from_mokpo),
        'other_factors': int(MOKPO_POP_CHANGE - mokpo_natural_decline_4m - (-sinan_influx_from_mokpo)),
        'sinan_share_of_mokpo_decline': abs(sinan_influx_from_mokpo / MOKPO_POP_CHANGE),
        'conclusion': 'partial_overlap',  # 제로섬이 아니라 부분적 중첩
    }


# ═══════════════════════════════════════════════
# 실행 및 결과 출력
# ═══════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  신안군 농어촌기본소득 시뮬레이션 결과")
    print("=" * 70)

    # Q1: 인구 동태
    pop = simulate_population_dynamics(months=60)
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q1. 반사실적 추론 — 인구 동태 시뮬레이션   │")
    print("└─────────────────────────────────────────┘")
    print(f"  기본소득 없는 세계 (4개월 후):  {pop['sinan_counterfactual'][4]:,.0f}명")
    print(f"  기본소득 있는 세계 (4개월 후):  {pop['sinan_with_bi'][4]:,.0f}명")
    print(f"  기본소득 순효과 (4개월):       +{pop['sinan_with_bi'][4] - pop['sinan_counterfactual'][4]:,.0f}명")
    print(f"  기본소득 있는 세계 (24개월 후): {pop['sinan_with_bi'][24]:,.0f}명")
    print(f"  기본소득 순효과 (24개월):      +{pop['sinan_with_bi'][24] - pop['sinan_counterfactual'][24]:,.0f}명")
    print(f"  기본소득 종료 후 (36개월):     {pop['sinan_with_bi'][36]:,.0f}명")
    print(f"  기본소득 종료 후 잔존 효과:    +{pop['sinan_with_bi'][36] - pop['sinan_counterfactual'][36]:,.0f}명")

    # 제로섬 분석
    zs = analyze_zero_sum()
    print(f"\n  ── 제로섬 가설 검증 ──")
    print(f"  목포 총 감소: {zs['mokpo_total_decline']:,}명")
    print(f"    ├ 자연 감소 추세:    {zs['mokpo_natural_decline_4m']:,}명 ({abs(zs['mokpo_natural_decline_4m']/zs['mokpo_total_decline'])*100:.0f}%)")
    print(f"    ├ 신안 이동 효과:    {-zs['sinan_effect_on_mokpo']:,}명 ({zs['sinan_share_of_mokpo_decline']*100:.0f}%)")
    print(f"    └ 기타 요인:        {zs['other_factors']:,}명 ({abs(zs['other_factors']/zs['mokpo_total_decline'])*100:.0f}%)")
    print(f"  → 결론: 목포 감소의 약 {zs['sinan_share_of_mokpo_decline']*100:.0f}%만 신안 효과, 나머지는 독립적 추세")

    # Q2: 정착률
    retention = simulate_retention_by_duration()
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q2. 실험 기간별 인구 정착률 추정         │")
    print("└─────────────────────────────────────────┘")
    for _, row in retention.iterrows():
        print(f"  {row['duration_years']:.0f}년: 정착률 {row['overall_retention']*100:.1f}% → "
              f"영구 인구 증가 약 +{row['estimated_permanent_pop_gain']:,}명")
    print(f"\n  → 2년 실험: 정착률 {retention[retention['duration_months']==24]['overall_retention'].values[0]*100:.1f}%")
    print(f"  → 5년 실험: 정착률 {retention[retention['duration_months']==60]['overall_retention'].values[0]*100:.1f}%")
    print(f"  → 차이: 5년 실험 시 2년 대비 약 {(retention[retention['duration_months']==60]['estimated_permanent_pop_gain'].values[0] - retention[retention['duration_months']==24]['estimated_permanent_pop_gain'].values[0]):,}명 추가 정착")

    # Q3: 임계점 분석
    threshold = analyze_payment_threshold()
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q3. 월 지급액별 행동 변화 임계점          │")
    print("└─────────────────────────────────────────┘")
    for _, row in threshold.iterrows():
        amt = row['monthly_amount_만원']
        print(f"  월 {amt:>3.0f}만원: 소득보충 {row['income_supplement_ratio']*100:5.1f}% | "
              f"주소이전 {row['prob_registration_move']*100:4.0f}% | "
              f"실제이주 {row['prob_actual_relocation']*100:4.0f}% | "
              f"행동변화 {row['prob_behavior_change']*100:4.0f}%")
    print(f"\n  → 현행 15만원: 주소이전은 강하게 유발하나, 실질적 행동변화(이주·경제활동)는 전환점 직전")
    print(f"  → 20만원 이상에서 행동변화 확률이 유의미하게 상승")

    # 경제 승수
    econ = simulate_economic_multiplier()
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q3-2. 지역경제 승수효과                   │")
    print("└─────────────────────────────────────────┘")
    print(f"  월 투입액: {econ['monthly_injection']/1e8:.1f}억 원")
    print(f"  연 투입액: {econ['annual_injection']/1e8:.1f}억 원")
    print(f"  승수 효과: ×{econ['multiplier']:.2f}")
    print(f"  연간 총 경제효과: {econ['annual_total_effect']/1e8:.1f}억 원")
    print(f"  신안 GRDP 대비: {econ['grdp_impact_ratio']*100:.1f}%")
    print(f"  1차 유출률: {econ['leakage_analysis']['first_round_leakage']*100:.0f}%")

    # Q4: 소비 제약
    voucher = analyze_voucher_constraints()
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q4. 지역상품권 소비 자유도 분석            │")
    print("└─────────────────────────────────────────┘")
    for cat, data in voucher['categories'].items():
        usable = data['voucher_usable'] * 100
        adequacy = {'high': '●', 'medium': '◐', 'low': '○', 'very_low': '✕'}[data['adequacy']]
        print(f"  {cat:<15s}: 필요비중 {data['share_of_need']*100:4.0f}% | 사용가능 {usable:4.0f}% | 적절성 {adequacy}")
    print(f"\n  종합 소비 자유도: {voucher['freedom_index']*100:.1f}%")
    print(f"  월 15만원 중 실효 사용: {voucher['monthly_effective']/10000:.1f}만원")
    print(f"  제약 받는 금액: {voucher['monthly_constrained']/10000:.1f}만원")

    # Q5: 인프라 부하
    infra = analyze_infrastructure_load()
    print("\n┌─────────────────────────────────────────┐")
    print("│  Q5. 인구 급증 시 인프라 부하 분석          │")
    print("└─────────────────────────────────────────┘")
    stress_icon = {'ok': '🟢', 'warning': '🟡', 'critical': '🔴'}
    for name, data in infra.items():
        icon = stress_icon[data['stress_level']]
        print(f"  {icon} {name:<15s}: 현재 {data['current_load_pct']:.0f}% → 예상 {data['projected_load_pct']:.0f}% "
              f"({'확충 필요' if data['expansion_needed'] else '여유'})")

    # 종합 데이터를 JSON으로 저장 (시각화용)
    all_results = {
        'population': {
            'months': pop['months'].tolist(),
            'sinan_counterfactual': pop['sinan_counterfactual'].tolist(),
            'sinan_with_bi': pop['sinan_with_bi'].tolist(),
            'mokpo_independent': pop['mokpo_independent'].tolist(),
            'mokpo_with_effect': pop['mokpo_with_sinan_effect'].tolist(),
            'influx_decomposition': pop['influx_decomposition'],
        },
        'retention': retention.to_dict('records'),
        'threshold': threshold.to_dict('records'),
        'economic': econ,
        'voucher': {
            'categories': {k: {'share': v['share_of_need'], 'usable': v['voucher_usable']}
                           for k, v in voucher['categories'].items()},
            'freedom_index': voucher['freedom_index'],
        },
        'infrastructure': infra,
        'zero_sum': zs,
    }

    with open('/sessions/gallant-practical-hawking/sim_results.json', 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("  시뮬레이션 완료. 결과 → sim_results.json")
    print("=" * 70)

if __name__ == '__main__':
    main()
