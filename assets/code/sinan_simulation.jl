#=
╔══════════════════════════════════════════════════════════════════╗
║  신안군 농어촌기본소득 시뮬레이션 (Julia 버전)                      ║
║  ────────────────────────────────────────────────────            ║
║  5가지 건설적 질문에 대한 정량적 분석                                ║
║                                                                  ║
║  원본: simulation.py → Julia 변환                                 ║
║  작성: 2026-03-22                                                 ║
║  요구: Julia 1.9+, DataFrames.jl, CSV.jl, JSON3.jl               ║
╚══════════════════════════════════════════════════════════════════╝

실행:
  julia> include("sinan_simulation.jl")
  julia> results = run_all()

패키지 설치 (최초 1회):
  julia> using Pkg
  julia> Pkg.add(["DataFrames", "CSV", "JSON3", "Printf"])
=#

using DataFrames
using CSV
using JSON3
using Printf
using Random

# ═══════════════════════════════════════════════════════════════
# 기초 파라미터
# ═══════════════════════════════════════════════════════════════

"""신안군 시뮬레이션 파라미터 구조체"""
Base.@kwdef struct SimParams
    # 신안군 기초 데이터
    sinan_pop_base::Int       = 39_500
    sinan_pop_after_4m::Int   = 42_500
    mokpo_pop_base::Int       = 215_000
    mokpo_pop_change::Int     = -3_300

    # 청산면 참조
    cheongsan_pop_base::Int        = 2_800
    cheongsan_initial_spike::Float64 = 0.10
    cheongsan_final_change::Float64  = -0.014

    # 정책 파라미터
    monthly_payment::Int      = 150_000
    experiment_months::Int    = 24
    total_budget_2y::Float64  = 1.2e12

    # 구조적 감소율 (연간)
    rural_annual_decline::Float64 = -0.025
    sinan_annual_decline::Float64 = -0.030

    # 유입 유형 비율
    α_admin::Float64    = 0.35   # 행정정리
    α_actual::Float64   = 0.25   # 실이전
    α_return::Float64   = 0.25   # 귀농귀촌
    α_opp::Float64      = 0.15   # 기회주의
    I_total::Int        = 3_000  # 총 유입
end


# ═══════════════════════════════════════════════════════════════
# Q1. 반사실적 추론 — 인구 동태 시뮬레이션
# ═══════════════════════════════════════════════════════════════

"""
    simulate_population(p::SimParams; months=60, seed=42) → DataFrame

3개 시나리오로 신안군 인구를 시뮬레이션한다:
- 반사실적 (기본소득 없음)
- 기본소득 시행
- 기본소득 순효과
"""
function simulate_population(p::SimParams; months::Int=60, seed::Int=42)
    Random.seed!(seed)

    t = 0:months
    n = length(t)

    # 월간 감소율
    r_sinan = (1 + p.sinan_annual_decline)^(1/12) - 1
    r_mokpo = (1 + (-0.015))^(1/12) - 1

    # ── 시나리오 A: 반사실적 ──
    pop_cf = [p.sinan_pop_base * (1 + r_sinan)^m for m in t]
    noise = cumsum([m == 0 ? 0.0 : randn() * 30 for m in t])
    pop_cf .+= noise

    # ── 시나리오 B: 기본소득 시행 ──
    pop_bi = copy(pop_cf)

    # Phase 1: 초기 급증 (1~4개월)
    for m in 1:min(4, months)
        influx = p.I_total * (1 - exp(-1.2 * m)) / (1 - exp(-1.2 * 4))
        pop_bi[m+1] = pop_cf[m+1] + influx   # +1 for 1-indexed
    end

    # Phase 2: 안정화 (5~24개월)
    for m in 5:min(24, months)
        opp_remain  = max(0, p.I_total * p.α_opp * (1 - 0.05 * (m - 4)))
        adm_remain  = p.I_total * p.α_admin * 0.95
        act_remain  = p.I_total * p.α_actual * max(0.6, 1 - 0.015 * (m - 4))
        ret_remain  = p.I_total * p.α_return * max(0.5, 1 - 0.02 * (m - 4))
        nat_add     = 30 * log(1 + m / 6)

        total_net = opp_remain + adm_remain + act_remain + ret_remain + nat_add
        pop_bi[m+1] = pop_cf[m+1] + total_net
    end

    # Phase 3: 종료 후 (25~60개월)
    if months >= 25
        net_at_end = pop_bi[25] - pop_cf[25]   # 24개월 시점 (index 25)
        for m in 25:months
            months_after = m - 24
            retention = 0.45 + 0.10 * exp(-0.05 * months_after)
            pop_bi[m+1] = pop_cf[m+1] + net_at_end * retention
        end
    end

    # ── 목포 인구 ──
    Random.seed!(seed + 1)
    pop_mokpo = [p.mokpo_pop_base * (1 + r_mokpo)^m for m in t]
    noise_m = cumsum([m == 0 ? 0.0 : randn() * 80 for m in t])
    pop_mokpo .+= noise_m

    pop_mokpo_eff = copy(pop_mokpo)
    for m in 1:min(4, months)
        eff = -p.I_total * 0.35 * (1 - exp(-1.2 * m)) / (1 - exp(-1.2 * 4))
        pop_mokpo_eff[m+1] = pop_mokpo[m+1] + eff
    end
    for m in 5:months
        adj = -p.I_total * 0.35 * max(0.3, exp(-0.02 * (m - 4)))
        pop_mokpo_eff[m+1] = pop_mokpo[m+1] + adj
    end

    DataFrame(
        month             = collect(t),
        pop_counterfactual = pop_cf,
        pop_with_bi        = pop_bi,
        bi_net_effect      = pop_bi .- pop_cf,
        pop_mokpo          = pop_mokpo,
        pop_mokpo_effect   = pop_mokpo_eff,
    )
