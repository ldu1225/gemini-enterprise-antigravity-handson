"""Build the Lab 6 skill package: SKILL.md (+ raw copy) and Cymbal_보고서스타일_스킬.zip (adapted from v1 build_skill.py).

Gemini Enterprise skill rules (docs, 2026-10-23 — same as v1):
- SKILL.md must START with YAML frontmatter between --- delimiters (no BOM / no leading text)
- name: 1–64 chars, [a-z0-9-], must equal the parent folder name in a ZIP
- description: 1–1,024 chars (we also keep it < 1,024 UTF-8 bytes for safety)
- ZIP: exactly one SKILL.md inside ONE top-level folder; no '..' paths
"""
from __future__ import annotations

import re
import zipfile

import yaml

import data_sales as S
from build_marketing_pdfs import BANNED
from common import DISCLAIMER, FILES, OUT

NAME = "cymbal-report-style"

DESCRIPTION = (
    "Cymbal(심벌) 사내 보고서 형식으로 답변·문서를 작성하는 스킬. 결론 먼저, 3줄 요약, 숫자는 표로, "
    "마지막은 담당·기한이 있는 다음 단계, 금지 표현 회피. 사용자가 보고서, 보고, 요약 보고, 주간 보고, 결과 보고, "
    "현황 보고, 임원 보고, 한 장 요약, 3줄 요약, 실적 정리, 분석 결과 정리를 요청하거나 executive summary, "
    "report, briefing을 요청할 때, 또는 데이터·회의록·문서를 보고서 형태로 정리해 달라고 할 때 사용."
)

F = S.facts()
_RQ2, _RQ3 = F["prod_q"]["로봇청소기"]["2분기"], F["prod_q"]["로봇청소기"]["3분기"]
_CQ2, _CQ3 = F["prod_q"]["홈카메라"]["2분기"], F["prod_q"]["홈카메라"]["3분기"]
_TQ2, _TQ3 = F["q_total"]["2분기"], F["q_total"]["3분기"]


def _pct(a, b):
    v = round(100 * (a / b - 1), 1)
    return f"▲ {v}" if v >= 0 else f"▼ {abs(v)}"


