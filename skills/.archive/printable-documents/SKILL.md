---
name: printable-documents
description: "Generate A4 formatted PDF documents from content — reference sheets, cheat sheets, reports, and learning materials with CJK (Chinese/Japanese/Korean) font support. Uses fpdf2 in the Hermes venv + Noto Sans CJK system fonts. Covers document structure (tables, sections, headers, code blocks) and delivery via MEDIA attachment."
category: productivity
tags: [pdf, document, printable, cheatsheet, reference, cjk, fpdf2]
---

# Printable Documents

Generate A4 formatted PDF documents from scratch. Typical use cases: reference sheets, cheat sheets, study materials, strategy summaries, any printable Chinese-English content.

## Prerequisites

- **fpdf2** must be installed in the Hermes venv:
  ```bash
  /home/wei/.local/share/pipx/venvs/hermes-agent/bin/python3 -m pip install fpdf2
  ```
- **Noto Sans CJK fonts** (usually pre-installed on Ubuntu at `/usr/share/fonts/opentype/noto/NotoSansCJK-{Regular,Bold}.ttc`)
- If the system is NOT Ubuntu with Noto fonts pre-installed:
  ```bash
  sudo apt install -y fonts-noto-cjk
  ```

## Workflow

### 1. Create the PDF generation script

Write a Python script that:
- Subclasses `FPDF` with CJK font registration
- Uses `section_title()`, `subsection_title()`, `draw_table()`, `body_text()`, `code_text()` helpers
- Builds all content before calling `pdf.output()`
- Run via the Hermes venv Python:
  ```bash
  /home/wei/.local/share/pipx/venvs/hermes-agent/bin/python3 /path/to/generate.py
  ```

### 2. Font setup

```python
self.add_font('NotoSC', '', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
self.add_font('NotoSC', 'B', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
```

Note: path is `opentype/noto/` on modern Ubuntu, NOT `truetype/noto/`.

### 3. A4 page defaults

```python
FPDF('P', 'mm', 'A4')  # Portrait, millimeters, A4
set_auto_page_break(auto=True, margin=18)
```

### 4. Useful helper methods (from the advanced script)

```python
def sub(self, title):
    """Subsection title: smaller bold, dark grey."""
    self.set_font('D', 'B', 9)
    self.set_text_color(60, 60, 60)
    self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
    self.ln(1)

def tip(self, label, text):
    """Labeled example block: blue ▶ heading + body text.
    Good for real-world examples with translations, case studies, etc."""
    self.set_font('D', 'B', 7.5)
    self.set_text_color(0, 82, 136)
    self.cell(0, 4.5, '▶ ' + label, new_x="LMARGIN", new_y="NEXT")
    self.set_font('D', '', 7.5)
    self.set_text_color(70, 70, 70)
    self.multi_cell(0, 4.5, text)
    self.ln(1)
```

The `draw_table()` in the advanced script also uses alternating row colors and re-draws the header when a table overflows to a new page — both recommended for any reference sheet with more than 10 rows.

### 5. Send to user

Include in the response:
```
MEDIA:/path/to/output.pdf
```

## Reference files

- `references/meme-english-vocabulary.md` — general internet meme vocabulary (abbreviations, slang, templates)
- `references/solana-degen-vocabulary.md` — crypto Twitter / Solana meme coin narrative vocabulary (core actions, risk signals, narrative types, on-chain metrics, real translation examples)

## Referenced scripts

`scripts/generate-meme-cheatsheet.py` — basic A4 reference sheet demonstrating:
- CJK title and metadata
- Multi-column tables with headers
- Code block display
- Section numbering
- Header/footer with page numbers
- `draw_table()` with page-break detection and header re-draw on overflow

`scripts/generate-degen-cheatsheet.py` — advanced A4 reference sheet demonstrating:
- `sub()` method for subsection titles (smaller bold, dark grey)
- `tip()` method for labeled example blocks (blue ▶ heading + body text) — good for real-world examples with translations
- Complex multi-section layouts with 6-7 sections
- Very long tables with alternating row colors
- Full-width code/body blocks interleaved with tables

Copy these scripts as starting points for new documents.

## Pitfalls

- **Font path varies by OS**: `opentype/noto/` on Ubuntu 24+, `truetype/noto/` on older. Check with `find /usr/share/fonts -name "NotoSansCJK*"`.
- **Run with the right Python**: The Hermes venv Python, not system Python. Using `python3` directly will fail if fpdf2 was installed via `--break-system-packages` to the system (it won't be importable).
- **Deprecation warnings**: The `uni=True` parameter in `add_font()` is deprecated since fpdf2 v2.5.1. Safe to include for now but will need removal in future versions.
- **Table page breaks**: `draw_table()` needs to check remaining vertical space before rendering each row. See the referenced script for the pattern.
- **Content width**: A4 is 210mm wide minus margins (default 10mm each side) = 190mm usable.
- **Line height**: CJK characters need ~4.5mm line height minimum at 8pt font to avoid overlap.
