#!/usr/bin/env python3
"""Generate A4 PDF meme English cheatsheet with CJK font support.
Copy this script as a starting point for new printable reference sheets."""

from fpdf import FPDF

class MemePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font('NotoSC', '', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
        self.add_font('NotoSC', 'B', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

    def footer(self):
        self.set_y(-15)
        self.set_font('NotoSC', '', 7)
        self.cell(0, 10, f'{self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('NotoSC', 'B', 13)
        self.set_text_color(25, 25, 112)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(25, 25, 112)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(3)

    def body_text(self, text):
        self.set_font('NotoSC', '', 8)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def code_text(self, text):
        self.set_font('NotoSC', '', 8)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(245, 245, 245)
        self.multi_cell(0, 4.5, text, fill=True)
        self.ln(1)

    def draw_table(self, headers, data, col_widths):
        """Draw table with header row + data rows. Checks page breaks per row."""
        # Header
        self.set_font('NotoSC', 'B', 7.5)
        self.set_fill_color(220, 220, 240)
        x_start = self.get_x()
        y_start = self.get_y()

        if y_start + 5 > 297 - 18:
            self.add_page()
            y_start = self.get_y()

        for i, (h, w) in enumerate(zip(headers, col_widths)):
            self.set_xy(x_start + sum(col_widths[:i]), y_start)
            self.cell(w, 5, h, border=0, fill=True)
        self.set_draw_color(200, 200, 200)
        self.line(x_start, y_start + 5, x_start + sum(col_widths), y_start + 5)

        # Data rows
        for row in data:
            y_start = y_start + 5
            if y_start + 5 > 297 - 18:
                self.add_page()
                y_start = self.get_y()
                # Redraw header on new page
                self.set_font('NotoSC', 'B', 7.5)
                self.set_fill_color(220, 220, 240)
                for i, (h, w) in enumerate(zip(headers, col_widths)):
                    self.set_xy(x_start + sum(col_widths[:i]), y_start)
                    self.cell(w, 5, h, border=0, fill=True)
                self.line(x_start, y_start + 5, x_start + sum(col_widths), y_start + 5)
                y_start = y_start + 5

            self.set_font('NotoSC', '', 7.5)
            self.set_fill_color(255, 255, 255)
            for i, (cell_text, w) in enumerate(zip(row, col_widths)):
                display = cell_text if len(cell_text) < 80 else cell_text[:77] + '...'
                self.set_xy(x_start + sum(col_widths[:i]), y_start)
                if i == 0:
                    self.set_font('NotoSC', 'B', 7.5)
                else:
                    self.set_font('NotoSC', '', 7.5)
                self.cell(w, 5, display, border=0, fill=True)
            self.line(x_start, y_start + 5, x_start + sum(col_widths), y_start + 5)

        self.set_xy(x_start, y_start + 5)
        self.ln(3)


def build_pdf():
    pdf = MemePDF()
    pdf.add_page()

    # Title
    pdf.set_font('NotoSC', 'B', 18)
    pdf.set_text_color(25, 25, 112)
    pdf.cell(0, 12, 'Meme English \u901f\u67e5\u8868', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('NotoSC', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, '\u96f6\u57fa\u7840\u2192\u770b\u61c2meme\uff0c\u4e00\u5f20\u8868\u591f\u4e86', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # === Section 1: Common Abbreviations ===
    pdf.section_title('1. \u6700\u5e38\u7528\u7f29\u5199')
    pdf.draw_table(
        ['\u7f29\u5199', '\u5168\u5199', '\u610f\u601d'],
        [
            ['idk', "I don't know", '\u6211\u4e0d\u77e5\u9053'],
            ['tbh', 'to be honest', '\u8bf4\u5b9e\u8bdd'],
            ['ngl', "not gonna lie", '\u4e0d\u6492\u8c0e\u8bf4'],
            ['af', 'as fuck', '\u975e\u5e38/\u6781\u5176'],
            ['afk', 'away from keyboard', '\u4eba\u4e0d\u5728'],
            ['fr', 'for real', '\u771f\u7684/\u8ba4\u771f\u7684'],
            ['lmao', 'laughing my ass off', '\u7b11\u6b7b'],
            ['wtf', 'what the fuck', '\u4ec0\u4e48\u9b3c'],
            ['rip', 'rest in peace', '\u5b8c\u4e86/\u6302\u4e86'],
        ],
        [25, 60, 50]
    )

    # === Section 2: High-frequency Slang ===
    pdf.section_title('2. \u9ad8\u9891\u53e3\u8bed\u8bcd')
    pdf.draw_table(
        ['\u8bcd', '\u610f\u601d', '\u4f8b\u53e5'],
        [
            ["ain't", '= am/is/are not', '"I ain\'t doing that"'],
            ['gonna', '= going to', '"You\'re gonna regret this"'],
            ['wanna', '= want to', '"I don\'t wanna know"'],
            ['gotta', '= got to', '"I gotta go"'],
            ['tho', '\u4e0d\u8fc7\uff08\u53e5\u5c3e\uff09', '"That\'s funny tho"'],
            ['cringe', '\u5c34\u5c2c/\u793e\u6b7b', '"This is so cringe"'],
            ['sus', 'suspicious', '\u53ef\u7591/\u9634\u9633\u602a\u6c14'],
            ['based', '\u597d/\u9177/\u771f\u5b9e', '"Based take"'],
            ['salty', '\u6025\u4e86/\u751f\u6c14\u4e86', '"Why so salty?"'],
            ['simp', '\u8214\u72d7', '"Stop simping"'],
            ['cap/no cap', '\u6492\u8c0e/\u6ca1\u6492\u8c0e', '"No cap, that\'s fire"'],
            ['lit', '\u592a\u68d2\u4e86', '"This party is lit"'],
            ['mid', '\u4e00\u822c/\u4e0d\u884c', '"That movie was mid"'],
            ['goated', '\u53f2\u4e0a\u6700\u4f73', '"This song is goated"'],
            ['lowkey', '\u6697\u5730\u91cc/\u6709\u70b9', '"I lowkey agree"'],
            ['normie', '\u4e0d\u61c2\u68d7\u7684\u4eba', '"Normie alert"'],
            ['NPC', '\u6ca1\u4e3b\u89c1\u7684\u4eba', '"You\'re just an NPC"'],
        ],
        [25, 55, 55]
    )

    # === Section 3: Meme Templates ===
    pdf.section_title('3. \u5e38\u7528Meme\u6a21\u677f')
    templates = [
        ('Nobody: / Absolutely nobody:\n   Me: ...', '\u6ca1\u4eba\u8bf4\u8bdd\u65f6\u94fa\u57ab'),
        ("I'm in this photo and I don't like it", '\u88ab\u8bf4\u4e2d\u4e86\u624e\u5fc3'),
        ('This is fine', '\u8868\u9762\u6ca1\u4e8b\u5b9e\u9645\u5df2\u5d29'),
        ('Hol up / Hold up / Say sike right now', '\u7b49\u4e0b\uff1f\u4f60\u5728\u5f00\u73a9\u7b11\uff1f'),
        ('Ratio + L + you fell off', '\u7f51\u7edc\u6252\u67b6\u80dc\u5229\u4e09\u8fde'),
    ]
    for eng, cn in templates:
        pdf.code_text(eng)
        pdf.set_font('NotoSC', '', 7.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, '\u2192 ' + cn, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # === Section 4: Workflow ===
    pdf.section_title('4. \u5feb\u901f\u4e0a\u624b\u6d41\u7a0b')
    workflow = """1. \u770b\u5230\u4e0d\u61c2\u7684\u8bcd \u2192 \u5728\u8fd9\u4e2a\u8868\u91ccCtrl+F\u627e
2. \u4e0d\u5728\u8868\u91cc \u2192 \u641c "X slang meaning" \u6216 "X urban dictionary"
3. \u68d7\u770b\u4e0d\u61c2 \u2192 \u641c "X meme know your meme"
4. \u6bcf\u5929\u5237 r/memes Hot \u524d10\u6761"""
    pdf.body_text(workflow)

    return pdf

if __name__ == '__main__':
    pdf = build_pdf()
    pdf.output('output.pdf')
    print('PDF generated: output.pdf')
