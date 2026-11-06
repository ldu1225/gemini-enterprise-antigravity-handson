#!/usr/bin/env python3
"""Antigravity track starter project `cymbal-voc` (실습용 가상 데이터).

Builds production/samples/v2/build/cymbal-voc/ and Cymbal_VOC_스타터.zip:
  cymbal-voc/
    README.md                 프로젝트 소개 + 실습 흐름
    요청서_CX팀.md             CX팀장의 요청(스토리의 출발점)
    data/voc_tickets.csv      고객 문의 300건 (2026-09-28 ~ 2026-10-25, 4주)
    setup/load_to_bigquery.sh 내 프로젝트 BigQuery에 같은 데이터 올리기 (맨 위 변수만 바꾸면 됨)

Story signals (must be discoverable in the data — DATA_NOTES §7 lists the exact numbers):
  1. 로봇청소기 '앱 연결' 문의: 10/14 펌웨어 업데이트(v3.2) 이후 급증
  2. 안전 이슈(긴급): 공기청정기 전원 어댑터 과열 — 마지막 주에 몰림, 홈카메라 배터리 부풂
  3. 에어폴 프로(출시 전) 구매 문의가 매주 증가
  4. 채팅·앱 채널 비중 증가
Run:  python3 production/samples/v2/build_voc_starter.py
"""
from __future__ import annotations

import csv
import io
import json
import random
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
PROJ = BUILD / "cymbal-voc"
ZIP = BUILD / "Cymbal_VOC_스타터.zip"
NOTES = HERE / "answer_keys" / "voc_facts.json"
DISC = "실습용 가상 데이터 — Cymbal(심벌)은 가상의 회사이며 실제 기업·인물과 무관"

START = date(2026, 9, 28)                      # Monday
WEEKS = [(START + timedelta(days=7 * i), START + timedelta(days=7 * i + 6)) for i in range(4)]
WEEK_TOTALS = [62, 68, 79, 91]                 # = 300
FIRMWARE_DAY = date(2026, 10, 14)

PRODUCTS = ["로봇청소기", "공기청정기", "스마트 스피커", "스마트 조명", "홈카메라", "에어폴 프로"]
CHANNELS = ["전화", "이메일", "채팅", "앱"]
REGIONS = ["수도권", "충청", "호남", "영남", "강원·제주"]
LAST = list("김이박최정강조윤장임한오서신권황안송류홍")
FIRST = ["민준", "서연", "도윤", "지우", "하준", "서윤", "은우", "지민", "시우", "하은", "유진", "준서", "수아", "지호",
         "예린", "건우", "채원", "현우", "다은", "태윤", "소율", "우진", "가은", "민서"]

# category → (product weights, severity weights, message templates)
MSG = {
    "배송": ["{p_을를} 주문한 지 {n}일이 지났는데 아직 '배송 준비 중'이에요. 언제 받을 수 있나요?",
            "배송 예정일이 지났는데 {p_이가} 도착하지 않았습니다. 송장 조회가 안 돼요.",
            "{p} 세트 중 일부만 먼저 왔어요. 나머지는 언제 오나요?",
            "이사 전에 {p_을를} 꼭 받아야 해서요. 배송 일정을 앞당길 수 있을까요?"],
    "불량·고장": ["{p_이가} 켜진 지 몇 분 만에 저절로 꺼져요. 콘센트는 다른 제품으로 확인했습니다.",
              "{p}에서 덜덜거리는 소음이 점점 심해집니다. 산 지 {n}주 됐어요.",
              "{p} 버튼을 눌러도 반응이 없어요. 초기화도 해 봤습니다.",
              "{p} 센서 수치가 하루 종일 바뀌지 않아요. 고장인 것 같습니다."],
    "앱 연결": ["Cymbal 홈 앱에서 {p_이가} '오프라인'으로만 나와요. Wi-Fi는 정상입니다.",
              "{p_을를} 앱에 다시 등록하려는데 페어링이 계속 실패해요.",
              "앱 업데이트 후 {p} 예약 기능이 사라졌어요.",
              "{p} 연결이 하루에도 여러 번 끊깁니다. 공유기는 2.4GHz로 설정했어요."],
    "사용법": ["{p} 필터는 얼마마다 바꿔야 하나요? 교체 알림을 끄는 방법도 알려 주세요.",
             "{p}의 예약 기능은 어떻게 쓰나요?",
             "{p_을를} 음성으로 제어하려면 어떻게 설정하나요?",
             "{p} 야간 모드를 켜는 방법이 궁금합니다."],
    "환불·교환": ["{p_을를} 받아 보니 생각보다 커서 반품하고 싶어요. 박스는 뜯지 않았습니다.",
              "{p} 색상이 주문과 다르게 왔어요. 교환해 주세요.",
              "같은 {p_이가} 두 번 결제됐습니다. 하나는 취소해 주세요.",
              "{p} 일주일 사용 후 환불이 가능한지 궁금합니다."],
    "구매 문의": ["{p} 사전 예약은 언제부터인가요? 가격도 알려 주세요.",
              "{p_과와} 기존 공기청정기의 차이가 궁금해요.",
              "{p} 출시일이 정해졌나요? 회사 단체 구매도 가능한지 문의드립니다.",
              "{p_을를} 반려동물 키우는 집에서 써도 괜찮을까요?"],
}
SAFETY_MSG = {
    "공기청정기": ["공기청정기 전원 어댑터가 손을 못 댈 정도로 뜨거워요. 타는 냄새도 났습니다. 바로 꺼 두었어요.",
              "공기청정기 어댑터 연결 부위가 녹은 것처럼 변형됐어요. 아이가 있는 집이라 너무 걱정됩니다.",
              "밤새 켜 둔 공기청정기 어댑터에서 '딱' 소리와 함께 연기가 났습니다."],
    "홈카메라": ["홈카메라 배터리가 부풀어서 케이스가 벌어졌어요. 계속 써도 되나요?",
             "홈카메라를 충전하다가 본체가 뜨거워지고 배터리 쪽이 볼록해졌습니다."],
    "로봇청소기": ["로봇청소기 충전 중에 충전대 쪽에서 탄 냄새가 납니다."],
}