end


# ═══════════════════════════════════════════════════════════════
# 제로섬 분해
# ═══════════════════════════════════════════════════════════════

"""제로섬 가설 검증: 목포 감소 분해"""
function analyze_zero_sum(p::SimParams)
    mokpo_natural_4m = p.mokpo_pop_base * ((1 - 0.015)^(4/12) - 1)
    sinan_effect     = p.I_total * 0.35
    other            = p.mokpo_pop_change - mokpo_natural_4m - (-sinan_effect)
    sinan_share      = sinan_effect / abs(p.mokpo_pop_change)

    (
        mokpo_total_decline = p.mokpo_pop_change,
        mokpo_natural_4m    = round(Int, mokpo_natural_4m),
        sinan_effect        = round(Int, sinan_effect),
        other_factors       = round(Int, other),
        sinan_share_pct     = sinan_share * 100,
    )
end


# ═══════════════════════════════════════════════════════════════
# Q2. 실험 기간별 정착률
# ═══════════════════════════════════════════════════════════════

"""실험 기간(개월)에 따른 인구 정착률 추정"""
function simulate_retention(p::SimParams)
    durations = [12, 24, 36, 48, 60]

    rows = map(durations) do dur
        ret_admin  = min(0.95, 0.85 + 0.003 * dur)
        ret_actual = min(0.80, 0.40 + 0.008 * dur)
        ret_return = min(0.70, 0.30 + 0.008 * dur)
        ret_opp    = max(0.05, 0.20 - 0.004 * dur)

        overall = (p.α_admin * ret_admin + p.α_actual * ret_actual +
                   p.α_return * ret_return + p.α_opp * ret_opp)

        (
            duration_months = dur,
            duration_years  = dur / 12,
            ret_admin       = ret_admin,
            ret_actual      = ret_actual,
            ret_return      = ret_return,
            ret_opp         = ret_opp,
            ret_overall     = overall,
            perm_pop_gain   = round(Int, p.I_total * overall),
        )
    end

    DataFrame(rows)
end


# ═══════════════════════════════════════════════════════════════
# Q3. 임계점 분석
# ═══════════════════════════════════════════════════════════════

"""월 지급액에 따른 행동 변화 임계점 (로지스틱 모델)"""
function analyze_threshold(; rural_income::Int=2_500_000)
    amounts = [50_000, 100_000, 150_000, 200_000, 300_000, 500_000]

    rows = map(amounts) do amt
        hh2 = amt * 2
        ratio = hh2 / rural_income

        prob_behavior = 1 / (1 + exp(-15 * (ratio - 0.12)))
        prob_register = min(0.95, 1 / (1 + exp(-25 * (ratio - 0.04))))
        prob_move     = 1 / (1 + exp(-12 * (ratio - 0.18)))
        spend_inc     = min(0.30, ratio * 0.8)

        (
            monthly_amount_만원 = amt ÷ 10_000,
            household_2p       = hh2,
            income_ratio       = ratio,
            prob_register      = prob_register,
            prob_behavior      = prob_behavior,
            prob_move          = prob_move,
            spending_increase  = spend_inc,
        )
    end

    DataFrame(rows)
