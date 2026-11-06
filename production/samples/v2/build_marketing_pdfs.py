"""Build the two short marketing documents (FICTIONAL):

- Cymbal_신제품_브리프_에어폴_프로_가상.pdf  (2~3쪽, Lab 4 이미지·동영상 프롬프트 소스)
- Cymbal_브랜드_가이드_가상.pdf              (2쪽, Lab 6 스킬·Lab 4 톤앤매너 소스)
"""
from __future__ import annotations

from common import (BLUE, CORAL, DANGER, DISCLAIMER, FILES, INK, LINE, OK, SUB, VIOLET, e, out_path,
                    preview_path, render_document)
from doccss import ACC_DARK, BASE_CSS, arcs_art, blk, h3, note, page_template, sec, table, ul

# ---------------------------------------------------------------- shared facts
PRODUCT = "Cymbal AirPole Pro"
PRODUCT_KO = "에어폴 프로"
MODEL = "CY-AP700"
LAUNCH = "2026년 12월 1일(화)"
PREORDER = "2026년 11월 17일(화) ~ 11월 30일(월)"
PRICE = 699000
PREORDER_PRICE = 629100   # 10% 할인
COPY_MAIN = "공기는 맑게, 공간은 넓게"
assert round(PRICE * 0.9) == PREORDER_PRICE

BRAND_COLORS = [  # name, hex, role, share
    ("Cymbal Blue", BLUE, "주 색상 — 로고, 제목 강조, 버튼, 핵심 수치", "30%"),
    ("Ink", INK, "본문 텍스트, 표 머리글", "본문"),
    ("Mist", "#F7F8FA", "배경, 카드, 여백", "60%"),
    ("Violet", VIOLET, "보조 강조 — 그라디언트, 일러스트 (아껴서)", "10% 이내"),
    ("Coral", CORAL, "포인트 — 프로모션 배지, 강조 1곳 (아껴서)", "10% 이내"),
    ("Leaf", OK, "긍정 상태 — 달성, 정상, 완료", "상태 표시"),
]
BANNED = ["세계 최초·업계 유일 (근거 없는 최상급)", "100% 제거·완벽 차단", "질병 예방·치료 등 의학적 효능",
          "경쟁사 실명 언급·비교 비하", "'대박', '역대급' 등 유행어·속어", "공포·불안을 자극하는 표현 (예: '숨 쉬기 무서운 집')"]

