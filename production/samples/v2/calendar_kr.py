"""2026 Korean public holidays + business-day arithmetic (used by the policy PDF and answer keys).

Source: 「관공서의 공휴일에 관한 규정」 기준 2026년 공휴일(대체공휴일 포함). 5월 1일(노동절)은
회사 휴무일로 취급. 7월(제헌절 공휴일 재지정 여부)은 계산 예시에서 의도적으로 피함.
"""
from __future__ import annotations

import datetime as dt

D = dt.date
HOLIDAYS_2026: dict[dt.date, str] = {
    D(2026, 1, 1): "신정",
    D(2026, 2, 16): "설날 연휴", D(2026, 2, 17): "설날", D(2026, 2, 18): "설날 연휴",
    D(2026, 3, 1): "삼일절", D(2026, 3, 2): "대체공휴일(삼일절)",
    D(2026, 5, 1): "노동절(회사 휴무)",
    D(2026, 5, 5): "어린이날",
    D(2026, 5, 24): "부처님오신날", D(2026, 5, 25): "대체공휴일(부처님오신날)",
    D(2026, 6, 3): "전국동시지방선거일",
    D(2026, 6, 6): "현충일",
    D(2026, 8, 15): "광복절", D(2026, 8, 17): "대체공휴일(광복절)",
    D(2026, 9, 24): "추석 연휴", D(2026, 9, 25): "추석", D(2026, 9, 26): "추석 연휴",
    D(2026, 10, 3): "개천절", D(2026, 10, 5): "대체공휴일(개천절)",
    D(2026, 10, 9): "한글날",
    D(2026, 12, 25): "성탄절",
}
WD = "월화수목금토일"


def wd(d: dt.date) -> str:
    return WD[d.weekday()]


def fmt(d: dt.date) -> str:
    return f"{d.year}년 {d.month}월 {d.day}일({wd(d)})"


def short(d: dt.date) -> str:
    return f"{d.month}월 {d.day}일({wd(d)})"


def is_business(d: dt.date) -> bool:
    return d.weekday() < 5 and d not in HOLIDAYS_2026


def nth_business_day_after(start: dt.date, n: int) -> dt.date:
    """n-th business day counting from the day AFTER `start` (start itself excluded)."""
    d, k = start, 0
    while k < n:
        d += dt.timedelta(days=1)
        if is_business(d):
            k += 1
    return d


def business_days_between(start: dt.date, end: dt.date) -> list[dt.date]:
    out, d = [], start
    while d < end:
        d += dt.timedelta(days=1)
        if is_business(d):
            out.append(d)
    return out


def h2_table() -> list[tuple[dt.date, str]]:
    """Holidays Aug–Dec 2026 (printed in the travel policy appendix)."""
    return [(d, n) for d, n in sorted(HOLIDAYS_2026.items()) if d.month >= 8]


# Worked examples used in the PDF and the answer key
SETTLE_DAYS = 7
EX_RETURN_A = D(2026, 10, 23)   # 금
EX_RETURN_B = D(2026, 9, 22)    # 화 — crosses 추석 + 개천절 대체공휴일
EX_DEADLINE_A = nth_business_day_after(EX_RETURN_A, SETTLE_DAYS)
EX_DEADLINE_B = nth_business_day_after(EX_RETURN_B, SETTLE_DAYS)
EX_CARD_STOP_A = nth_business_day_after(EX_RETURN_A, 16)   # 15영업일 '초과' → 16번째 영업일부터
EX_PAYROLL_A = nth_business_day_after(EX_RETURN_A, 31)

# Worked examples PRINTED in the PDF (deliberately different from the answer-key test dates above,
# so the agent must actually calculate the test questions)
DOC_RETURN_A = D(2026, 11, 13)  # 금
DOC_RETURN_B = D(2026, 10, 1)   # 목 — crosses 한글날 + 대체공휴일 없는 주말
DOC_DEADLINE_A = nth_business_day_after(DOC_RETURN_A, SETTLE_DAYS)
DOC_DEADLINE_B = nth_business_day_after(DOC_RETURN_B, SETTLE_DAYS)
DOC_CARD_STOP_A = nth_business_day_after(DOC_RETURN_A, 16)

assert DOC_DEADLINE_A == D(2026, 11, 24) and DOC_DEADLINE_B == D(2026, 10, 14), (DOC_DEADLINE_A, DOC_DEADLINE_B)
assert wd(EX_RETURN_A) == "금" and EX_DEADLINE_A == D(2026, 11, 3), EX_DEADLINE_A
assert EX_DEADLINE_B == D(2026, 10, 6), EX_DEADLINE_B
assert EX_CARD_STOP_A == D(2026, 11, 16), EX_CARD_STOP_A
assert not any(d.month == 11 for d in HOLIDAYS_2026)

if __name__ == "__main__":
    for lbl, d in [("A 마감", EX_DEADLINE_A), ("B 마감", EX_DEADLINE_B), ("A 카드정지", EX_CARD_STOP_A),
                   ("A 급여공제 대상", EX_PAYROLL_A)]:
        print(lbl, fmt(d))
    print([short(x) for x in business_days_between(EX_RETURN_B, EX_DEADLINE_B)])
