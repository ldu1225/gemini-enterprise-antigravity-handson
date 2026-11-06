"""Build the two fictional Cymbal Excel workbooks with xlsxwriter (adapted from v1 build_xlsx.py).

- Cymbal_제품별_지역별_월별매출_2026_가상.xlsx   (Lab 3 — 데이터 분석 + Canvas)
- Cymbal_고객문의_로그_2026-10_가상.xlsx          (Lab 8 — 워크플로 분류·답변 초안)

Tidy tables: row 1 = title + disclaimer, row 2 = header, data from row 3; static values only.
"""
from __future__ import annotations

import datetime as dt

import xlsxwriter

import data_inquiries as Q
import data_sales as S
from common import BLUE, DISCLAIMER, INK, OUT, SUB, out_path

XL_FONT = "Malgun Gothic"
BAND = "#F7F8FA"
GRID = "#E5E7EB"
HDR_BORDER = "#2B63C6"


class Fmt:
    KINDS = {
        "text_c": {"align": "center"},
        "text_l": {"align": "left"},
        "wrap": {"align": "left", "text_wrap": True},
        "int": {"num_format": "#,##0", "align": "right"},
        "dec1": {"num_format": "#,##0.0", "align": "right"},
        "pct1": {"num_format": "0.0", "align": "right"},
        "datetime": {"num_format": "yyyy-mm-dd hh:mm", "align": "center"},
    }

    def __init__(self, wb):
        self.wb = wb
        self.cache = {}
        self.title = wb.add_format({"bold": True, "font_size": 15, "font_color": INK, "font_name": XL_FONT})
        self.disc = wb.add_format({"bold": True, "font_size": 10, "font_color": "#D93025", "font_name": XL_FONT})
        self.title_cell = wb.add_format({"valign": "vcenter", "font_name": XL_FONT})
        self.hdr = wb.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": BLUE, "align": "center", "valign": "vcenter",
            "text_wrap": True, "border": 1, "border_color": HDR_BORDER, "font_name": XL_FONT, "font_size": 10})

    def get(self, kind, banded):
        key = (kind, banded)
        if key not in self.cache:
            props = {"font_name": XL_FONT, "font_size": 10, "valign": "vcenter", "bottom": 1, "bottom_color": GRID}
            props.update(self.KINDS[kind])
            if banded:
                props["bg_color"] = BAND
            self.cache[key] = self.wb.add_format(props)
        return self.cache[key]


def write_table(ws, fmt, title, columns, rows, *, freeze_cols=1, header_height=30, row_height=20):
    ws.set_row(0, 30)
    ws.write_rich_string(0, 0, fmt.title, title, fmt.disc, f"    ※ {DISCLAIMER}", fmt.title_cell)
    ws.set_row(1, header_height)
    for c, (name, kind, width) in enumerate(columns):
        ws.write(1, c, name, fmt.hdr)
        ws.set_column(c, c, width)
    for r, row in enumerate(rows):
        banded = r % 2 == 1
        if row_height:
            ws.set_row(2 + r, row_height)
        for c, (name, kind, _w) in enumerate(columns):
            val = row[name]
            f = fmt.get(kind, banded)
            if isinstance(val, dt.datetime):
                ws.write_datetime(2 + r, c, val, f)
            elif val == "" or val is None:
                ws.write_blank(2 + r, c, None, f)
            else:
                ws.write(2 + r, c, val, f)
    last_row = 1 + len(rows)
    ws.autofilter(1, 0, last_row, len(columns) - 1)
    ws.freeze_panes(2, freeze_cols)
    ws.set_landscape()
    ws.set_paper(9)
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(1)
    ws.set_footer(f"&L&8{DISCLAIMER}&R&8&P / &N")
    return last_row


def props(title: str, subject: str, kw: str) -> dict:
    return {"title": title, "subject": subject, "author": "Cymbal(심벌) 핸즈온 실습 (가상)",
            "company": "Cymbal (가상 회사) · 실습용 가상 데이터", "keywords": kw, "comments": DISCLAIMER}


SALES_SPEC = [("월", "text_c", 10), ("분기", "text_c", 8), ("제품", "text_c", 14), ("지역", "text_c", 10),
              ("판매수량(대)", "int", 13), ("평균판매가(원)", "int", 15), ("매출액(백만원)", "dec1", 15),
              ("매출총이익(백만원)", "dec1", 17), ("매출총이익률(%)", "pct1", 15)]
TARGET_SPEC = [("월", "text_c", 10), ("분기", "text_c", 8), ("제품", "text_c", 14), ("목표수량(대)", "int", 14),
               ("목표매출액(백만원)", "dec1", 18)]
CS_SPEC = [("문의번호", "text_c", 14), ("접수일시", "datetime", 17), ("채널", "text_c", 12), ("고객명(가상)", "text_c", 13),
           ("제품", "text_c", 13), ("주문번호", "text_c", 15), ("문의내용", "wrap", 90)]


def build_sales() -> None:
    path = out_path("sales")
    wb = xlsxwriter.Workbook(str(path), {"default_format_properties": {"font_name": XL_FONT, "font_size": 10}})
    wb.set_properties(props("Cymbal 제품별·지역별 월별 매출 2026 (가상)", "AI 업무 활용 핸즈온 Lab 3 실습용",
                            "실습용, 가상 데이터, 매출, Cymbal"))
    fmt = Fmt(wb)
    ws = wb.add_worksheet("매출데이터")
    ws.set_tab_color(BLUE)
    write_table(ws, fmt, "Cymbal 제품별·지역별 월별 매출 (2026년 1~9월, 단위: 대·원·백만원·%)",
                SALES_SPEC, S.rows(), freeze_cols=4)
    ws2 = wb.add_worksheet("목표")
    write_table(ws2, fmt, "2026년 제품별 월간 판매 목표 (전 지역 합계, 2025년 12월 수립)", TARGET_SPEC, S.target_rows(),
                freeze_cols=3)
    ws.activate()
    wb.close()
    print("wrote", path.name, path.stat().st_size, "bytes")


def build_cs() -> None:
    path = out_path("cs")
    wb = xlsxwriter.Workbook(str(path), {"default_format_properties": {"font_name": XL_FONT, "font_size": 10}})
    wb.set_properties(props("Cymbal 고객 문의 로그 2026-10 (가상)", "AI 업무 활용 핸즈온 Lab 8 실습용",
                            "실습용, 가상 데이터, 고객 문의, CS"))
    fmt = Fmt(wb)
    ws = wb.add_worksheet("문의로그")
    ws.set_tab_color(BLUE)
    rows = Q.public_rows()
    write_table(ws, fmt, f"Cymbal 고객 문의 로그 (2026년 10월 1~25일 접수, {len(rows)}건)", CS_SPEC, rows,
                freeze_cols=1, row_height=34)
    ws.activate()
    wb.close()
    print("wrote", path.name, path.stat().st_size, "bytes")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    build_sales()
    build_cs()