DOC_CSS = f"""
.hero {{ border-radius: 4mm; overflow: hidden; color: #fff; padding: 7mm 8mm 6mm; margin-bottom: 4mm;
  background: linear-gradient(135deg, #1B3F8F 0%, {BLUE} 52%, {VIOLET} 100%); }}
.hero .top {{ display: flex; align-items: center; gap: 3mm; font-size: 8.4pt; font-weight: 700; color: rgba(255,255,255,.9); }}
.hero .top .wm {{ font-size: 13pt; font-weight: 800; color: #fff; letter-spacing: .02em; }}
.hero .top .vchip {{ margin-left: auto; background: #fff; color: {DANGER}; border-radius: 999px; padding: .6mm 3mm; font-weight: 800; }}
.hero h1 {{ font-size: 25pt; font-weight: 800; letter-spacing: -0.03em; line-height: 1.2; margin-top: 6mm; }}
.hero .sub {{ font-size: 10pt; margin-top: 2mm; color: rgba(255,255,255,.94); }}
.hero .chips {{ display: flex; gap: 2mm; margin-top: 5mm; flex-wrap: wrap; }}
.hero .chips span {{ border: .3mm solid rgba(255,255,255,.7); border-radius: 999px; padding: .6mm 3mm; font-size: 7.8pt; font-weight: 700; }}
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.4mm; margin: 1mm 0 3mm; }}
.kpi {{ background: #F7F8FA; border: .25mm solid {LINE}; border-radius: 3mm; padding: 2.6mm 3mm; }}
.kpi .l {{ font-size: 7.6pt; color: {SUB}; font-weight: 700; }}
.kpi .v {{ font-size: 12.5pt; font-weight: 800; color: {INK}; margin-top: .6mm; letter-spacing: -0.02em; }}
.kpi .v.acc {{ color: {ACC_DARK}; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
.card {{ border: .25mm solid {LINE}; border-radius: 3mm; padding: 3mm 3.4mm; background: #fff; }}
.card h4 {{ font-size: 9.2pt; font-weight: 800; margin-bottom: 1.2mm; color: {ACC_DARK}; }}
.feat {{ display: grid; grid-template-columns: 7mm 1fr; gap: 1mm 2.4mm; padding: 1.6mm 0; border-bottom: .25mm solid {LINE}; }}
.feat .n {{ width: 6.4mm; height: 6.4mm; border-radius: 2mm; background: #EEF3FE; color: {ACC_DARK}; font-weight: 800;
  display: flex; align-items: center; justify-content: center; font-size: 8.4pt; }}
.feat .t {{ font-weight: 800; font-size: 9.4pt; align-self: center; }}
.feat .d {{ grid-column: 2; font-size: 8.6pt; color: #2B3038; }}
.copy {{ font-size: 15pt; font-weight: 800; letter-spacing: -0.02em; color: {INK}; margin: 1mm 0 1.6mm; }}
.copy em {{ font-style: normal; color: {ACC_DARK}; }}
.swatches {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.6mm; margin: 1mm 0 2mm; }}
.sw {{ border: .25mm solid {LINE}; border-radius: 3mm; overflow: hidden; }}
.sw .chip {{ height: 13mm; }}
.sw .meta {{ padding: 1.6mm 2.4mm 2mm; font-size: 7.9pt; }}
.sw .meta b {{ font-size: 9pt; }}
.sw .meta .hex {{ color: {SUB}; font-weight: 700; margin-left: 1.4mm; }}
.wordmark-demo {{ display: flex; gap: 3mm; align-items: stretch; margin: 1mm 0 2mm; }}
.wordmark-demo div {{ flex: 1; border-radius: 3mm; display: flex; align-items: center; justify-content: center; height: 18mm;
  font-size: 17pt; font-weight: 800; letter-spacing: .02em; }}
.wordmark-demo .a {{ background: #F7F8FA; color: {BLUE}; border: .25mm solid {LINE}; }}
.wordmark-demo .b {{ background: {BLUE}; color: #fff; }}
.wordmark-demo .c {{ background: #0B0F17; color: #fff; }}
table.t td.do {{ color: {OK}; font-weight: 700; }}
table.t td.dont {{ color: {DANGER}; font-weight: 700; }}
"""


def hero(kicker: str, title: str, sub: str, chips: list[str], seed: int) -> str:
    chips_html = "".join(f"<span>{e(c)}</span>" for c in chips)
    return (f'<section class="blk keep hero" data-id="hero"><div class="top"><span class="wm">Cymbal</span><span>{e(kicker)}</span>'
            f'<span class="vchip">실습용 가상 데이터</span></div><h1>{title}</h1><div class="sub">{e(sub)}</div>'
            f'<div class="chips">{chips_html}</div></section>')


def kpis(items: list[tuple[str, str, bool]]) -> str:
    return '<section class="blk keep kpis" data-id="kpis">' + "".join(
        f'<div class="kpi"><div class="l">{e(l)}</div><div class="v{" acc" if a else ""}">{e(v)}</div></div>' for l, v, a in items) + "</section>"


def feat(i: int, t: str, d: str) -> str:
    return f'<div class="feat"><span class="n">{i}</span><span class="t">{e(t)}</span><span class="d">{d}</span></div>'


