# production/samples/v2 — Cymbal(심벌) 실습 파일 생성기 (범용 v2)

> ※ 실습용 가상 데이터 — Cymbal(심벌)은 가상의 회사이며 실제 기업·인물과 무관

모든 고객사 대상 핸즈온 v2의 **가상 실습 파일**을 만드는 스크립트 모음입니다. v1(`production/samples/*.py`, 이 저장소에는 없음)의
파이프라인(HTML/CSS → Playwright PDF, xlsxwriter, 스킬 ZIP, 미리보기, 번들, verify)을 복사해 고쳤습니다. v1 파일은 건드리지 않았습니다.
완성 파일은 `build/`에, 강사용 정답은 `answer_keys/`에 생성됩니다. 수치·스토리 요약은 [DATA_NOTES.md](DATA_NOTES.md)(자동 생성)를 보세요.

## 한 번에 다시 만들기

```bash
cd production/samples/v2
python3 build_all.py      # 생성 → 미리보기 → 번들/manifest → 정답·DATA_NOTES → verify.py
python3 verify.py         # 검증만 다시 실행 (실패 시 exit 1). 모든 PDF 쪽을 sips로 렌더링해 work/contact_*.png 생성
```

필요 패키지(이미 설치된 것만 사용, 추가 설치 없음): `xlsxwriter`, `playwright`(Chromium), `pypdf`, `Pillow`, `PyYAML`. macOS `sips`(PDF 렌더 검증).

## 출력물 (`build/`)

| 파일 | 생성 스크립트 | 실습 | 내용 |
|---|---|---|---|
| `Cymbal_제품별_지역별_월별매출_2026_가상.xlsx` | `build_xlsx.py` + `data_sales.py` | Lab 3 | `매출데이터` 225행(1~9월 × 5제품 × 5지역), `목표` 45행 |
| `Cymbal_고객문의_로그_2026-10_가상.xlsx` | `build_xlsx.py` + `data_inquiries.py` | Lab 8 | 문의 60건, **분류·긴급도 컬럼 없음** |
| `Cymbal_출장비_및_경비처리_규정_가상.pdf` (7쪽) | `build_travel_pdf.py` + `calendar_kr.py` | Lab 7 | CYM-FIN-POL-012, 시행 2026-07-01 |
| `Cymbal_휴가_및_근무제도_규정_가상.pdf` (6쪽) | `build_leave_pdf.py` | Lab 7 | CYM-HR-POL-003 |
| `Cymbal_IT보안_및_계정관리_가이드_가상.pdf` (6쪽) | `build_it_pdf.py` | Lab 7 | CYM-IT-GDE-005 |
| `Cymbal_신제품_브리프_에어폴_프로_가상.pdf` (3쪽) | `build_marketing_pdfs.py` | Lab 4 | AirPole Pro 런칭 브리프 |
| `Cymbal_브랜드_가이드_가상.pdf` (2쪽) | `build_marketing_pdfs.py` | Lab 4·6·8 | 컬러·톤·금지 표현·고객 응대 |
| `Cymbal_보고서스타일_스킬.zip`, `skills/cymbal-report-style/SKILL.md` | `build_skill.py` | Lab 6 | GE 스킬 업로드용 |
| `previews/*.png` (폭 1200px) | PDF: 각 `build_*_pdf.py`, 나머지: `build_previews.py` | 포털 | 표지 썸네일 |
| `Cymbal_실습파일_전체.zip`, `manifest.json` | `build_bundle.py` | 포털 | 학습자용 9개 파일 + README (정답 제외) |

강사용(배포 금지): `answer_keys/inquiries_answer_key.json`(분류·urgent·needs_info), `answer_keys/policies_qa.md`(테스트 질문 12개).

## 핵심 팩트 (자세한 값은 DATA_NOTES.md)

- **매출 스토리**: 로봇청소기 급성장(9월 = 1월의 2.55배, 3분기 목표 대비 137.6%, 9월 1위) · 홈카메라 3분기 급락(전분기 대비 −33.4%, 달성률 58.6%) ·
  온라인 비중 22.0% → 38.8% · 공기청정기 3~4월 성수기 · 스마트 스피커 5월 가격 인하 후 마진 하락 · 스마트 조명 마진 최고(45.1%)