def _batchim(word: str) -> bool:
    ch = word.strip()[-1]
    code = ord(ch) - 0xAC00
    if 0 <= code <= 11171:
        return code % 28 != 0
    return ch.lower() in "lmnr0136789"   # latin/digit endings read with a final consonant


def fill(tpl: str, p: str, n: int) -> str:
    b = _batchim(p)
    return tpl.format(p=p, n=n, p_을를=p + ("을" if b else "를"), p_이가=p + ("이" if b else "가"),
                      p_과와=p + ("과" if b else "와"))


def week_of(d: date) -> int:
    return (d - START).days // 7


def phone(rng: random.Random) -> str:
    # 010-0xxx-xxxx: 실제로 개통되지 않는 대역(가운데 자리가 0으로 시작)
    return f"010-0{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"


def build_rows(seed: int = 20261027) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    serial = 0
    for w, total in enumerate(WEEK_TOTALS):
        # category mix per week (story: app-connection spike after firmware day, safety piles up in week 4,
        # purchase inquiries for AirPole Pro rise every week)
        mix = {"배송": 13, "불량·고장": 13, "앱 연결": 7, "사용법": 11, "환불·교환": 8, "구매 문의": 4}
        mix["앱 연결"] += [0, 1, 11, 16][w]
        mix["구매 문의"] += [0, 3, 6, 10][w]
        mix["불량·고장"] += [0, 1, 1, 2][w]
        safety = [1, 1, 2, 6][w]
        cats = []
        weights = list(mix.items())
        n_regular = total - safety
        tot_w = sum(v for _, v in weights)
        # deterministic proportional allocation, remainder by largest fraction
        alloc = {k: int(n_regular * v / tot_w) for k, v in weights}
        rem = n_regular - sum(alloc.values())
        for k, _ in sorted(weights, key=lambda kv: -(n_regular * kv[1] / tot_w - int(n_regular * kv[1] / tot_w)))[:rem]:
            alloc[k] += 1
        for k, n in alloc.items():
            cats += [k] * n
        cats += ["안전 이슈"] * safety
        rng.shuffle(cats)
        w0, _ = WEEKS[w]
        for cat in cats:
            serial += 1
            day = w0 + timedelta(days=rng.randrange(7))
            if cat == "앱 연결" and w >= 2:
                day = max(day, FIRMWARE_DAY)          # spike starts the day the firmware shipped
                if day > WEEKS[w][1]:
                    day = WEEKS[w][1]
            hh = rng.choice([9, 9, 10, 10, 11, 13, 14, 14, 15, 16, 17, 19, 21])
            ts = datetime(day.year, day.month, day.day, hh, rng.randrange(60))
            if cat == "안전 이슈":
                prod = rng.choices(["공기청정기", "홈카메라", "로봇청소기"], [6, 3, 1])[0]
                if w == 3:
                    prod = rng.choices(["공기청정기", "홈카메라"], [5, 1])[0]
                msg = rng.choice(SAFETY_MSG[prod])
                sev = "긴급"
            else:
                if cat == "구매 문의":
                    prod = rng.choices(["에어폴 프로", "공기청정기", "로봇청소기"], [8, 1, 1])[0]
                elif cat == "앱 연결":
                    prod = "로봇청소기" if (w >= 2 and rng.random() < 0.8) else rng.choice(["로봇청소기", "스마트 조명", "홈카메라", "스마트 스피커"])
                elif cat == "불량·고장":
                    prod = rng.choices(PRODUCTS[:5], [3, 3, 2, 2, 3 + w])[0]
                else:
                    prod = rng.choices(PRODUCTS[:5], [4, 4, 2, 2, 2])[0]
                msg = fill(rng.choice(MSG[cat]), prod, rng.randint(3, 12))
                sev = {"불량·고장": rng.choices(["높음", "보통"], [2, 3])[0],
                       "앱 연결": rng.choices(["높음", "보통"], [1, 2])[0],
                       "환불·교환": "보통", "배송": rng.choices(["보통", "낮음"], [3, 1])[0],
                       "사용법": "낮음", "구매 문의": "낮음"}[cat]
            ch = rng.choices(CHANNELS, [5 - w, 3, 3 + w, 2 + w])[0]
            age_days = (date(2026, 10, 26) - day).days
            if cat == "안전 이슈" and w == 3:
                status = rng.choice(["접수", "처리중"])
            else:
                status = "완료" if age_days > 6 or rng.random() < 0.55 else rng.choice(["처리중", "접수"])
            hours = None
            csat = None
            if status == "완료":
                base = {"안전 이슈": 4, "배송": 20, "불량·고장": 40, "앱 연결": 30, "사용법": 6, "환불·교환": 28, "구매 문의": 5}[cat]
                hours = round(max(0.5, rng.gauss(base, base * 0.35)), 1)
                csat = rng.choices([5, 4, 3, 2, 1], [5, 4, 2, 1, 1 if cat != "앱 연결" else 3])[0]
            rows.append({
                "ticket_id": f"CX-{ts:%y%m}-{serial:04d}",
                "created_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "week_start": WEEKS[w][0].isoformat(),
                "channel": ch, "product": prod, "category": cat, "severity": sev, "status": status,
                "region": rng.choices(REGIONS, [45, 13, 11, 25, 6])[0],
                "customer_name": rng.choice(LAST) + rng.choice(FIRST), "phone": phone(rng),
                "message": msg,
                "resolution_hours": "" if hours is None else hours,
                "csat": "" if csat is None else csat,
            })
    rows.sort(key=lambda r: r["created_at"])
    for i, r in enumerate(rows, 1):                      # ids in time order
        r["ticket_id"] = f"CX-{r['created_at'][2:4]}{r['created_at'][5:7]}-{i:04d}"
    return rows