# ---------------------------------------------------------------- product brief
def brief_blocks() -> list[str]:
    B = [hero("신제품 마케팅 브리프 · 마케팅팀(가상)", f"{e(PRODUCT)}<br>({e(PRODUCT_KO)}) 런칭 브리프",
              "거실 한쪽에 세워 두는 슬림 기둥형 스마트 공기청정기", [f"모델 {MODEL}", f"출시 {LAUNCH}", "문서번호 CYM-MKT-BRF-2611", "대외비 · 실습용"], 21),
         kpis([("출시일", LAUNCH, True), ("판매가", f"{PRICE:,}원", False), ("사전 예약가 (10%↓)", f"{PREORDER_PRICE:,}원", False),
               ("적용 면적", "62㎡ (약 19평)", False)])]
    B.append(sec("1", "제품 개요", "OVERVIEW",
                 f"<p><b>{e(PRODUCT)}</b>는 바닥 면적이 A4 용지 반 장 정도(지름 22cm)인 <b>높이 110cm 기둥형</b> 공기청정기입니다. "
                 "360° 전면 흡입 구조로 거실 구석에 두어도 공기를 고르게 정화하고, 공기질에 따라 색이 바뀌는 무드 라이트 링이 "
                 "인테리어 조명 역할을 합니다. Cymbal Home 앱과 연동해 집 밖에서도 공기질을 확인하고 제어할 수 있습니다.</p>"
                 + table(["항목", "사양 (가상)", "항목", "사양 (가상)"],
                         [["크기", "지름 22cm × 높이 110cm", "무게", "6.8kg"],
                          ["CADR(청정 능력)", "7.2m³/분", "소음", "21dB(수면) ~ 48dB(터보)"],
                          ["필터", "H13 HEPA + 활성탄 탈취 + 극세사 프리필터", "필터 수명", "약 12개월 (앱 알림)"],
                          ["센서", "PM1.0·PM2.5·PM10, VOC(냄새), CO2", "소비전력", "최대 45W"],
                          ["색상", "미스트 화이트, 스톤 그레이", "보증", "본체 2년, 모터 5년"]],
                         ["k", "", "k", ""], widths=["17%", "33%", "17%", "33%"]), "b1"))
    B.append(sec("2", "타깃 고객과 인사이트", "TARGET & INSIGHT",
                 '<div class="two"><div class="card"><h4>1차 타깃</h4>'
                 + ul(["30~40대 맞벌이 부부, 영유아·초등 자녀", "거실 중심 생활, 인테리어에 신경 쓰는 30평대 이하 아파트",
                       "퇴근 후·주말에 집에서 보내는 시간이 많음"])
                 + '</div><div class="card"><h4>2차 타깃</h4>'
                 + ul(["반려동물(강아지·고양이) 가정 — 털·냄새 고민", "1~2인 가구 소형 주거 — 공간 효율 중시",
                       "선물 수요(집들이·출산 선물)"]) + "</div></div>"
                 + note("핵심 인사이트", "“공기청정기는 꼭 필요한데, 거실에 두면 자리만 차지하고 인테리어를 해친다.” — 고객 인터뷰 24명 중 17명이 "
                        "'크기와 디자인'을 구매 망설임 1순위로 꼽음 (가상 조사)."), "b2"))
    B.append(sec("3", "핵심 기능 (커뮤니케이션 우선순위 순)", "KEY FEATURES",
                 feat(1, "공간을 덜 차지하는 기둥형 디자인", "바닥 면적 지름 22cm. 소파 옆·TV 옆 자투리 공간에 쏙 들어가며 360° 흡입으로 위치 제약이 적음.")
                 + feat(2, "AI 자동 모드", "5종 센서가 공기질을 실시간 감지해 풍량을 자동 조절. 요리·청소 후 냄새(VOC)가 올라가면 먼저 반응.")
                 + feat(3, "21dB 수면 모드", "도서관보다 조용한 수준. 수면 모드에서는 무드 라이트가 자동으로 꺼짐.")
                 + feat(4, "무드 라이트 링", "공기질에 따라 파랑(좋음)·초록(보통)·주황(나쁨)으로 은은하게 표시. 밝기 3단계 조절.")
                 + feat(5, "반려동물 모드 + 앱 연동", "털 흡입을 위한 하단 흡입 강화, 탈취 강화. Cymbal Home 앱에서 필터 수명·공기질 기록 확인."), "b3"))
    B.append(sec("4", "경쟁 포지셔닝", "POSITIONING",
                 table(["구분", "경쟁사 A 대형 박스형", "경쟁사 B 저가 소형", f"{PRODUCT_KO} (우리)"],
                       [["가격대", "80만~100만원대", "10만~20만원대", f"<b>{PRICE // 10000}만원대</b>"],
                        ["청정 능력", "매우 높음", "낮음 (10평 이하)", "<b>높음 (19평)</b>"],
                        ["공간·디자인", "큼, 존재감 강함", "작지만 평범", "<b>슬림 기둥형, 조명 겸용</b>"],
                        ["스마트 기능", "앱 지원", "없음", "<b>AI 자동 + 앱 + 반려동물 모드</b>"]],
                       ["k", "c", "c", "c"], widths=["19%", "27%", "27%", "27%"], raw=True)
                 + '<p class="fn">※ 경쟁사는 외부 커뮤니케이션에서 절대 실명·로고를 쓰지 않으며, 비교 광고를 하지 않는다.</p>', "b4"))
    B.append(sec("5", "핵심 메시지와 카피", "MESSAGE",
                 f'<div class="copy">“<em>{e(COPY_MAIN)}</em>”</div>'
                 + ul(["서브 카피 ①: 자리는 반으로, 맑음은 그대로.", "서브 카피 ②: 아이가 잠든 밤에도, 21dB로 조용히.",
                       "서브 카피 ③: 거실의 빛이 되는 공기청정기."])
                 + "<p>Reason to believe: 지름 22cm 기둥형 · H13 HEPA · 5종 센서 AI 자동 모드 · 21dB 수면 모드</p>", "b5"))
    B.append(sec("6", "톤앤매너 (이미지·영상 공통)", "TONE & MANNER",
                 '<div class="two"><div class="card"><h4>이렇게</h4>'
                 + ul(["<b>차분하고 따뜻한 미니멀</b> — 넓은 여백, 정돈된 거실", "<b>아침·오후의 자연광</b>, 부드러운 그림자",
                       "색감: 미스트 화이트·우드·연한 세이지, 포인트로 Cymbal Blue 무드 라이트",
                       "사람은 자연스러운 일상 장면(낮잠, 책 읽기, 반려견과 휴식)으로", "제품은 화면의 1/3 이하, 공간 속에 어우러지게"])
                 + '</div><div class="card"><h4>이렇게 하지 않기</h4>'
                 + ul(["어둡고 탁한 공기·미세먼지 공포를 강조하는 장면", "의학적 효능을 암시하는 문구·이미지 (병원, 마스크 쓴 아이)",
                       "아이가 제품을 만지거나 기대는 장면 (안전)", "과도한 네온·SF 느낌, 과장된 공기 입자 CG",
                       "경쟁사 제품과 나란히 놓는 비교 장면"]) + "</div></div>", "b6"))
    B.append(sec("7", "캠페인 산출물과 일정", "DELIVERABLES",
                 table(["산출물", "규격", "용도", "마감 (가상)"],
                       [["키 비주얼 이미지 3종", "16:9 · 1:1 · 9:16", "온라인몰 배너, SNS 피드·스토리", "11월 10일(화)"],
                        ["티저 영상 1편", "15초, 16:9, 자막 포함", "SNS·온라인몰 상세 페이지", "11월 13일(금)"],
                        ["사전 예약 안내 카드뉴스", "1:1, 5장", "SNS, 뉴스레터", "11월 16일(월)"]],
                       ["k", "c", "", "c"], widths=["26%", "22%", "32%", "20%"])
                 + h3("7.1", "15초 티저 스토리보드")
                 + table(["시간", "장면", "자막·사운드"],
                         [["0~3초", "아침 햇살이 드는 정돈된 거실, 카메라가 천천히 옆으로 이동", "잔잔한 피아노"],
                          ["3~7초", "소파 옆 기둥형 제품 클로즈업, 무드 라이트 링이 초록 → 파랑으로 바뀜", "“공기질 좋음”"],
                          ["7~11초", "아이와 강아지가 소파에서 낮잠, 제품은 배경에 조용히", "“21dB, 아이가 잠든 밤에도”"],
                          ["11~15초", "거실 전체 와이드 샷 + 제품명 + 카피 + 출시일", f"“{COPY_MAIN}” · {PRODUCT} · 12월 1일 출시"]],
                         ["c", "", ""], widths=["13%", "55%", "32%"])
                 + note("프롬프트 작성 팁", "이미지·영상 프롬프트에는 ① 장면(공간·시간대·빛) ② 피사체(제품 형태: 흰색 슬림 원기둥, 상단 빛 링) "
                        "③ 분위기(차분·따뜻한 미니멀) ④ 구도·비율 ⑤ 넣지 말 것(텍스트 왜곡, 로고, 공포 분위기)을 포함한다. "
                        "브랜드 컬러와 금지 표현은 「Cymbal 브랜드 가이드」를 따른다."), "b7"))
    return B


