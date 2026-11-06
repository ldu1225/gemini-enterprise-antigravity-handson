"""Write instructor answer keys (NOT bundled for learners):

- answer_keys/inquiries_answer_key.json  — 60 inquiries: category, urgent, needs_info
- answer_keys/policies_qa.md             — 12 test questions for the Lab 7 support-desk agent
- DATA_NOTES.md                          — facts/story of every file, generated from the same constants
"""
from __future__ import annotations

import json
from collections import Counter

import build_it_pdf as IT
import build_leave_pdf as LV
import build_marketing_pdfs as MK
import build_travel_pdf as TR
import calendar_kr as C
import data_inquiries as Q
import data_sales as S
from common import DISCLAIMER, FILES, HERE, KEYS

usd, won = TR.usd, TR.won


def write_inquiries_key() -> dict:
    key = Q.answer_key()
    cnt = Counter(k["category"] for k in key)
    doc = {
        "file": FILES["cs"],
        "note": "강사용 정답 — 학습자 배포 금지. urgent=안전 이슈(발열·연기·불꽃·타는 냄새·배터리 팽창)만 true. "
                "needs_info=배송지연·환불/교환인데 주문번호가 비어 있어 주문번호를 요청해야 하는 건.",
        "categories": Q.CATEGORIES,
        "counts": {c: cnt[c] for c in Q.CATEGORIES},
        "urgent_ids": [k["문의번호"] for k in key if k["urgent"]],
        "needs_info_ids": [k["문의번호"] for k in key if k["needs_info"]],
        "trap_ids": [k["문의번호"] for k in key if "급합니다" in k["요약"] or "급해요" in k["요약"]],
        "items": key,
    }
    KEYS.mkdir(parents=True, exist_ok=True)
    (KEYS / "inquiries_answer_key.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def qa_items() -> list[dict]:
    a, b = C.EX_RETURN_A, C.EX_RETURN_B
    days_a = ", ".join(C.short(d) for d in C.business_days_between(a, C.EX_DEADLINE_A))
    days_b = ", ".join(C.short(d) for d in C.business_days_between(b, C.EX_DEADLINE_B))
    stop15 = C.nth_business_day_after(a, 15)
    return [
        {"q": f"{a.month}월 {a.day}일({C.wd(a)})에 미국 출장에서 귀국했어요. 출장비 정산 마감일이 언제예요?",
         "a": f"**{C.fmt(C.EX_DEADLINE_A)}**. 귀국 다음 날부터 주말·공휴일을 제외한 7영업일 — 10/24(토)·10/25(일) 제외, "
              f"1~7영업일 = {days_a}. 2026년 11월에는 공휴일이 없음.",
         "ref": "출장비 규정 제19조 ①, 제3조(영업일 정의), 부록 A·B", "type": "날짜 계산"},
        {"q": f"{b.month}월 {b.day}일({C.wd(b)})에 귀국했다면 정산 마감일은?",
         "a": f"**{C.fmt(C.EX_DEADLINE_B)}**. 9/24~26 추석 연휴, 9/27 일요일, 10/3(토)·10/4(일), 10/5(월) 개천절 대체공휴일 제외 — "
              f"1~7영업일 = {days_b}.",
         "ref": "출장비 규정 제19조, 부록 A(공휴일표)·부록 B", "type": "날짜 계산(공휴일)"},
        {"q": f"{a.month}월 {a.day}일 귀국 후 정산을 계속 안 하면 법인카드는 언제부터 정지되나요?",
         "a": f"**{C.fmt(C.EX_CARD_STOP_A)}부터**. 15영업일 '초과' 시 정지 → 15영업일째 {C.short(stop15)}까지 미정산이면 다음 영업일부터. "
              "(7영업일 초과: 매일 알림+지연 사유서, 30영업일 초과: 다음 달 급여 공제)",
         "ref": "출장비 규정 제23조 표·①", "type": "날짜 계산 + 규정"},
        {"q": "팀장인데 뉴욕으로 3박 5일 출장을 가요. 숙박비 한도와 일비 총액은?",
         "a": f"숙박비 1박 **{usd(TR.OS_HOTEL['미주·유럽']['팀장'])}** 한도(세금·봉사료 포함, ×3박), 일비 {usd(95)} × 5일 = **{usd(475)}** "
              "(출발일·귀국일 포함). 항공은 편도 8시간 이상이므로 팀장 비즈니스석.",
         "ref": "출장비 규정 제10조 표, 제11조 ①, 제8조", "type": "표 조회 + 계산"},
        {"q": "팀원이 두바이로 2박 3일 출장 가면 일비는?",
         "a": f"중동은 아시아·미주유럽 어디에도 속하지 않으므로 **미주·유럽 기준** → {usd(80)} × 3일 = **{usd(240)}**, 숙박 1박 {usd(220)} 한도.",
         "ref": "출장비 규정 제10조 ③, 제11조 ①", "type": "예외 규칙"},
        {"q": "고객 4명과 우리 직원 2명(임원 없음)이 저녁을 먹었고 총 75만원이 나왔어요. 문제 없나요?",
         "a": f"한도 {won(TR.ENT_PER_PERSON)} × 6명 = 600,000원 → **150,000원 초과분은 본인 부담**(사전 예외 승인 시 인정). "
              f"또한 총액이 {won(TR.ENT_PRE_APPROVAL)}을 넘으므로 **담당 임원 사전 승인 대상**. 주류는 총액의 30% 이내, 참석자 명단 기재.",
         "ref": "출장비 규정 제18조 표, 제6장 계산 예", "type": "계산 + 다중 조건"},
        {"q": "올해 연차가 7일 남았는데 내년으로 넘길 수 있나요?",
         "a": f"**최대 {LV.CARRY_MAX}일**까지 **다음 해 6월 30일까지** 이월 가능. 12월 15일까지 '연차 이월 신청' + 팀장 승인. 나머지 2일은 사용 촉진 절차에 따라 소멸.",
         "ref": "휴가 규정 제7조 ①~③, 제6조", "type": "규정 조회"},
        {"q": "배우자가 출산하면 휴가를 며칠 쓸 수 있고, 나눠 쓸 수 있나요?",
         "a": "**20일**(영업일 기준, 유급), 출산일로부터 **120일 이내**, **최대 3회 분할** 가능. 경조금 50만원(가상).",
         "ref": "휴가 규정 제9조 표·②", "type": "표 조회"},
        {"q": "재택근무는 일주일에 며칠까지 되고, 언제까지 신청해야 하나요? 코어타임은?",
         "a": f"**주 {LV.REMOTE_MAX_PER_WEEK}일 이내**, **{LV.REMOTE_DEADLINE}까지** 다음 주 근무 계획 등록 + 팀장 승인. "
              f"코어타임 **{LV.CORE_START}~{LV.CORE_END}**(점심 12~13시 제외). 화요일은 원칙적으로 출근.",
         "ref": "휴가 규정 제14조, 제15조, 제17조 ②", "type": "다중 조항"},
        {"q": "비밀번호를 여러 번 틀려서 계정이 잠겼어요. 어떻게 하나요?",
         "a": f"{IT.LOCK_FAILS}회 연속 실패 시 {IT.LOCK_MINUTES}분 잠금 → ① {IT.LOCK_MINUTES}분 후 자동 해제, ② 급하면 계정 셀프서비스 포털(로그인 화면 "
              f"'계정 잠금 해제')에서 2단계 인증 후 즉시 해제·재설정, ③ 안 되면 IT 헬프데스크({IT.HELPDESK_PHONE}) — 사번+등록 휴대폰+팀장 확인.",
         "ref": "IT 가이드 제7조, 제8조 ①~④", "type": "절차 안내"},
        {"q": "오늘 아침 9시부터 재택 중에 VPN이 안 돼요. 재부팅도 해 봤어요. 헬프데스크 티켓 좀 써 주세요.",
         "a": "6개 항목을 모두 채운 초안: **제목** [네트워크] 재택 중 VPN 연결 실패 / **유형** 네트워크 / **긴급도** 높음(업무 완전 중단·대체 수단 없음, "
              "목표 응답 4시간) / **증상** VPN 접속 불가(오류 메시지 원문 확인 요청) / **발생 시각** 2026-10-26 09:00부터 / **시도한 조치** 노트북 재부팅. "
              "정보가 부족한 항목(오류 메시지 원문)은 사용자에게 되묻는 것이 좋음.",
         "ref": "IT 가이드 제20조 표, 제21조 표, 부록 B", "type": "작성 지원"},
        {"q": "Cymbal 주식 지금 사도 될까요? / 경쟁사 A 제품이랑 비교해서 어디가 더 좋아요?",
         "a": "**답변 거절(범위 밖)**. 투자 조언·외부 제품 비교는 사내 규정(출장비·휴가·IT) 지원 범위가 아니라고 정중히 안내하고, "
              "답할 수 있는 주제(출장·경비, 휴가·근무, IT 보안·계정)를 제시. 문서에 없는 내용을 지어내면 실패.",
         "ref": "(문서 범위 밖 — 에이전트 지침에 '범위 밖 거절' 규칙 필요)", "type": "범위 밖 거절"},
    ]


def write_policies_qa() -> list[dict]:
    items = qa_items()
    assert len(items) == 12
    lines = [
        "# Lab 7 사내 지원 데스크 에이전트 — 테스트 질문 12개 (강사용 정답)",
        "",
        f"> ※ {DISCLAIMER}. 학습자 배포 금지. `write_answer_keys.py`가 PDF와 같은 상수에서 자동 생성합니다.",
        "",
        "지식 소스: "
        f"`{FILES['travel']}` · `{FILES['leave']}` · `{FILES['it']}` (모두 시행일 2026-07-01).",
        "",
        "채점 기준: ① 정확한 값 ② 조항 근거 제시 ③ 계산 과정(날짜 문항) ④ 범위 밖 질문 거절. 기준일은 2026-10-26(월).",
        "",
        "| # | 유형 | 질문 | 정답 | 근거 조항 |",
        "|---|---|---|---|---|",
    ]
    for i, it in enumerate(items, start=1):
        lines.append(f"| {i} | {it['type']} | {it['q']} | {it['a']} | {it['ref']} |")
    hol = ", ".join(f"{d.month}/{d.day}({C.wd(d)}) {n}" for d, n in C.h2_table())
    lines += [
        "",
        "## 참고: 2026년 8~12월 공휴일 (PDF 부록 A와 동일)",
        "",
        hol,
        "",
        "2026년 11월에는 공휴일이 없습니다. 요일은 Python `datetime`으로 검증했습니다(`calendar_kr.py`의 assert).",
        "",
        "## 자주 틀리는 포인트",
        "",
        "- 정산 기한을 '귀국일 포함'으로 세거나 주말을 포함하면 오답 (10/23 귀국 → 10/30이나 11/2는 오답).",
        "- 9/22 귀국 건에서 10/5 대체공휴일을 빠뜨리면 10/5를 마감일로 답함 → 오답(정답 10/6).",
        "- '15영업일 초과'를 15영업일째로 착각하면 11/13 → 오답(정답 11/16부터 정지).",
        "- 두바이를 아시아로 분류하면 일비 USD 180 → 오답(정답 USD 240).",
        "- 접대비 75만원 문항에서 사전 승인(50만원 초과) 조건을 빠뜨리면 부분 정답.",
    ]
    (KEYS / "policies_qa.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return items


def write_data_notes(inq: dict) -> None:
    F = S.facts()
    q = ("1분기", "2분기", "3분기")
    prod_rows = "\n".join(
        f"| {p} | " + " | ".join(f"{F['prod_q'][p][x]:,.1f}" for x in q) + " | "
        + " | ".join(f"{F['achv_q'][p][x]}" for x in q) + f" | {F['gm_pct_ytd'][p]} |" for p in S.PRODUCTS)
    online = " → ".join(f"{m[-2:]}월 {v}%" for m, v in F["online_share"].items())
    region = ", ".join(f"{g} {v:,.1f}" for g, v in F["region_ytd"].items())
    txt = f"""# DATA_NOTES — v2 실습 파일 팩트 시트 (자동 생성)

> ※ {DISCLAIMER}. `python3 write_answer_keys.py`가 생성기와 같은 상수에서 만듭니다. 손으로 고치지 마세요.

## 1. {FILES['sales']} (Lab 3)
- 시트: `매출데이터`(225행 = 9개월 × 5제품 × 5지역), `목표`(45행 = 9개월 × 5제품). 1행 제목+면책, 2행 헤더, 정적 값.
- 컬럼: {", ".join(S.SALES_COLS)} / 목표: {", ".join(S.TARGET_COLS)}
- 1~9월 총매출 **{F['total_rev']:,.1f}백만원** (분기: {", ".join(f"{k} {v:,.1f}" for k, v in F['q_total'].items())})
- 온라인 매출 비중: {online}
- 9월 매출 순위: {" > ".join(F['sep_rank'])}
- 로봇청소기 9월 매출 = 1월의 **{F['robot_growth_x']}배**; 홈카메라 3분기 매출 전분기 대비 **{F['camera_q3_vs_q2_pct']}%**
- 지역별 1~9월 매출(백만원): {region}

| 제품 | 1분기 매출 | 2분기 | 3분기 | 1Q 달성률% | 2Q | 3Q | 1~9월 매출총이익률% |
|---|---:|---:|---:|---:|---:|---:|---:|
{prod_rows}

스토리(분석 시 나와야 할 인사이트): 로봇청소기 급성장·목표 초과(3Q {F['achv_q']['로봇청소기']['3분기']}%), 홈카메라 3분기 급락(달성률 {F['achv_q']['홈카메라']['3분기']}%),
온라인 비중 확대(22% → 약 39%), 공기청정기 3~4월 성수기, 스마트 스피커 5월 가격 인하 후 마진 하락(약 28% → 22%), 스마트 조명 마진 최고(약 45%).

## 2. {FILES['cs']} (Lab 8)
- 60건, 컬럼: {", ".join(Q.COLUMNS)} — **분류·긴급도 정답 컬럼 없음**(정답: `answer_keys/inquiries_answer_key.json`)
- 분류별 건수: {", ".join(f"{k} {v}" for k, v in inq['counts'].items())}
- 긴급(안전 이슈) {len(inq['urgent_ids'])}건: {", ".join(inq['urgent_ids'])}
- 정보 요청 필요(주문번호 없음) {len(inq['needs_info_ids'])}건: {", ".join(inq['needs_info_ids'])}
- 함정: "급합니다!!" 표현이 있지만 안전 이슈가 아닌 배송 문의 → {", ".join(inq['trap_ids'])} (긴급 아님)

## 3. 규정 PDF 3종 (Lab 7) — 시행일 2026-07-01
- {FILES['travel']} ({TR.DOC_NO}): 일비/숙박 국내(원)·해외 아시아/미주·유럽(USD), 직급 임원/팀장/팀원, 정산 = 귀국 다음 날부터 7영업일,
  지연 7/15/30영업일 초과 단계 조치, 3만원 초과 적격증빙, 접대비 1인 10만원(임원 동석 15만원)·50만원 초과 사전 승인, 부록에 2026년 8~12월 공휴일표.
- {FILES['leave']} ({LV.DOC_NO}): 연차 15일(+2년마다 1일, 최대 25일), 이월 최대 {LV.CARRY_MAX}일·다음 해 6/30까지, 반차 0.5/반반차 0.25(2시간),
  경조사 표(배우자 출산 20일·120일 이내·3회 분할), 재택 주 {LV.REMOTE_MAX_PER_WEEK}일·{LV.REMOTE_DEADLINE} 신청, 코어타임 {LV.CORE_START}~{LV.CORE_END}.
- {FILES['it']} ({IT.DOC_NO}): 비밀번호 {IT.PW_MIN}자·{IT.PW_CLASSES}종·최근 {IT.PW_HISTORY}개 재사용 금지·{IT.PW_ROTATE_DAYS}일 변경, {IT.LOCK_FAILS}회 실패 {IT.LOCK_MINUTES}분 잠금,
  보안 사고 {IT.REPORT_WITHIN_MIN}분 이내 전화 신고({IT.SOC_PHONE}), 티켓 6항목(제목/유형/긴급도/증상/발생 시각/시도한 조치), 긴급도 4단계 응답 목표.
- 테스트 질문 12개와 정답: `answer_keys/policies_qa.md`

## 4. {FILES['brief']} (Lab 4)
- {MK.PRODUCT}({MK.PRODUCT_KO}, {MK.MODEL}) — 출시 {MK.LAUNCH}, 사전 예약 {MK.PREORDER}, 가격 {MK.PRICE:,}원(사전 예약 {MK.PREORDER_PRICE:,}원)
- 핵심 카피 “{MK.COPY_MAIN}”, 타깃 30~40대 맞벌이·영유아 가정(2차: 반려동물·1~2인 가구), 지름 22cm × 높이 110cm 기둥형, 21dB 수면 모드, 무드 라이트 링
- 톤앤매너: 차분·따뜻한 미니멀, 자연광 / 금지: 공포 조장, 의학적 효능, 아이가 제품을 만지는 장면, 경쟁사 비교. 15초 티저 4컷 스토리보드 포함.

## 5. {FILES['brand']} (Lab 4·6·8)
- 컬러: {", ".join(f"{n} {h}" for n, h, _r, _s in MK.BRAND_COLORS)} (60:30:10)
- 톤 오브 보이스: 쉬운 말·핵심 먼저·근거 있는 숫자·존중하는 존댓말 / 금지 표현 {len(MK.BANNED)}종 / 고객 응대 3단계(공감→해결→다음 단계), 안전 이슈 답변 원칙

## 6. 스킬 {FILES['skill_zip']} (Lab 6)
- `cymbal-report-style/SKILL.md` 1개. 형식: 제목 → 결론 → 3줄 요약 → 근거 표 → 원인·시사점 → 다음 단계(담당/할 일/기한) → 작성 기준. 금지 표현은 브랜드 가이드와 동일.
"""
    (HERE / "DATA_NOTES.md").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    inq = write_inquiries_key()
    write_policies_qa()
    write_data_notes(inq)
    print("answer keys + DATA_NOTES written:", inq["counts"], "urgent", len(inq["urgent_ids"]), "needs_info", len(inq["needs_info_ids"]))
