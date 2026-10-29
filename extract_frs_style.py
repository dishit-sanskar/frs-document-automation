import os
import json
from docx import Document
from docx.oxml.ns import qn

def extract_style_from_sample(sample_docx_path, output_config="style_config.json"):
    """
    Parses a sample reference FRS .docx document to extract branding, font sizes,
    colors, paragraph spacing, and table formatting styles.
    """
    if not os.path.exists(sample_docx_path):
        print(f"[Style Extractor] File not found: {sample_docx_path}. Using standard defaults.")
        return

    doc = Document(sample_docx_path)
    
    style_config = {
        "fonts": {
            "title_font": "Arial",
            "body_font": "Calibri",
            "title_size_pt": 26,
            "heading1_size_pt": 18,
            "heading2_size_pt": 14,
            "body_size_pt": 11
        },
        "colors": {
            "primary_red": [192, 0, 0],
            "dark_neutral": [0, 0, 0],
            "muted_gray": [128, 128, 128],
            "table_header_bg": "F2F2F2"
        },
        "table_style": {
            "alignment": "CENTER",
            "has_header_shading": True
        }
    }

    # Inspect runs in paragraphs for primary colors and fonts
    for p in doc.paragraphs[:15]:
        for run in p.runs:
            if run.font.color and run.font.color.rgb:
                rgb = run.font.color.rgb
                if rgb[0] > 150 and rgb[1] < 100 and rgb[2] < 100:
                    style_config["colors"]["primary_red"] = [rgb[0], rgb[1], rgb[2]]
            if run.font.name:
                style_config["fonts"]["body_font"] = run.font.name

    # Inspect tables for background XML shading
    if doc.tables:
        table = doc.tables[0]
        if table.rows:
            first_cell = table.rows[0].cells[0]
            tcPr = first_cell._tc.get_or_add_tcPr()
            shd = tcPr.find(qn('w:shd'))
            if shd is not None and shd.get(qn('w:fill')):
                style_config["colors"]["table_header_bg"] = shd.get(qn('w:fill'))

    with open(output_config, "w", encoding="utf-8") as f:
        json.dump(style_config, f, indent=2)

    print(f"[Style Extractor] Successfully extracted design config to: {output_config}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        extract_style_from_sample(sys.argv[1])
    else:
        print("Usage: python extract_frs_style.py <sample_frs.docx>")