- **고객 문의**: 6개 분류(배송지연 11, 불량/고장 12, 환불/교환 11, 사용법 11, 안전 이슈 7, 개인정보/계정 8). 긴급 = 안전 이슈 7건만.
  주문번호가 빠진 배송·환불 문의 5건은 '정보 요청' 분기용. "급합니다!!" 함정 1건(긴급 아님).
- **규정 날짜 계산**(2026년 공휴일 반영, `calendar_kr.py`에서 assert): 10/23(금) 귀국 → 정산 마감 **11/3(화)**, 9/22(화) 귀국 → **10/6(화)**,
  10/23 귀국 미정산 → 법인카드 정지 **11/16(월)**부터. PDF에는 다른 날짜(11/13 → 11/24, 10/1 → 10/14)를 예시로 넣어 테스트 문항은 직접 계산해야 함.
- **신제품**: Cymbal AirPole Pro(에어폴 프로) — 2026-12-01(화) 출시, 699,000원(사전 예약 629,100원), 카피 “공기는 맑게, 공간은 넓게”.

## 구현 메모

- **엑셀**: `xlsxwriter`(openpyxl 미설치·불필요). 1행 제목 + "실습용 가상 데이터", 2행 Cymbal Blue(#4285F4) 헤더, 3행부터 tidy 데이터.
  수식 없이 정적 값, 틀 고정·자동 필터·천 단위 서식. 폰트는 맑은 고딕(엑셀 표준).
- **PDF**: v1과 같은 자체 paginator(`common.py`)로 A4 페이지에 블록을 흘려 넣음. 조항은 `제N장/제N조/①` 체계, 문서번호·개정 이력·목차 표지.
  - 본문 폰트는 **NanumGothic**. 저장소의 Pretendard는 *가변 폰트 subset(woff2)*뿐인데, Chromium(Skia)은 가변 폰트를 **Type3**로 내보내
    텍스트 레이어가 음절마다 띄어져 추출됨(RAG 품질 저하) — `work/`에서 실험으로 확인. 그래서 PDF는 NanumGothic(Type0, 임베드), **미리보기 PNG는 Pretendard**.
  - `verify.py`가 모든 폰트가 Type0 + NanumGothic뿐인지(대체 글꼴로 빠진 글리프 없음) 검사. `−`, `⊞`, `₂` 같은 글리프는 대체 글꼴을 부르므로 쓰지 않음.
- **렌더 검증**: `pdftoppm`은 엔드포인트 정책으로 차단, Swift/PDFKit은 CLT 모듈 오류 → `tools/pdf_pages.py`(pypdf로 쪽 분리 + macOS `sips`)로 실제 PDF를 PNG로 렌더.
- **스킬**: GE 규칙 — `---` 프론트매터(BOM 없음), `name`=폴더명 `cymbal-report-style`, `description` < 1,024바이트, ZIP 안 SKILL.md 1개. 예시 수치는 `data_sales.facts()`에서 주입.
- **데이터 결정성**: `random.Random` 고정 시드(매출 2026, 문의 1026). 정답·DATA_NOTES·스킬 예시는 모두 같은 상수에서 생성되어 서로 어긋나지 않음.

## 보안·안전 메모

- 렌더링은 별도로 띄운 headless Chromium에서만 수행(공유 Chrome :9222 미사용), `file:`/`data:` 외 네트워크 요청 차단. 외부 CDN·원격 폰트 없음.
- 생성 HTML의 데이터 텍스트는 `html.escape` 처리(작성자 마크업만 raw). 검증 XML 파싱은 자체 생성 xlsx에 한해 표준 라이브러리 사용.
- 연락처는 `example.com`·`0000` 가상 값. 실제 회사명은 `verify.py`의 금지어 목록으로 검사(경쟁사는 '경쟁사 A/B'로만 표기).
- 공휴일: 2026년 관공서 공휴일(대체공휴일 포함) 기준. 제헌절(7/17) 공휴일 재지정 여부 등 변동 가능성이 있는 7월은 계산 예시에서 제외했고,
  PDF 부록 A에는 8~12월만 실었습니다.
