#!/usr/bin/env python3
"""Generate A4 PDF Solana degen narrative English cheatsheet with CJK font support.
Demonstrates advanced patterns: tip() blocks, sub() sections, alternating table rows, 
multiple interleaved formats. Copy as starting point for complex multi-section references."""

from fpdf import FPDF

class DegenPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font('D', '', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
        self.add_font('D', 'B', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

    def footer(self):
        self.set_y(-15)
        self.set_font('D', '', 7)
        self.cell(0, 10, str(self.page_no()), align='C')

    def sec(self, title):
        """Section title: larger bold, blue, with underline."""
        self.set_font('D', 'B', 12)
        self.set_text_color(0, 82, 136)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 82, 136)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(2)

    def sub(self, title):
        """Subsection title: smaller bold, dark grey."""
        self.set_font('D', 'B', 9)
        self.set_text_color(60, 60, 60)
        self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def table(self, headers, data, widths):
        """Table with header, alternating rows, page-break safety, header re-draw on overflow."""
        # Header
        self.set_font('D', 'B', 7)
        self.set_fill_color(0, 82, 136)
        self.set_text_color(255, 255, 255)
        x0 = self.get_x()
        y0 = self.get_y()
        if y0 + 6 > 297 - 18:
            self.add_page()
            y0 = self.get_y()
        for i, (h, w) in enumerate(zip(headers, widths)):
            self.set_xy(x0 + sum(widths[:i]), y0)
            self.cell(w, 6, h, border=0, fill=True, align='L')
        self.set_xy(x0, y0 + 6)
        self.set_draw_color(200, 200, 200)

        # Rows
        for row_idx, row in enumerate(data):
            self.set_font('D', '', 7)
            self.set_text_color(30, 30, 30)
            if row_idx % 2 == 0:
                self.set_fill_color(245, 248, 255)
            else:
                self.set_fill_color(255, 255, 255)
            y0 = self.get_y()
            if y0 + 5.5 > 297 - 18:
                self.add_page()
                y0 = self.get_y()
                # Redraw header on new page
                self.set_font('D', 'B', 7)
                self.set_fill_color(0, 82, 136)
                self.set_text_color(255, 255, 255)
                for i, (h, w) in enumerate(zip(headers, widths)):
                    self.set_xy(x0 + sum(widths[:i]), y0)
                    self.cell(w, 6, h, border=0, fill=True, align='L')
                y0 = self.get_y() + 6
                self.set_font('D', '', 7)
                self.set_text_color(30, 30, 30)

            for i, (cell, w) in enumerate(zip(row, widths)):
                self.set_xy(x0 + sum(widths[:i]), y0)
                if i == 0:
                    self.set_font('D', 'B', 7)
                else:
                    self.set_font('D', '', 7)
                display = cell[:50] if len(cell) > 50 else cell
                self.cell(w, 5.5, display, border=0, fill=True, align='L')
            self.line(x0, y0 + 5.5, x0 + sum(widths), y0 + 5.5)
            self.set_xy(x0, y0 + 5.5)
        self.ln(3)

    def tip(self, label, text):
        """Labeled example block: blue ▶ heading + body text."""
        self.set_font('D', 'B', 7.5)
        self.set_text_color(0, 82, 136)
        self.cell(0, 4.5, '▶ ' + label, new_x="LMARGIN", new_y="NEXT")
        self.set_font('D', '', 7.5)
        self.set_text_color(70, 70, 70)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def body(self, text):
        self.set_font('D', '', 7.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, text)
        self.ln(1)