end


# ═══════════════════════════════════════════════════════════════
# Q3-2. 지역경제 승수효과
# ═══════════════════════════════════════════════════════════════

"""케인지안 승수 모델 (10 라운드)"""
function simulate_multiplier(p::SimParams; n_rounds::Int=10)
    monthly_inject = p.sinan_pop_after_4m * p.monthly_payment

    leakage_1st  = 0.40
    leakage_sub  = 0.55
    mpc          = 0.70

    spending = zeros(n_rounds)
    spending[1] = monthly_inject * 1.0

    for r in 2:n_rounds
        leak = r == 2 ? leakage_1st : leakage_sub
        spending[r] = spending[r-1] * (1 - leak) * mpc
    end

    total = sum(spending)
    multiplier = total / monthly_inject

    # GRDP 대비
    annual_inject = monthly_inject * 12
    annual_total  = total * 12
    grdp_est      = 6_000e8
    grdp_ratio    = annual_total / grdp_est

    df = DataFrame(
        round     = 1:n_rounds,
        spending  = spending,
        cumulative = cumsum(spending),
        share_pct  = spending ./ monthly_inject .* 100,
    )

    (
        table            = df,
        monthly_inject   = monthly_inject,
        annual_inject    = annual_inject,
        multiplier       = multiplier,
        annual_total     = annual_total,
        grdp_impact_pct  = grdp_ratio * 100,
    )
end


# ═══════════════════════════════════════════════════════════════
# Q4. 지역상품권 소비 제약 분석
# ═══════════════════════════════════════════════════════════════

"""상품권 소비 자유도 분석 (8개 지출 범주)"""
function analyze_voucher(p::SimParams)
    categories = DataFrame(
        category   = ["식료품·생필품", "의료·약국", "교통·연료", "교육·학원",
                       "의류·생활용품", "외식·카페", "통신·공과금", "기타 서비스"],
        need_share = [0.35, 0.15, 0.12, 0.08, 0.10, 0.08, 0.07, 0.05],
        usable     = [0.95, 0.30, 0.60, 0.10, 0.70, 0.85, 0.20, 0.40],
        adequacy   = ["high", "low", "medium", "very_low",
                       "medium", "high", "low", "low"],
    )

    categories.weighted = categories.need_share .* categories.usable

    freedom = sum(categories.weighted)
    effective = p.monthly_payment * freedom
    constrained = p.monthly_payment - effective

    (
        table          = categories,
        freedom_index  = freedom,
        effective_원   = effective,
        constrained_원 = constrained,
    )
end


# ═══════════════════════════════════════════════════════════════
# Q5. 인프라 부하 분석
# ═══════════════════════════════════════════════════════════════

"""인구 급증 시 공공서비스 인프라 부하율"""
function analyze_infrastructure(p::SimParams)
    pop_ratio = p.sinan_pop_after_4m / p.sinan_pop_base

    facilities = DataFrame(
        facility      = ["의료기관", "초중고교", "대중교통(여객선)", "주거", "상하수도"],
        current_load  = [0.75, 0.45, 0.80, 0.60, 0.65],
        expansion     = [true, false, true, true, false],
    )

    facilities.projected_load = facilities.current_load .* pop_ratio
    facilities.overload       = max.(0, facilities.projected_load .- 1.0)
    facilities.stress = map(facilities.projected_load) do ld
        ld > 0.95 ? "critical" : (ld > 0.85 ? "warning" : "ok")
    end

    facilities
end


# ═══════════════════════════════════════════════════════════════
# 전체 실행
# ═══════════════════════════════════════════════════════════════

