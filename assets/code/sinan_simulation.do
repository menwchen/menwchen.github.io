/*==============================================================================
  신안군 농어촌기본소득 시뮬레이션
  ──────────────────────────────────
  5가지 건설적 질문에 대한 정량적 분석

  원본: simulation.py → Stata 변환
  작성: 2026-03-22
  실행: Stata 16+ (mata 포함)

  사용법:
    . do sinan_simulation.do

  출력:
    - sinan_q1_population.dta       (Q1 인구동태 60개월)
    - sinan_q2_retention.dta        (Q2 정착률)
    - sinan_q3_threshold.dta        (Q3 임계점)
    - sinan_q3_multiplier.dta       (Q3-2 승수효과)
    - sinan_q4_voucher.dta          (Q4 소비제약)
    - sinan_q5_infra.dta            (Q5 인프라부하)
    - sinan_zerosum.dta             (제로섬 분해)
==============================================================================*/

clear all
set more off
set seed 42

/*──────────────────────────────────────────────────────────────────────────────
  기초 파라미터 정의
──────────────────────────────────────────────────────────────────────────────*/

// 신안군 기초 데이터
scalar SINAN_POP_BASE       = 39500
scalar SINAN_POP_AFTER_4M   = 42500
scalar MOKPO_POP_BASE       = 215000
scalar MOKPO_POP_CHANGE     = -3300

// 청산면 참조 데이터
scalar CHEONGSAN_POP_BASE       = 2800
scalar CHEONGSAN_INITIAL_SPIKE  = 0.10
scalar CHEONGSAN_FINAL_CHANGE   = -0.014

// 정책 파라미터
scalar MONTHLY_PAYMENT      = 150000
scalar EXPERIMENT_MONTHS    = 24
scalar TOTAL_BUDGET_2Y      = 1.2e12

// 구조적 감소율 (연간)
scalar RURAL_ANNUAL_DECLINE = -0.025
scalar SINAN_ANNUAL_DECLINE = -0.030

// 유입 유형 비율
scalar ALPHA_ADMIN      = 0.35
scalar ALPHA_ACTUAL     = 0.25
scalar ALPHA_RETURN     = 0.25
scalar ALPHA_OPP        = 0.15
scalar I_TOTAL          = 3000

display _n "╔══════════════════════════════════════════════════════════════╗"
display    "║  신안군 농어촌기본소득 시뮬레이션 (Stata 버전)               ║"
display    "╚══════════════════════════════════════════════════════════════╝"


/*==============================================================================
  Q1. 반사실적 추론 — 인구 동태 시뮬레이션 (60개월)
==============================================================================*/

display _n "── Q1. 인구 동태 시뮬레이션 (60개월) ──"

// 월간 감소율 변환
scalar r_monthly_sinan = (1 + SINAN_ANNUAL_DECLINE)^(1/12) - 1
scalar r_monthly_mokpo = (1 + (-0.015))^(1/12) - 1

display "  신안 월간 감소율: " %8.6f r_monthly_sinan
display "  목포 월간 감소율: " %8.6f r_monthly_mokpo