# ---------------------------------------------------------------- brand guide
def brand_blocks() -> list[str]:
    sw = "".join(f'<div class="sw"><div class="chip" style="background:{h};{"border-bottom:.25mm solid #E5E7EB" if h == "#F7F8FA" else ""}"></div>'
                 f'<div class="meta"><b>{e(n)}</b><span class="hex">{e(h)}</span><br>{e(r)} · 비중 {e(s)}</div></div>'
                 for n, h, r, s in BRAND_COLORS)
    B = [hero("브랜드 가이드 · 브랜드커뮤니케이션팀(가상)", "Cymbal 브랜드 가이드",
              "모든 문서·보고서·마케팅 콘텐츠에 공통으로 적용하는 최소 규칙", ["CYM-BRD-GDE-01", "Rev. 2.0 · 2026-07-01", "사내한정 · 실습용"], 31)]
    B.append(sec("1", "브랜드 핵심", "BRAND CORE",
                 '<div class="two"><div class="card"><h4>미션</h4><p><b>“매일의 집을 더 편안하게.”</b> Cymbal은 복잡한 기술을 '
                 "누구나 쉽게 쓰는 스마트홈 제품으로 바꿉니다.</p></div>"
                 '<div class="card"><h4>브랜드 성격 3가지</h4>'
                 + ul(["<b>친절한</b> — 고객의 입장에서, 쉬운 말로", "<b>명료한</b> — 핵심부터, 군더더기 없이",
                       "<b>믿을 수 있는</b> — 근거 있는 숫자, 과장 없이"]) + "</div></div>", "br1"))
    B.append(sec("2", "워드마크", "WORDMARK",
                 '<div class="wordmark-demo"><div class="a">Cymbal</div><div class="b">Cymbal</div><div class="c">Cymbal</div></div>'
                 + ul(["워드마크는 영문 <b>Cymbal</b> 한 가지이며, 한글 표기는 <b>심벌</b>로 통일한다 (시멀·심발 등 사용 금지).",
                       "주변에 글자 높이만큼 여백을 두고, 최소 크기는 인쇄 12mm·화면 64px 이상으로 한다.",
                       "허용 색상: Cymbal Blue, 흰색(파란·어두운 배경 위). 늘이기·기울이기·그림자·그라디언트 채우기는 금지."]), "br2"))
    B.append(sec("3", "컬러 팔레트", "COLOR",
                 f'<div class="swatches">{sw}</div>'
                 + '<p class="fn">※ 기본 비율 60(Mist) : 30(Blue) : 10(Violet·Coral). 상태 표시는 성공 #1E8E3E · 경고 #F29900 · 위험 #D93025.</p>'
                 + h3("3.1", "타이포그래피")
                 + ul(["한글: <b>Pretendard</b> (제목 Bold/ExtraBold, 본문 Regular) — 없으면 시스템 기본 고딕체",
                       "숫자·영문: <b>Inter</b> · 코드: JetBrains Mono", "본문 최소 10pt(문서)·16px(화면), 줄 간격 150%"]), "br3"))
    B.append(sec("4", "톤 오브 보이스", "TONE OF VOICE",
                 table(["원칙", "이렇게 쓴다 (Do)", "이렇게 쓰지 않는다 (Don't)"],
                       [["쉬운 말", "필터를 바꿀 때가 되면 앱에서 알려 드려요.", "필터 교체 주기 도래 시 푸시 노티피케이션이 발송됩니다."],
                        ["핵심 먼저", "3분기 매출은 목표보다 4% 낮습니다. 원인은 홈카메라 판매 감소입니다.", "여러 가지 대내외 환경 변화 속에서 다양한 노력을 기울였으나…"],
                        ["근거 있는 숫자", "수면 모드 소음 21dB (자체 측정, 가상)", "세상에서 가장 조용한 공기청정기"],
                        ["존중하는 존댓말", "불편을 드려 죄송합니다. 오늘 안에 다시 연락드리겠습니다.", "고객님 사용 부주의로 보입니다."]],
                       ["k", "do", "dont"], widths=["16%", "42%", "42%"]), "br4"))
    B.append(sec("5", "금지 표현", "DON'T SAY",
                 ul([e(x) for x in BANNED])
                 + h3("5.1", "사내 보고서 기본 형식")
                 + ul(["<b>결론 먼저</b>: 첫 문장에 결론과 핵심 숫자", "<b>3줄 요약</b>: 본문 앞에 핵심 3줄",
                       "<b>표</b>: 숫자 비교는 표로 (단위·기간 명시)", "<b>다음 단계</b>: 담당·기한이 있는 실행 항목으로 마무리",
                       "숫자는 천 단위 쉼표, 금액 단위(원·백만원·억원)와 기준 기간을 함께 쓴다."])
                 + '<p class="fn">※ 보고서 형식은 사내 AI 도구의 스킬 「cymbal-report-style」로 자동 적용할 수 있다(실습 Lab 6).</p>', "br5"))
    B.append(sec("6", "고객 응대 답변 원칙", "CUSTOMER REPLIES",
                 table(["순서", "내용", "예시 문장"],
                       [["① 공감", "불편에 대한 사과·공감 한 문장", "배송이 늦어져 많이 답답하셨을 것 같습니다. 죄송합니다."],
                        ["② 해결", "확인한 사실과 해결 방법 (추측 금지)", "확인해 보니 물류센터 출고가 하루 지연되었습니다. 내일(10/27) 도착 예정입니다."],
                        ["③ 다음 단계", "고객이 할 일 또는 우리가 할 일, 시점", "도착하지 않으면 이 메일에 회신해 주세요. 바로 재발송하겠습니다."]],
                       ["k", "", ""], widths=["14%", "34%", "52%"])
                 + note("안전 이슈(발열·연기·불꽃·타는 냄새·배터리 팽창)",
                        "답변 첫 문장에서 <b>즉시 사용을 중지하고 전원 플러그를 뽑도록</b> 안내하고, 연기·불꽃이 계속되면 119에 신고하도록 알린다. "
                        "그다음 안전관리 전담팀이 <b>당일 연락</b>한다고 안내한다. 원인 추정이나 책임 언급은 하지 않는다.", "red")
                 + ul(["고객 이름은 '○○○ 고객님'으로 부르고, 내부 용어(출고 보류, 물류 코드 등)는 쓰지 않는다.",
                       "주문번호가 없으면 확인을 위해 주문번호(예: CY261012-1234)를 정중히 요청한다.",
                       "답변 길이는 5문장 이내, 마지막에 상담 채널(고객센터 00-0000-0000, 가상)을 안내한다."]), "br6"))

    return B


def doc_html(title: str, header: str, right: str, blocks: list[str]) -> str:
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>{e(title)} — {e(DISCLAIMER)}</title>
<style>{BASE_CSS}{DOC_CSS}</style></head>
<body>
{page_template("Cymbal", header, right)}
<div id="flow">{"".join(blocks)}</div>
</body></html>"""


def build() -> dict:
    rep = {}
    rep["brief"] = render_document(doc_html("Cymbal 신제품 브리프 — AirPole Pro (가상)", f"신제품 브리프 · {PRODUCT}", "CYM-MKT-BRF-2611",
                                            brief_blocks()), out_path("brief"), preview_path(FILES["brief"]))
    rep["brand"] = render_document(doc_html("Cymbal 브랜드 가이드 (가상)", "브랜드 가이드", "CYM-BRD-GDE-01 · Rev. 2.0",
                                            brand_blocks()), out_path("brand"), preview_path(FILES["brand"]))
    return rep


if __name__ == "__main__":
    import json
    r = build()
    for k, v in r.items():
        print(k, v["paginate"]["pages"], v["paginate"]["log"], [o["fill"] for o in v["overflow"]])
