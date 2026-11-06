"""Bundle zip (Cymbal_실습파일_전체.zip) + manifest.json (adapted from v1 build_bundle.py).

Answer keys are instructor-only and are NOT bundled.
"""
from __future__ import annotations

import json
import zipfile

from common import DISCLAIMER, FILES, OUT, nfc, preview_path

ZIP_DATE = (2026, 10, 26, 9, 0, 0)
ROOT_DIR = nfc("Cymbal_실습파일")

ENTRIES = [  # key, title, description (one line), usedIn
    ("sales", "제품별·지역별 월별 매출 2026 (가상)",
     "2026년 1~9월 5개 제품 × 5개 지역 월별 판매수량·매출·매출총이익과 월간 목표 — 데이터 분석·차트·Canvas 실습용 엑셀", "Lab 3"),
    ("cs", "고객 문의 로그 2026-10 (가상)",
     "10월 고객 문의 60건(채널·제품·문의내용) — 분류·긴급도 판단과 답변 초안을 만드는 워크플로 실습용 엑셀", "Lab 8"),
    ("travel", "출장비 및 경비처리 규정 (가상)",
     "직급·지역별 일비·숙박 한도, 법인카드, 7영업일 정산·지연 조치, 영수증·접대비 규정 7쪽 PDF — 사내 지원 데스크 에이전트 지식", "Lab 7"),
    ("leave", "휴가 및 근무제도 규정 (가상)",
     "연차 발생·이월, 반차·반반차, 경조사 휴가표, 재택근무 주 2일, 코어타임 6쪽 PDF — 사내 지원 데스크 에이전트 지식", "Lab 7"),
    ("it", "IT보안 및 계정관리 가이드 (가상)",
     "비밀번호·계정 잠금 해제·장비·소프트웨어 승인·보안 사고 신고·헬프데스크 티켓 6쪽 PDF — 사내 지원 데스크 에이전트 지식", "Lab 7"),
    ("brief", "신제품 브리프 — AirPole Pro (가상)",
     "기둥형 스마트 공기청정기 런칭 브리프(타깃·기능·카피·톤앤매너·티저 스토리보드) 3쪽 PDF — 이미지·동영상 프롬프트 소스", "Lab 4"),
    ("brand", "브랜드 가이드 (가상)",
     "브랜드 컬러·워드마크·톤 오브 보이스·금지 표현·고객 응대 원칙 2쪽 PDF — 스킬·톤앤매너 기준", "Lab 4 · 6"),
    ("skill_zip", "보고서 스타일 스킬 (ZIP)",
     "결론 먼저·3줄 요약·표·다음 단계·금지 표현을 적용하는 cymbal-report-style 스킬 — 스킬 업로드에 그대로 올리는 ZIP", "Lab 6"),
    ("skill_md", "보고서 스타일 스킬 원본 (SKILL.md)", "cymbal-report-style 스킬 원본 마크다운 — 내용 확인용", "Lab 6"),
]

README = f"""Cymbal(심벌) AI 업무 활용 핸즈온 — 실습 파일 안내
※ {DISCLAIMER}
Cymbal(심벌)은 실습을 위해 만든 가상의 소비자 가전·스마트홈 회사입니다. 모든 수치·규정·제품·인물은 가상입니다.

[파일 목록]
1) {FILES['sales']}  (Lab 3 데이터 분석 + Canvas)
2) {FILES['cs']}  (Lab 8 워크플로 — 고객 문의 자동 분류·답변 초안)
3) {FILES['travel']}  (Lab 7 사내 지원 데스크 에이전트)
4) {FILES['leave']}  (Lab 7)
5) {FILES['it']}  (Lab 7)
6) {FILES['brief']}  (Lab 4 이미지·동영상)
7) {FILES['brand']}  (Lab 4·6)
8) {FILES['skill_zip']}  (Lab 6 스킬 — ZIP 그대로 업로드)
   skills/cymbal-report-style/SKILL.md 는 같은 스킬의 원본(내용 확인용)

[주의]
- 실습용 가상 데이터이므로 실제 업무 의사결정에 사용하지 마세요.
"""


def _members() -> list[str]:
    return [FILES[k] for k, *_ in ENTRIES]


def build_bundle() -> dict:
    zpath = OUT / FILES["bundle"]
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        zi = zipfile.ZipInfo(f"{ROOT_DIR}/README_읽어주세요.txt", date_time=ZIP_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, ("\ufeff" + README).replace("\n", "\r\n").encode("utf-8"))
        for m in _members():
            src = OUT / m
            assert src.is_file(), src
            arc = f"{ROOT_DIR}/{nfc(m)}"
            assert ".." not in arc.split("/")
            zi = zipfile.ZipInfo(arc, date_time=ZIP_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, src.read_bytes())
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        names = z.namelist()
    return {"zip": zpath.name, "bytes": zpath.stat().st_size, "entries": names}


def build_manifest() -> list[dict]:
    items = []
    for key, title, desc, used in ENTRIES:
        f = FILES[key]
        prev = preview_path("SKILL.md" if key == "skill_md" else f)
        if key == "skill_zip":
            prev = preview_path("SKILL.md")
        items.append({"file": f, "title": title, "description": desc, "usedIn": used,
                      "sizeBytes": (OUT / f).stat().st_size, "preview": f"previews/{prev.name}"})
    b = OUT / FILES["bundle"]
    items.append({"file": FILES["bundle"], "title": "실습 파일 전체 다운로드 (ZIP)",
                  "description": "실습 파일 8종(엑셀 2, PDF 5, 스킬)과 안내문을 한 번에 내려받는 압축 파일",
                  "usedIn": "전체 실습", "sizeBytes": b.stat().st_size,
                  "preview": f"previews/{preview_path(FILES['bundle']).name}"})
    for it in items:
        assert (OUT / it["preview"]).is_file(), it["preview"]
    (OUT / "manifest.json").write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


if __name__ == "__main__":
    print(json.dumps(build_bundle(), ensure_ascii=False, indent=1))
    print(len(build_manifest()), "manifest entries")