// 데이터셋 생성: 61행 (0~60개월)
quietly {
    set obs 61
    gen int month = _n - 1

    // ── 시나리오 A: 반사실적 세계 (기본소득 없음) ──
    gen double pop_cf = SINAN_POP_BASE * (1 + r_monthly_sinan)^month
    gen double noise_cf = rnormal(0, 30)
    replace noise_cf = 0 if month == 0
    gen double cum_noise_cf = sum(noise_cf)
    replace pop_cf = pop_cf + cum_noise_cf

    // ── 시나리오 B: 기본소득 시행 세계 ──
    gen double pop_bi = pop_cf

    // Phase 1: 초기 급증 (0~4개월)
    forvalues m = 1/4 {
        scalar influx_`m' = I_TOTAL * (1 - exp(-1.2 * `m')) / (1 - exp(-1.2 * 4))
        replace pop_bi = pop_cf + influx_`m' if month == `m'
    }

    // Phase 2: 안정화 (5~24개월)
    forvalues m = 5/24 {
        // 기회주의적 잔존
        scalar opp_remain = max(0, I_TOTAL * ALPHA_OPP * (1 - 0.05 * (`m' - 4)))
        // 행정 정리 잔존
        scalar adm_remain = I_TOTAL * ALPHA_ADMIN * 0.95
        // 실제 이전 잔존
        scalar act_remain = I_TOTAL * ALPHA_ACTUAL * max(0.6, 1 - 0.015 * (`m' - 4))
        // 귀농귀촌 잔존
        scalar ret_remain = I_TOTAL * ALPHA_RETURN * max(0.5, 1 - 0.02 * (`m' - 4))
        // 추가 자연 유입
        scalar nat_add = 30 * ln(1 + `m'/6)

        scalar total_net = opp_remain + adm_remain + act_remain + ret_remain + nat_add
        replace pop_bi = pop_cf + total_net if month == `m'
    }

    // Phase 3: 기본소득 종료 후 (25~60개월)
    // 24개월 시점의 순효과 계산
    summarize pop_bi if month == 24, meanonly
    scalar pop_bi_24 = r(mean)
    summarize pop_cf if month == 24, meanonly
    scalar pop_cf_24 = r(mean)
    scalar net_at_end = pop_bi_24 - pop_cf_24

    forvalues m = 25/60 {
        scalar months_after = `m' - 24
        scalar retention = 0.45 + 0.10 * exp(-0.05 * months_after)
        scalar retained = net_at_end * retention
        replace pop_bi = pop_cf + retained if month == `m'
    }

    // ── 목포 인구 동태 ──
    gen double pop_mokpo = MOKPO_POP_BASE * (1 + r_monthly_mokpo)^month
    gen double noise_mokpo = rnormal(0, 80)
    replace noise_mokpo = 0 if month == 0
    gen double cum_noise_mokpo = sum(noise_mokpo)
    replace pop_mokpo = pop_mokpo + cum_noise_mokpo

    // 목포 - 신안 효과 포함
    gen double pop_mokpo_effect = pop_mokpo
    forvalues m = 1/4 {
        scalar sinan_eff = -I_TOTAL * 0.35 * (1 - exp(-1.2 * `m')) / (1 - exp(-1.2 * 4))
        replace pop_mokpo_effect = pop_mokpo + sinan_eff if month == `m'
    }
    forvalues m = 5/60 {
        scalar mokpo_adj = -I_TOTAL * 0.35 * max(0.3, exp(-0.02 * (`m' - 4)))
        replace pop_mokpo_effect = pop_mokpo + mokpo_adj if month == `m'
    }

    // 기본소득 순효과
    gen double bi_net_effect = pop_bi - pop_cf

    // 라벨
    label variable month            "개월 (0=시작)"
    label variable pop_cf           "반사실적 인구 (기본소득 없음)"
    label variable pop_bi           "기본소득 시행 인구"
    label variable bi_net_effect    "기본소득 순효과 (명)"
    label variable pop_mokpo        "목포 독립 추세"
    label variable pop_mokpo_effect "목포 (신안효과 포함)"

    drop noise_cf cum_noise_cf noise_mokpo cum_noise_mokpo
}

// 핵심 시점 출력
display _n "  [시뮬레이션 결과]"
list month pop_cf pop_bi bi_net_effect if inlist(month, 0, 4, 12, 24, 36, 60), ///
    noobs separator(0) abbreviate(20)

save sinan_q1_population.dta, replace
display "  → sinan_q1_population.dta 저장 완료"


/*==============================================================================
  제로섬 분해 분석
==============================================================================*/

display _n "── 제로섬 가설 검증 ──"

preserve
clear
quietly set obs 1

// 목포 자연 감소 (4개월분)
gen double mokpo_natural_4m = MOKPO_POP_BASE * ((1 - 0.015)^(4/12) - 1)
// 신안 효과 (목포 출신 이동)
gen double sinan_effect = I_TOTAL * 0.35
// 기타 요인
gen double other_factors = MOKPO_POP_CHANGE - mokpo_natural_4m - (-sinan_effect)
// 신안 귀속 비율
gen double sinan_share = sinan_effect / abs(MOKPO_POP_CHANGE)

gen double mokpo_total = MOKPO_POP_CHANGE

label variable mokpo_total      "목포 총 감소"
label variable mokpo_natural_4m "자연감소 (4개월)"
label variable sinan_effect     "신안 이동 효과"
label variable other_factors    "기타 요인"
label variable sinan_share      "신안 귀속 비율"

list, noobs abbreviate(20)
display "  → 목포 감소의 약 " %4.1f (sinan_share[1]*100) "%만 신안 효과"

save sinan_zerosum.dta, replace
display "  → sinan_zerosum.dta 저장 완료"
restore


/*==============================================================================
  Q2. 실험 기간별 인구 정착률
==============================================================================*/

display _n "── Q2. 정착률 시뮬레이션 ──"

preserve
clear
quietly {
    set obs 5
    gen int duration_months = .
    replace duration_months = 12 in 1
    replace duration_months = 24 in 2
    replace duration_months = 36 in 3
    replace duration_months = 48 in 4
    replace duration_months = 60 in 5

    gen double duration_years = duration_months / 12

    // 유형별 정착률
    gen double ret_admin = min(0.95, 0.85 + 0.003 * duration_months)
    gen double ret_actual = min(0.80, 0.40 + 0.008 * duration_months)
    gen double ret_return = min(0.70, 0.30 + 0.008 * duration_months)
    gen double ret_opp = max(0.05, 0.20 - 0.004 * duration_months)

    // 가중평균 정착률
    gen double ret_overall = ALPHA_ADMIN * ret_admin + ALPHA_ACTUAL * ret_actual ///
                           + ALPHA_RETURN * ret_return + ALPHA_OPP * ret_opp

    // 영구 인구 증가 추정
    gen int perm_pop_gain = round(I_TOTAL * ret_overall)

    label variable duration_months "실험기간 (월)"
    label variable duration_years  "실험기간 (년)"
    label variable ret_admin       "행정정리 정착률"
    label variable ret_actual      "실이전 정착률"
    label variable ret_return      "귀농귀촌 정착률"
    label variable ret_opp         "기회주의 정착률"
    label variable ret_overall     "종합 정착률"
    label variable perm_pop_gain   "영구 인구 증가 (명)"
}

list duration_years ret_overall perm_pop_gain, noobs separator(0)

save sinan_q2_retention.dta, replace
display "  → sinan_q2_retention.dta 저장 완료"
restore


/*==============================================================================
  Q3. 월 지급액별 행동 변화 임계점
==============================================================================*/

display _n "── Q3. 임계점 분석 ──"

preserve
clear
quietly {
    set obs 6
    gen double monthly_amount = .
    replace monthly_amount = 50000  in 1
    replace monthly_amount = 100000 in 2
    replace monthly_amount = 150000 in 3
    replace monthly_amount = 200000 in 4
    replace monthly_amount = 300000 in 5
    replace monthly_amount = 500000 in 6

    gen double amount_만원 = monthly_amount / 10000
    gen double household_2p = monthly_amount * 2

    // 소득 보충 비율 (농어촌 평균 가구소득 250만원)
    scalar rural_income = 2500000
    gen double income_ratio = household_2p / rural_income

    // 행동변화 확률 (로지스틱 모델)
    gen double prob_behavior = 1 / (1 + exp(-15 * (income_ratio - 0.12)))

    // 주소이전 확률
    gen double prob_register = min(0.95, 1 / (1 + exp(-25 * (income_ratio - 0.04))))

    // 실제이주 확률
    gen double prob_move = 1 / (1 + exp(-12 * (income_ratio - 0.18)))

    // 지역소비 증가율
    gen double spending_inc = min(0.30, income_ratio * 0.8)

    label variable amount_만원    "월 지급액 (만원)"
    label variable income_ratio   "소득보충비율"
    label variable prob_behavior  "행동변화 확률"
    label variable prob_register  "주소이전 확률"
    label variable prob_move      "실제이주 확률"
    label variable spending_inc   "지역소비 증가율"
}

list amount_만원 income_ratio prob_register prob_move prob_behavior, ///
    noobs separator(0) abbreviate(16)

save sinan_q3_threshold.dta, replace
display "  → sinan_q3_threshold.dta 저장 완료"
restore


/*==============================================================================
  Q3-2. 지역경제 승수효과
==============================================================================*/

display _n "── Q3-2. 승수효과 분석 ──"

preserve
clear
quietly {
    scalar monthly_inject = SINAN_POP_AFTER_4M * MONTHLY_PAYMENT
    scalar annual_inject = monthly_inject * 12

    set obs 10
    gen int round = _n
    gen double spending = .

    // 라운드별 지출 계산
    replace spending = monthly_inject * 1.0 if round == 1
    replace spending = spending[_n-1] * (1 - 0.40) * 0.70 if round == 2
    forvalues r = 3/10 {
        replace spending = spending[_n-1] * (1 - 0.55) * 0.70 if round == `r'
    }

    gen double cumulative = sum(spending)
    gen double share_pct = spending / monthly_inject * 100

    label variable round       "라운드"
    label variable spending    "라운드별 지출 (원)"
    label variable cumulative  "누적 지출 (원)"
    label variable share_pct   "투입액 대비 (%)"
}

summarize cumulative if round == 10, meanonly
scalar total_effect = r(mean)
scalar multiplier = total_effect / monthly_inject

display "  월 투입액:     " %15.0fc monthly_inject " 원"
display "  연 투입액:     " %15.0fc annual_inject " 원"
display "  승수:          " %6.3f multiplier
display "  월 총경제효과: " %15.0fc total_effect " 원"

list round spending cumulative share_pct, noobs separator(0)

save sinan_q3_multiplier.dta, replace
display "  → sinan_q3_multiplier.dta 저장 완료"
restore


/*==============================================================================
  Q4. 지역상품권 소비 제약 분석
==============================================================================*/

display _n "── Q4. 소비 제약 분석 ──"

preserve
clear
quietly {
    set obs 8

    gen str20 category = ""
    gen double need_share = .
    gen double usable = .
    gen str10 adequacy = ""

    replace category = "식료품·생필품"     in 1
    replace need_share = 0.35              in 1
    replace usable = 0.95                  in 1
    replace adequacy = "high"              in 1

    replace category = "의료·약국"         in 2
    replace need_share = 0.15              in 2
    replace usable = 0.30                  in 2
    replace adequacy = "low"               in 2

    replace category = "교통·연료"         in 3
    replace need_share = 0.12              in 3
    replace usable = 0.60                  in 3
    replace adequacy = "medium"            in 3

    replace category = "교육·학원"         in 4
    replace need_share = 0.08              in 4
    replace usable = 0.10                  in 4
    replace adequacy = "very_low"          in 4

    replace category = "의류·생활용품"     in 5
    replace need_share = 0.10              in 5
    replace usable = 0.70                  in 5
    replace adequacy = "medium"            in 5

    replace category = "외식·카페"         in 6
    replace need_share = 0.08              in 6
    replace usable = 0.85                  in 6
    replace adequacy = "high"              in 6

    replace category = "통신·공과금"       in 7
    replace need_share = 0.07              in 7
    replace usable = 0.20                  in 7
    replace adequacy = "low"               in 7

    replace category = "기타 서비스"       in 8
    replace need_share = 0.05              in 8
    replace usable = 0.40                  in 8
    replace adequacy = "low"               in 8

    // 가중 사용가능률
    gen double weighted = need_share * usable

    label variable category    "지출 범주"
    label variable need_share  "필요 비중"
    label variable usable      "상품권 사용가능률"
    label variable adequacy    "적절성"
    label variable weighted    "가중 사용가능률"
}

// 종합 소비 자유도
summarize weighted, meanonly
scalar freedom_index = r(sum)
scalar effective_amt = MONTHLY_PAYMENT * freedom_index
scalar constrained_amt = MONTHLY_PAYMENT - effective_amt

display "  종합 소비 자유도: " %5.1f (freedom_index * 100) "%"
display "  실효 사용 금액:   " %9.0fc effective_amt " 원"
display "  제약 금액:        " %9.0fc constrained_amt " 원"

list category need_share usable weighted, noobs separator(0)

save sinan_q4_voucher.dta, replace
display "  → sinan_q4_voucher.dta 저장 완료"
restore


/*==============================================================================
  Q5. 인프라 부하 분석
==============================================================================*/

display _n "── Q5. 인프라 부하 분석 ──"

preserve
clear
quietly {
    set obs 5

    gen str20 facility = ""
    gen double current_load = .
    gen byte expansion = .

    replace facility = "의료기관"         in 1
    replace current_load = 0.75           in 1
    replace expansion = 1                 in 1

    replace facility = "초중고교"         in 2
    replace current_load = 0.45           in 2
    replace expansion = 0                 in 2

    replace facility = "대중교통(여객선)" in 3
    replace current_load = 0.80           in 3
    replace expansion = 1                 in 3

    replace facility = "주거"             in 4
    replace current_load = 0.60           in 4
    replace expansion = 1                 in 4

    replace facility = "상하수도"         in 5
    replace current_load = 0.65           in 5
    replace expansion = 0                 in 5

    // 인구 증가 후 부하율
    scalar pop_ratio = SINAN_POP_AFTER_4M / SINAN_POP_BASE
    gen double projected_load = current_load * pop_ratio
    gen double overload = max(0, projected_load - 1.0)

    gen str10 stress = "ok"
    replace stress = "critical" if projected_load > 0.95
    replace stress = "warning"  if projected_load > 0.85 & projected_load <= 0.95

    label variable facility       "시설 유형"
    label variable current_load   "현재 부하율"
    label variable projected_load "예상 부하율"
    label variable overload       "초과 부하율"
    label variable stress         "스트레스 수준"
    label variable expansion      "확충 필요 (1=예)"
}

list facility current_load projected_load stress expansion, noobs separator(0)

save sinan_q5_infra.dta, replace
display "  → sinan_q5_infra.dta 저장 완료"
restore


/*==============================================================================
  완료 메시지
==============================================================================*/

display _n "╔══════════════════════════════════════════════════════════════╗"
display    "║  시뮬레이션 완료                                            ║"
display    "║  저장된 파일:                                               ║"
display    "║    sinan_q1_population.dta   (Q1 인구동태 60개월)            ║"
display    "║    sinan_zerosum.dta         (제로섬 분해)                   ║"
display    "║    sinan_q2_retention.dta    (Q2 정착률)                     ║"
display    "║    sinan_q3_threshold.dta    (Q3 임계점)                     ║"
display    "║    sinan_q3_multiplier.dta   (Q3-2 승수효과)                 ║"
display    "║    sinan_q4_voucher.dta      (Q4 소비제약)                   ║"
display    "║    sinan_q5_infra.dta        (Q5 인프라부하)                  ║"
display    "╚══════════════════════════════════════════════════════════════╝"
