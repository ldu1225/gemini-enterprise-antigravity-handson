"""Cymbal 제품별·지역별 월별 매출 2026 (1~9월) — FICTIONAL, deterministic.

Intended story (verified in verify.py / DATA_NOTES.md):
  1) 로봇청소기 급성장: 1월 대비 9월 매출 약 2.5배, 2분기부터 목표 초과, 9월 매출 1위 제품
  2) 홈카메라 3분기 부진: 2분기 대비 3분기 매출 약 −33%, 3분기 목표 달성률 약 59%
  3) 온라인 비중 증가: 전체 매출 중 온라인 비중 1월 약 22% → 9월 약 38%
  4) 공기청정기 3~4월 성수기(미세먼지·황사), 여름 비수기
  5) 스마트 스피커 정체 + 가격 인하로 마진 하락, 스마트 조명은 작지만 마진 최고
"""
from __future__ import annotations

import random

MONTHS = [f"2026-{m:02d}" for m in range(1, 10)]
PRODUCTS = ["스마트 스피커", "로봇청소기", "공기청정기", "스마트 조명", "홈카메라"]
REGIONS = ["수도권", "충청", "호남", "영남", "온라인"]
SEED = 2026

# list price (원) by month index 0..8
ASP = {
    "스마트 스피커": [129000] * 4 + [119000] * 5,           # 5월 가격 인하
    "로봇청소기": [690000] * 3 + [670000] * 3 + [650000] * 3,
    "공기청정기": [389000] * 9,
    "스마트 조명": [39000] * 9,
    "홈카메라": [89000] * 9,
}
# total monthly units (all regions), ×1
UNITS = {
    "스마트 스피커": [27000, 26600, 26400, 25800, 25900, 25300, 24800, 24300, 23800],
    "로봇청소기": [4500, 5100, 5900, 6800, 7700, 8700, 9800, 11000, 12300],
    "공기청정기": [12600, 15800, 20200, 18900, 13900, 10100, 8800, 9400, 12000],
    "스마트 조명": [36000, 36800, 37900, 38900, 40100, 41200, 42600, 44000, 45600],
    "홈카메라": [24000, 24600, 25300, 25900, 26400, 26900, 20100, 17200, 15600],
}
# gross margin % by month (offline); online gets −1.5pp
MARGIN = {
    "스마트 스피커": [28.0, 27.8, 27.5, 27.2, 23.5, 23.0, 22.6, 22.2, 21.8],
    "로봇청소기": [33.0, 33.4, 33.8, 33.5, 33.9, 34.2, 34.0, 34.4, 34.6],
    "공기청정기": [31.0, 31.5, 32.0, 31.8, 31.2, 30.5, 30.0, 30.2, 30.8],
    "스마트 조명": [45.0, 45.2, 45.1, 45.4, 45.6, 45.5, 45.8, 46.0, 46.1],
    "홈카메라": [30.0, 30.2, 30.4, 30.1, 30.3, 30.0, 26.5, 25.0, 24.2],
}
# region weights: offline base, online share grows 22% → 38%
OFFLINE_BASE = {"수도권": 0.49, "충청": 0.13, "호남": 0.11, "영남": 0.27}
ONLINE_SHARE = [0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38]
ONLINE_TILT = {"스마트 스피커": 0.02, "로봇청소기": 0.04, "공기청정기": -0.01, "스마트 조명": 0.03, "홈카메라": -0.02}
ONLINE_PRICE = 0.95  # online ASP = 95% of list

# monthly revenue targets (백만원) — annual plan made in Dec 2025
TARGET_UNITS = {
    "스마트 스피커": [27500, 27300, 27200, 27000, 26800, 26600, 26400, 26200, 26000],
    "로봇청소기": [4600, 5000, 5400, 5800, 6200, 6600, 7000, 7400, 7800],
    "공기청정기": [12500, 15500, 20000, 19000, 14000, 10500, 9000, 9500, 12000],
    "스마트 조명": [35500, 36200, 37000, 37800, 38600, 39400, 40200, 41000, 41800],
    "홈카메라": [24000, 24800, 25600, 26400, 27200, 28000, 28800, 29600, 30400],
}
TARGET_ASP = {"스마트 스피커": 129000, "로봇청소기": 690000, "공기청정기": 389000, "스마트 조명": 39000, "홈카메라": 89000}


def _alloc(total: int, weights: dict[str, float]) -> dict[str, int]:
    raw = {k: total * w for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    rest = total - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:rest]:
        out[k] += 1
    return out