def facts(rows: list[dict]) -> dict:
    by_week = defaultdict(Counter)
    for r in rows:
        by_week[r["week_start"]]["total"] += 1
        by_week[r["week_start"]][r["category"]] += 1
    wk = sorted(by_week)
    last, prev = wk[-1], wk[-2]
    robo_app = Counter(r["week_start"] for r in rows if r["product"] == "로봇청소기" and r["category"] == "앱 연결")
    safety = [r for r in rows if r["category"] == "안전 이슈"]
    open_urgent = [r["ticket_id"] for r in safety if r["status"] != "완료"]
    airpole = Counter(r["week_start"] for r in rows if r["product"] == "에어폴 프로")
    chan = {w: Counter(r["channel"] for r in rows if r["week_start"] == w) for w in wk}
    done = [r for r in rows if r["status"] == "완료"]
    return {
        "rows": len(rows), "period": [rows[0]["created_at"][:10], rows[-1]["created_at"][:10]],
        "weekly_total": {w: by_week[w]["total"] for w in wk},
        "last_week": last, "prev_week": prev,
        "last_week_by_category": dict(by_week[last].most_common()),
        "prev_week_by_category": dict(by_week[prev].most_common()),
        "robot_app_connection_by_week": {w: robo_app.get(w, 0) for w in wk},
        "safety_total": len(safety), "safety_by_week": dict(Counter(r["week_start"] for r in safety)),
        "safety_by_product": dict(Counter(r["product"] for r in safety)),
        "open_urgent_ticket_ids": open_urgent,
        "airpole_by_week": {w: airpole.get(w, 0) for w in wk},
        "channel_by_week": {w: dict(chan[w]) for w in wk},
        "avg_resolution_hours_all": round(sum(float(r["resolution_hours"]) for r in done) / len(done), 1),
        "by_product_all": dict(Counter(r["product"] for r in rows).most_common()),
    }


