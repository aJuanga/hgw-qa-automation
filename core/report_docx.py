"""Genera el informe de ejecución en Word (.docx) con evidencias."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from core.images import compact_jpeg

COLORS = {"PASS": "1F8A4C", "FAIL": "C0392B", "BLOCKED": "B9770E", "NOT RUN": "7F8C8D"}


def _shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _shade(c, "14532D")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            if v in COLORS:
                _shade(cells[i], COLORS[v])
                cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                cells[i].paragraphs[0].runs[0].bold = True
    for row in t.rows:
        for i, c in enumerate(row.cells):
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
            if widths:
                c.width = Cm(widths[i])
    return t


def build(run, run_dir: Path):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2)

    h = doc.add_heading("Informe de ejecución de pruebas automatizadas", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f"{run['environment']['app']} · Corrida {run['run_id']} · {run['date']}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    s = run["summary"]
    doc.add_heading("1. Resumen", 1)
    _table(doc, ["Total", "PASS", "FAIL", "BLOCKED", "Tasa de aprobación", "Duración"],
           [[s["total"], s["PASS"], s["FAIL"], s["BLOCKED"], f"{s['pass_rate']} %", f"{run['duration']} s"]])

    e = run["environment"]
    doc.add_heading("2. Ambiente", 1)
    _table(doc, ["Elemento", "Valor"], [
        ["URL evaluada", e["base_url"]], ["Sistema / versión", f"{e['app']} {e['app_version']}"],
        ["Navegador", f"{e['browser']} (headless={e['headless']})"], ["Sistema operativo", e["os"]],
        ["Python / Selenium", f"{e['python']} / {e['selenium']}"], ["Suites", ", ".join(run["suites"])]],
        widths=[5, 12])

    doc.add_heading("3. Resultados por caso", 1)
    _table(doc, ["ID", "Caso de prueba", "Requisito", "Estado", "Duración"],
           [[r["id"], r["title"], r["requirement"], r["status"], f"{r['duration']} s"] for r in run["results"]],
           widths=[1.8, 9, 2.6, 2, 1.8])

    doc.add_heading("4. Análisis de resultados", 1)
    src = f"IA ({run['analysis'].get('model')})" if run["analysis"]["source"] == "ia" else "analizador por reglas"
    doc.add_paragraph(f"Fuente del análisis: {src}.").runs[0].italic = True
    for line in run["analysis"]["text"].splitlines():
        if line.strip():
            doc.add_paragraph(line.strip())

    doc.add_heading("5. Detalle y evidencias", 1)
    for r in run["results"]:
        doc.add_heading(f"{r['id']} – {r['title']} [{r['status']}]", 2)
        doc.add_paragraph(f"Resultado esperado: {r['expected']}")
        if r["error"]:
            doc.add_paragraph(f"Motivo: {r['error']}")
        for c in r["checks"]:
            mark = "✔" if c["passed"] else "✘"
            doc.add_paragraph(f"{mark} {c['description']}" + (f" — {c['detail']}" if c["detail"] else ""),
                              style="List Bullet")
        for k, v in r["metrics"].items():
            doc.add_paragraph(f"{k}: {v}", style="List Bullet 2")
        for sh in r["screenshots"]:
            doc.add_picture(compact_jpeg(sh["path"]), width=Cm(15))
            cap = doc.add_paragraph(f"Evidencia {Path(sh['path']).stem}: {sh['label']}")
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.size = Pt(9)
            cap.runs[0].italic = True

    path = run_dir / f"informe_{run['run_id']}.docx"
    doc.save(path)
    return path