"""모든 시뮬레이션을 실행하고 결과를 출력·저장한다."""
function run_all(; save_csv::Bool=true, output_dir::String=".")
    p = SimParams()

    println("╔══════════════════════════════════════════════════════════════╗")
    println("║  신안군 농어촌기본소득 시뮬레이션 (Julia 버전)               ║")
    println("╚══════════════════════════════════════════════════════════════╝")

    # ── Q1: 인구 동태 ──
    println("\n── Q1. 인구 동태 시뮬레이션 (60개월) ──")
    pop = simulate_population(p)
    for m in [0, 4, 12, 24, 36, 60]
        row = pop[pop.month .== m, :]
        @printf("  %2d개월: 반사실 %6.0f | 기본소득 %6.0f | 순효과 %+6.0f\n",
                m, row.pop_counterfactual[1], row.pop_with_bi[1], row.bi_net_effect[1])
    end

    # ── 제로섬 ──
    println("\n── 제로섬 가설 검증 ──")
    zs = analyze_zero_sum(p)
    @printf("  목포 총 감소: %,d명\n", zs.mokpo_total_decline)
    @printf("    ├ 자연 감소:   %,d명\n", zs.mokpo_natural_4m)
    @printf("    ├ 신안 효과:   %,d명\n", zs.sinan_effect)
    @printf("    └ 기타 요인:   %,d명\n", zs.other_factors)
    @printf("  → 신안 귀속 비율: %.1f%%\n", zs.sinan_share_pct)

    # ── Q2: 정착률 ──
    println("\n── Q2. 정착률 시뮬레이션 ──")
    ret = simulate_retention(p)
    for row in eachrow(ret)
        @printf("  %1.0f년: 정착률 %5.1f%% → 영구 인구 +%,d명\n",
                row.duration_years, row.ret_overall * 100, row.perm_pop_gain)
    end

    # ── Q3: 임계점 ──
    println("\n── Q3. 임계점 분석 ──")
    thr = analyze_threshold()
    for row in eachrow(thr)
        @printf("  월 %3d만원: 주소이전 %4.0f%% | 실제이주 %4.0f%% | 행동변화 %4.0f%%\n",
                row.monthly_amount_만원, row.prob_register*100, row.prob_move*100, row.prob_behavior*100)
    end

    # ── Q3-2: 승수 ──
    println("\n── Q3-2. 승수효과 분석 ──")
    mult = simulate_multiplier(p)
    @printf("  월 투입액:     %15s 원\n", format_number(mult.monthly_inject))
    @printf("  승수:          ×%.3f\n", mult.multiplier)
    @printf("  연간 총효과:   %15s 원\n", format_number(mult.annual_total))
    @printf("  GRDP 대비:     %.1f%%\n", mult.grdp_impact_pct)

    # ── Q4: 소비 제약 ──
    println("\n── Q4. 소비 제약 분석 ──")
    vouch = analyze_voucher(p)
    for row in eachrow(vouch.table)
        @printf("  %-15s: 필요 %4.0f%% | 사용가능 %4.0f%%\n",
                row.category, row.need_share*100, row.usable*100)
    end
    @printf("  종합 소비 자유도: %.1f%%\n", vouch.freedom_index * 100)

    # ── Q5: 인프라 ──
    println("\n── Q5. 인프라 부하 분석 ──")
    infra = analyze_infrastructure(p)
    for row in eachrow(infra)
        icon = row.stress == "critical" ? "🔴" : (row.stress == "warning" ? "🟡" : "🟢")
        @printf("  %s %-15s: 현재 %4.0f%% → 예상 %4.0f%%\n",
                icon, row.facility, row.current_load*100, row.projected_load*100)
    end

    # ── CSV 저장 ──
    if save_csv
        CSV.write(joinpath(output_dir, "sinan_q1_population.csv"), pop)
        CSV.write(joinpath(output_dir, "sinan_q2_retention.csv"), ret)
        CSV.write(joinpath(output_dir, "sinan_q3_threshold.csv"), thr)
        CSV.write(joinpath(output_dir, "sinan_q3_multiplier.csv"), mult.table)
        CSV.write(joinpath(output_dir, "sinan_q4_voucher.csv"), vouch.table)
        CSV.write(joinpath(output_dir, "sinan_q5_infra.csv"), infra)
        println("\n  → CSV 파일 6개 저장 완료 ($output_dir)")
    end

    println("\n╔══════════════════════════════════════════════════════════════╗")
    println("║  시뮬레이션 완료                                            ║")
    println("╚══════════════════════════════════════════════════════════════╝")

    # 결과 반환
    (
        params         = p,
        population     = pop,
        zero_sum       = zs,
        retention      = ret,
        threshold      = thr,
        multiplier     = mult,
        voucher        = vouch,
        infrastructure = infra,
    )
end

# 숫자 포맷 헬퍼
function format_number(n::Number)
    s = string(round(Int, n))
    parts = String[]
    while length(s) > 3
        push!(parts, s[end-2:end])
        s = s[1:end-3]
    end
    push!(parts, s)
    join(reverse(parts), ",")
end

# ── 스크립트 직접 실행 시 ──
if abspath(PROGRAM_FILE) == @__FILE__
    run_all()
end