README = """# cymbal-voc — Cymbal 고객의 소리(VOC) 인사이트 프로젝트

> {disc}

Cymbal CX(고객경험)팀의 주간 VOC 업무를 자동화하는 실습 프로젝트입니다. Antigravity 핸즈온 랩 Lab 3부터 Lab 10까지
**이 폴더 하나를 계속 키워 갑니다.**

| 단계 | 하는 일 |
|---|---|
| Lab 3 | 요청서와 데이터를 파악하고, 대시보드 계획(Implementation Plan)을 세웁니다 |
| Lab 4 | VOC 대시보드를 만들고 브라우저로 검증합니다 |
| Lab 5 | 팀 규칙(AGENTS.md)과 주간 보고 스킬(SKILL.md)을 만듭니다 |
| Lab 6 | MCP로 회사 BigQuery에 연결해 실데이터를 씁니다 |
| Lab 7 | 임원 보고용 슬라이드를 만듭니다 |
| Lab 8 | 누구나 물어볼 수 있는 VOC 분석 에이전트(ADK)를 만듭니다 |
| Lab 9 | 에이전트를 배포하고 Gemini Enterprise에 게시합니다 |
| Lab 10 | 매주 자동 보고(/schedule)와 서브에이전트로 운영을 자동화합니다 |

## 폴더
- `요청서_CX팀.md` — 출발점. CX팀장이 보낸 요청서
- `data/voc_tickets.csv` — 고객 문의 {n}건 ({p0} ~ {p1}, 4주). 열 설명은 아래 표
- `lab.env` — 실습 환경 변수(프로젝트 ID·리전·BigQuery·Gemini Enterprise 앱). **여기 값만 바꾸면** 모든 명령을 그대로 복사해 쓸 수 있습니다
- `setup/load_to_bigquery.sh` — Lab 6 준비: 같은 데이터를 내 프로젝트 BigQuery에 올리는 스크립트(lab.env 값을 읽습니다)
- `templates/exec_deck_template.html` — Lab 7 준비: 회사 임원 보고 슬라이드 템플릿(16:9, 외부 CDN 없음). 에이전트가 이 디자인으로 슬라이드를 만듭니다

## 데이터 열
| 열 | 뜻 |
|---|---|
| ticket_id | 문의 번호 |
| created_at | 접수 일시 (KST) |
| week_start | 접수 주의 월요일 |
| channel | 접수 채널 (전화·이메일·채팅·앱) |
| product | 제품 |
| category | 분류 (배송·불량·고장·앱 연결·사용법·환불·교환·구매 문의·안전 이슈) |
| severity | 긴급도 (긴급·높음·보통·낮음) — 안전 이슈는 모두 긴급 |
| status | 상태 (접수·처리중·완료) |
| region | 지역 |
| customer_name, phone | 고객 이름·연락처 (가상, **개인정보로 취급**) |
| message | 문의 내용 |
| resolution_hours | 처리 시간(시간, 완료 건만) |
| csat | 만족도 1~5 (완료 건만) |
"""

REQUEST = """# [요청서] 주간 VOC 보고 자동화

> {disc}

- 보낸 사람: CX(고객경험)팀장
- 받는 사람: 디지털혁신팀
- 날짜: 2026-10-26 (월)

## 배경
매주 월요일 아침, 지난주 고객 문의 로그를 엑셀로 손집계해 임원 보고를 만들고 있습니다. **반나절**이 걸리고,
지난달에는 **안전 이슈(긴급) 문의를 하루 늦게 발견**한 일도 있었습니다.

## 요청 사항
1. **VOC 대시보드** — 주간 문의 건수, 제품별·분류별 건수, 주간 추이, **긴급 문의 목록**을 한 화면에서
2. **주간 보고 자동화** — 매주 월요일 08:30까지 지난주 요약(핵심 3줄 · 표 · 원인 · 다음 할 일)과 임원 보고 슬라이드
3. **VOC 도우미** — 팀원 누구나 Gemini Enterprise에서 "지난주 긴급 문의 알려 줘"처럼 물어볼 수 있게

## 지켜야 할 것
- 고객 이름·연락처는 화면과 보고서에 **마스킹**해서 보여 주세요 (예: 김*수, 010-****-1234)
- 사내 보안 정책상 **외부 CDN·외부 스크립트는 쓸 수 없습니다** (차트도 직접 그리기)
- 화면과 보고서는 **한국어**로
- 안전 이슈는 건수가 적어도 **맨 위에** 보여 주세요

## 데이터
- 지금은 `data/voc_tickets.csv`(4주치)로 시작합니다.
- 원본은 매일 회사 **BigQuery**(`cymbal_cx.voc_tickets`)에 쌓입니다. 나중에는 이 데이터를 직접 써 주세요.
"""