BODY = rf"""
# Cymbal 보고서 스타일 (cymbal-report-style)

> ※ {DISCLAIMER}. 이 스킬은 AI 업무 활용 핸즈온 실습용 **예시 보고서 지침**입니다. 보고서 본문에는 이 문구를 넣지 않습니다.

## 1. 언제 사용하나요
- "보고서로 정리해 줘", "3줄 요약", "임원 보고용", "주간 보고", "executive summary" 같은 요청
- 엑셀 데이터 분석 결과, 회의록, 검색 결과, 첨부 문서를 보고서 형태로 바꿀 때

## 2. 반드시 지킬 형식 (순서 고정)
1. **제목**: `[보고] 주제 (YYYY.MM.DD, 작성 부서)` — 날짜를 모르면 오늘 날짜를 씁니다.
2. **결론**: 첫 줄에 `결론:`으로 시작하는 1~2문장. 무엇이, 얼마나, 그래서 무엇을 해야 하는지 씁니다.
3. **3줄 요약**: `3줄 요약` 제목 아래 정확히 3개의 글머리표. 각 줄에 핵심 숫자 1개 이상을 **굵게** 표시합니다.
4. **근거 표**: 숫자를 3개 이상 비교하면 반드시 마크다운 표로 씁니다. 표 위에 `(단위: 백만원, %)`처럼 단위와 기간을 적고, 증감은 ▲/▼로 표시합니다. 표는 최대 2개, 6행 × 6열 이내입니다.
5. **원인·시사점**: 글머리표 2~4개. 데이터로 확인된 사실과 추정을 구분하고, 추정에는 `(추정)`을 붙입니다.
6. **다음 단계**: `다음 단계` 제목 아래 2~3개. 각 항목은 `담당 / 할 일 / 기한` 형식입니다. 예) `영업기획팀 / 홈카메라 재고 할인안 검토 / 11.6(금)`
7. **작성 기준**: 마지막 줄에 `※ 작성 기준: 데이터 출처, 기준 기간`을 씁니다.

## 3. 표현 규칙
- 존댓말 평서문(~입니다, ~했습니다)으로 짧게 씁니다. 한 문장은 50자 안팎.
- 숫자: 천 단위 쉼표, 금액 단위(원·백만원·억원)와 비교 기준(전월 대비, 전분기 대비, 목표 대비)을 함께 씁니다.
- 비율은 소수점 첫째 자리까지. 계산한 값은 데이터와 다시 대조한 뒤 씁니다.
- 데이터에 없는 수치는 만들지 않고 `확인 필요`라고 씁니다.
- 고객·개인 이름은 `고객 A`, `담당자 B`처럼 익명화합니다. 경쟁사는 `경쟁사 A`로만 씁니다.

## 4. 금지 표현
{chr(10).join(f"- {b}" for b in BANNED)}
- 인사말·맺음말("안녕하세요", "감사합니다", "도움이 되셨길 바랍니다")
- 이모지, 느낌표, 근거 없는 형용사("획기적인", "놀라운", "엄청난")
- 결론 없이 배경 설명부터 시작하는 글

## 5. 출력 방식
- 채팅 답변은 마크다운으로 씁니다. 사용자가 문서·슬라이드를 원하면 Canvas로 작성하고 제목 앞에 `[보고]`를 붙입니다.
- 수정 요청을 받으면 형식(2장)을 유지한 채 해당 부분만 고칩니다.
- 형식에 맞추기 어려운 질문(단순 사실 확인 등)은 형식 없이 짧게 답해도 됩니다.

## 6. 예시 (실습용 가상 데이터)

[보고] 3분기 제품별 매출 점검 (2026.10.26, 영업기획팀)

결론: 3분기 전체 매출은 {_TQ3:,.1f}백만원으로 2분기 대비 {abs(round(100*(_TQ3/_TQ2-1),1))}% 줄었습니다. 로봇청소기는 목표를 크게 넘었지만 홈카메라가 크게 밑돌아, 홈카메라 회복 대책이 필요합니다.

3줄 요약
- 로봇청소기 3분기 매출 **목표 대비 {F["achv_q"]["로봇청소기"]["3분기"]}%**, 9월 매출 1위 제품
- 홈카메라 3분기 매출 **전분기 대비 {F["camera_q3_vs_q2_pct"]}%**, 목표 달성률 **{F["achv_q"]["홈카메라"]["3분기"]}%**
- 온라인 매출 비중 **1월 {F["online_share"]["2026-01"]}% → 9월 {F["online_share"]["2026-09"]}%**로 상승

(단위: 백만원, %, 2026년 2~3분기)

| 제품 | 2분기 매출 | 3분기 매출 | 전분기 대비(%) | 3분기 목표 달성률(%) |
|---|---:|---:|---:|---:|
| 로봇청소기 | {_RQ2:,.1f} | {_RQ3:,.1f} | {_pct(_RQ3, _RQ2)} | {F["achv_q"]["로봇청소기"]["3분기"]} |
| 홈카메라 | {_CQ2:,.1f} | {_CQ3:,.1f} | {_pct(_CQ3, _CQ2)} | {F["achv_q"]["홈카메라"]["3분기"]} |
| 전체 | {_TQ2:,.1f} | {_TQ3:,.1f} | {_pct(_TQ3, _TQ2)} | - |

원인·시사점
- 홈카메라는 7월부터 판매 수량이 급감했습니다. 원인은 매출 데이터에 없어 고객 문의·반품 데이터 확인이 필요합니다.
- 온라인 평균판매가는 오프라인보다 5% 낮아, 온라인 비중이 커질수록 매출총이익률이 낮아질 수 있습니다 (추정).

다음 단계
- 영업기획팀 / 홈카메라 판매 감소 원인 분석(고객 문의·반품 데이터) / 11.6(금)
- 온라인사업팀 / 로봇청소기 4분기 재고 확보 계획 / 11.13(금)

※ 작성 기준: Cymbal_제품별_지역별_월별매출_2026_가상.xlsx, 2026년 7~9월
"""

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ZIP_DATE = (2026, 10, 26, 9, 0, 0)


def skill_md() -> str:
    assert '"' not in DESCRIPTION and "\\" not in DESCRIPTION
    return f'---\nname: {NAME}\ndescription: "{DESCRIPTION}"\n---\n{BODY.lstrip(chr(10))}'


def validate(text: str) -> dict:
    assert text.startswith("---\n"), "frontmatter must start at byte 0"
    _, fm, body = text.split("---\n", 2)
    meta = yaml.safe_load(fm)
    assert set(meta) == {"name", "description"}, meta.keys()
    name, desc = meta["name"], meta["description"]
    assert 1 <= len(name) <= 64 and NAME_RE.match(name) and name == NAME
    assert 1 <= len(desc) <= 1024 and len(desc.encode("utf-8")) < 1024, (len(desc), len(desc.encode()))
    assert len(body) <= 500_000
    return {"name": name, "description_chars": len(desc), "description_bytes": len(desc.encode("utf-8")),
            "body_chars": len(body)}


def build() -> dict:
    text = skill_md()
    info = validate(text)
    md_path = OUT / FILES["skill_md"]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_bytes(text.encode("utf-8"))
    zpath = OUT / FILES["skill_zip"]
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        zi = zipfile.ZipInfo(f"{NAME}/SKILL.md", date_time=ZIP_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, text.encode("utf-8"))
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        assert names == [f"{NAME}/SKILL.md"], names
        assert z.read(names[0]).decode("utf-8") == text
    info.update({"zip_entries": names, "zip_bytes": zpath.stat().st_size, "md_bytes": md_path.stat().st_size})
    return info


if __name__ == "__main__":
    import json
    print(json.dumps(build(), ensure_ascii=False, indent=1))