def rows() -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for mi, month in enumerate(MONTHS):
        q = f"{(mi // 3) + 1}분기"
        for prod in PRODUCTS:
            on = ONLINE_SHARE[mi] + ONLINE_TILT[prod]
            weights = {r: OFFLINE_BASE[r] * (1 - on) * (1 + rng.uniform(-0.04, 0.04)) for r in OFFLINE_BASE}
            weights["온라인"] = on
            s = sum(weights.values())
            weights = {k: v / s for k, v in weights.items()}
            units = _alloc(UNITS[prod][mi], weights)
            for reg in REGIONS:
                price = ASP[prod][mi] if reg != "온라인" else int(ASP[prod][mi] * ONLINE_PRICE / 100 + 0.5) * 100
                rev = round(units[reg] * price / 1_000_000, 1)              # 백만원 (= 수량 × 평균판매가)
                gm_pct = MARGIN[prod][mi] - (1.5 if reg == "온라인" else 0.0) + round(rng.uniform(-0.3, 0.3), 1)
                gm_pct = round(gm_pct, 1)
                gp = round(rev * gm_pct / 100, 1)
                out.append({
                    "월": month, "분기": q, "제품": prod, "지역": reg,
                    "판매수량(대)": units[reg],
                    "평균판매가(원)": price,
                    "매출액(백만원)": rev,
                    "매출총이익(백만원)": gp,
                    "매출총이익률(%)": gm_pct,
                })
    return out


def target_rows() -> list[dict]:
    out = []
    for mi, month in enumerate(MONTHS):
        for prod in PRODUCTS:
            u = TARGET_UNITS[prod][mi]
            out.append({"월": month, "분기": f"{(mi // 3) + 1}분기", "제품": prod,
                        "목표수량(대)": u, "목표매출액(백만원)": round(u * TARGET_ASP[prod] / 1_000_000, 1)})
    return out


SALES_COLS = ["월", "분기", "제품", "지역", "판매수량(대)", "평균판매가(원)", "매출액(백만원)", "매출총이익(백만원)", "매출총이익률(%)"]
TARGET_COLS = ["월", "분기", "제품", "목표수량(대)", "목표매출액(백만원)"]


# ---------------------------------------------------------------- facts for notes / verify
def facts() -> dict:
    R = rows()
    T = target_rows()
    f: dict = {}
    def s(pred, key="매출액(백만원)"):
        return round(sum(r[key] for r in R if pred(r)), 1)
    f["total_rev"] = s(lambda r: True)
    f["by_month"] = {m: s(lambda r, m=m: r["월"] == m) for m in MONTHS}
    f["online_share"] = {m: round(100 * s(lambda r, m=m: r["월"] == m and r["지역"] == "온라인") / f["by_month"][m], 1)
                         for m in MONTHS}
    f["prod_q"] = {p: {q: s(lambda r, p=p, q=q: r["제품"] == p and r["분기"] == q) for q in ("1분기", "2분기", "3분기")}
                   for p in PRODUCTS}
    f["prod_month"] = {p: {m: s(lambda r, p=p, m=m: r["제품"] == p and r["월"] == m) for m in MONTHS} for p in PRODUCTS}
    tq = {p: {q: round(sum(t["목표매출액(백만원)"] for t in T if t["제품"] == p and t["분기"] == q), 1)
              for q in ("1분기", "2분기", "3분기")} for p in PRODUCTS}
    f["target_q"] = tq
    f["achv_q"] = {p: {q: round(100 * f["prod_q"][p][q] / tq[p][q], 1) for q in tq[p]} for p in PRODUCTS}
    f["sep_rank"] = sorted(PRODUCTS, key=lambda p: -f["prod_month"][p]["2026-09"])
    f["robot_growth_x"] = round(f["prod_month"]["로봇청소기"]["2026-09"] / f["prod_month"]["로봇청소기"]["2026-01"], 2)
    f["camera_q3_vs_q2_pct"] = round(100 * (f["prod_q"]["홈카메라"]["3분기"] / f["prod_q"]["홈카메라"]["2분기"] - 1), 1)
    gp = {p: s(lambda r, p=p: r["제품"] == p, "매출총이익(백만원)") for p in PRODUCTS}
    f["gm_pct_ytd"] = {p: round(100 * gp[p] / s(lambda r, p=p: r["제품"] == p), 1) for p in PRODUCTS}
    f["region_ytd"] = {g: s(lambda r, g=g: r["지역"] == g) for g in REGIONS}
    f["q_total"] = {q: s(lambda r, q=q: r["분기"] == q) for q in ("1분기", "2분기", "3분기")}
    return f


if __name__ == "__main__":
    import json
    print(len(rows()), "rows")
    print(json.dumps(facts(), ensure_ascii=False, indent=1))