LOADER = """#!/usr/bin/env bash
# Lab 6 준비 — data/voc_tickets.csv를 내 Google Cloud 프로젝트의 BigQuery에 올립니다.
# 실습용 가상 데이터. lab.env의 PROJECT_ID를 내 프로젝트로 바꾼 뒤 실행하세요:  bash setup/load_to_bigquery.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
# 변수는 프로젝트 맨 위의 lab.env 한 곳에서만 바꿉니다 (PROJECT_ID · BQ_DATASET · BQ_LOCATION · BQ_TABLE)
source "$HERE/lab.env"
DATASET="$BQ_DATASET"; LOCATION="$BQ_LOCATION"; TABLE="$BQ_TABLE"
SCHEMA="ticket_id:STRING,created_at:DATETIME,week_start:DATE,channel:STRING,product:STRING,category:STRING,severity:STRING,status:STRING,region:STRING,customer_name:STRING,phone:STRING,message:STRING,resolution_hours:FLOAT,csat:INTEGER"

bq --project_id="$PROJECT_ID" show --dataset "$PROJECT_ID:$DATASET" >/dev/null 2>&1 || \\
  bq --project_id="$PROJECT_ID" --location="$LOCATION" mk --dataset --description "Cymbal VOC (실습용 가상 데이터)" "$PROJECT_ID:$DATASET"
bq --project_id="$PROJECT_ID" --location="$LOCATION" load --replace --source_format=CSV --skip_leading_rows=1 \\
  "$PROJECT_ID:$DATASET.$TABLE" "$HERE/data/voc_tickets.csv" "$SCHEMA"
bq --project_id="$PROJECT_ID" query --use_legacy_sql=false \\
  "SELECT week_start, COUNT(*) AS tickets FROM \\`$PROJECT_ID.$DATASET.$TABLE\\` GROUP BY week_start ORDER BY week_start"
echo "완료: $PROJECT_ID.$DATASET.$TABLE"
"""

LABENV = """# 실습 환경 변수 — 내 환경에 맞게 아래 값만 바꾸세요. (Lab 6 BigQuery · Lab 8 에이전트 · Lab 9 배포/게시에서 사용)
# 실습용 가상 데이터 프로젝트입니다. 이 파일에 비밀번호나 키를 넣지 마세요.
PROJECT_ID="your-project-id"        # Google Cloud 프로젝트 ID
PROJECT_NUMBER="000000000000"       # 프로젝트 번호 (콘솔 홈 대시보드에서 확인)
REGION="us-central1"                # Agent Runtime 배포 리전
BQ_DATASET="cymbal_cx"              # BigQuery 데이터셋 (setup/load_to_bigquery.sh가 만듭니다)
BQ_TABLE="voc_tickets"              # BigQuery 테이블
BQ_LOCATION="US"                    # BigQuery 데이터셋 위치
GE_APP_ID="your-ge-app-id"          # Gemini Enterprise 앱(엔진) ID — 콘솔 Gemini Enterprise > 앱 목록
GE_LOCATION="global"                # Gemini Enterprise 앱 위치 (global | us | eu)
GE_DISPLAY_NAME="Cymbal VOC 분석가"  # Gemini Enterprise에 보일 에이전트 이름
"""


def main() -> None:
    rows = build_rows()
    f = facts(rows)
    (PROJ / "data").mkdir(parents=True, exist_ok=True)
    (PROJ / "setup").mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (PROJ / "data" / "voc_tickets.csv").write_text(buf.getvalue(), encoding="utf-8")
    (PROJ / "README.md").write_text(README.format(disc=DISC, n=len(rows), p0=f["period"][0], p1=f["period"][1]), encoding="utf-8")
    (PROJ / "요청서_CX팀.md").write_text(REQUEST.format(disc=DISC), encoding="utf-8")
    (PROJ / "setup" / "load_to_bigquery.sh").write_text(LOADER, encoding="utf-8")
    (PROJ / "lab.env").write_text(LABENV, encoding="utf-8")
    (PROJ / "templates").mkdir(parents=True, exist_ok=True)   # Lab 7 company deck template (single self-contained HTML)
    (PROJ / "templates" / "exec_deck_template.html").write_text(
        (HERE / "templates" / "exec_deck_template.html").read_text(encoding="utf-8"), encoding="utf-8")
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PROJ.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(BUILD).as_posix())
    print(json.dumps(f, ensure_ascii=False, indent=1))
    print("wrote", PROJ, ZIP)


if __name__ == "__main__":
    main()
