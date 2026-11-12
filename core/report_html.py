"""Genera el reporte HTML autocontenido (capturas embebidas en base64)."""
import base64

from core.images import compact_jpeg
from pathlib import Path

from jinja2 import Template

TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Reporte de pruebas HGW - {{ run.run_id }}</title>
<style>
:root{--ok:#1f8a4c;--ko:#c0392b;--bl:#b9770e;--nr:#7f8c8d;--ink:#1d2a24;--muted:#5d6d64;--line:#e3e8e5;--bg:#f6f8f7}
*{box-sizing:border-box}body{font-family:Segoe UI,Roboto,Arial,sans-serif;margin:0;background:var(--bg);color:var(--ink)}
header{background:#14532d;color:#fff;padding:24px 32px}header h1{margin:0 0 4px;font-size:22px}header p{margin:0;opacity:.85}
main{max-width:1150px;margin:0 auto;padding:24px}
.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:20px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.card b{display:block;font-size:26px}.card span{color:var(--muted);font-size:13px}
.PASS{color:var(--ok)}.FAIL{color:var(--ko)}.BLOCKED{color:var(--bl)}.NOTRUN{color:var(--nr)}
.bar{display:flex;height:12px;border-radius:6px;overflow:hidden;background:var(--line);margin:4px 0 22px}
.bar div{height:100%}
section{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:18px}
h2{font-size:17px;margin:0 0 12px}table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#eef3f0}
.badge{font-weight:700;font-size:12px;padding:2px 8px;border-radius:10px;color:#fff}
.b-PASS{background:var(--ok)}.b-FAIL{background:var(--ko)}.b-BLOCKED{background:var(--bl)}
details{border:1px solid var(--line);border-radius:8px;margin:10px 0;padding:10px 14px}
summary{cursor:pointer;font-weight:600}ul.checks{margin:8px 0;padding-left:18px}
.shots{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}.shots figure{margin:0;width:48%}
.shots img{width:100%;border:1px solid var(--line);border-radius:6px}figcaption{font-size:12px;color:var(--muted)}
.env td:first-child{width:200px;color:var(--muted)}.ai{white-space:pre-wrap;line-height:1.5}
footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
</style></head><body>
<header><h1>Reporte de ejecución de pruebas automatizadas</h1>
<p>{{ run.environment.app }} · Corrida {{ run.run_id }} · {{ run.date }}</p></header>
<main>
<div class="cards">
 <div class="card"><b>{{ s.total }}</b><span>Casos ejecutados</span></div>
 <div class="card"><b class="PASS">{{ s.PASS }}</b><span>PASS</span></div>
 <div class="card"><b class="FAIL">{{ s.FAIL }}</b><span>FAIL</span></div>
 <div class="card"><b class="BLOCKED">{{ s.BLOCKED }}</b><span>BLOCKED</span></div>
 <div class="card"><b>{{ s.pass_rate }}%</b><span>Tasa de aprobación</span></div>
 <div class="card"><b>{{ run.duration }} s</b><span>Duración total</span></div>
</div>
<div class="bar">
 {% if s.total %}<div style="width:{{ 100*s.PASS/s.total }}%;background:var(--ok)"></div>
 <div style="width:{{ 100*s.FAIL/s.total }}%;background:var(--ko)"></div>
 <div style="width:{{ 100*s.BLOCKED/s.total }}%;background:var(--bl)"></div>{% endif %}
</div>
<section><h2>Ambiente de ejecución</h2><table class="env">
{% for k,v in env_rows %}<tr><td>{{ k }}</td><td>{{ v }}</td></tr>{% endfor %}
</table></section>
<section><h2>Resumen por caso</h2><table>
<tr><th>ID</th><th>Caso</th><th>Suite</th><th>Requisito</th><th>Estado</th><th>Duración</th></tr>
{% for r in run.results %}<tr><td>{{ r.id }}</td><td>{{ r.title }}</td><td>{{ r.suite }}</td><td>{{ r.requirement }}</td>
<td><span class="badge b-{{ r.status }}">{{ r.status }}</span></td><td>{{ r.duration }} s</td></tr>{% endfor %}
</table></section>
<section><h2>Análisis de resultados {% if run.analysis.source == 'ia' %}(IA: {{ run.analysis.model }}){% else %}(analizador por reglas){% endif %}</h2>
<div class="ai">{{ run.analysis.text }}</div></section>
<section><h2>Detalle y evidencias</h2>
{% for r in run.results %}
<details {% if r.status != 'PASS' %}open{% endif %}><summary>{{ r.id }} · {{ r.title }} — <span class="{{ r.status }}">{{ r.status }}</span></summary>
<p><b>Resultado esperado:</b> {{ r.expected }}<br><b>Técnica:</b> {{ r.technique }} · <b>Prioridad:</b> {{ r.priority }} · <b>Inicio:</b> {{ r.started_at }}</p>
{% if r.error %}<p class="FAIL"><b>Motivo:</b> {{ r.error }}</p>{% endif %}
<ul class="checks">{% for c in r.checks %}<li class="{{ 'PASS' if c.passed else 'FAIL' }}">{{ '✔' if c.passed else '✘' }} {{ c.description }}{% if c.detail %} — {{ c.detail }}{% endif %}</li>{% endfor %}</ul>
{% if r.metrics %}<p><b>Métricas:</b> {% for k,v in r.metrics.items() %}{{ k }} = {{ v }}{% if not loop.last %} · {% endif %}{% endfor %}</p>{% endif %}
<div class="shots">{% for sh in r.screenshots %}<figure><img src="data:image/jpeg;base64,{{ images[sh.path] }}"><figcaption>{{ sh.label }} ({{ sh.path.split('/')[-1].split('\\')[-1] }})</figcaption></figure>{% endfor %}</div>
</details>{% endfor %}
</section></main>
<footer>Generado por HGW QA Automation · Selenium WebDriver + Python (POM)</footer>
</body></html>""")


def build(run, run_dir: Path):
    images = {}
    for r in run["results"]:
        for sh in r["screenshots"]:
            images[sh["path"]] = base64.b64encode(compact_jpeg(sh["path"]).read()).decode()
    e = run["environment"]
    env_rows = [("URL evaluada", e["base_url"]), ("Sistema / versión", f"{e['app']} {e['app_version']}"),
                ("Navegador", f"{e['browser']} (headless={e['headless']})"), ("Sistema operativo", e["os"]),
                ("Python / Selenium", f"{e['python']} / {e['selenium']}"), ("Suites", ", ".join(run["suites"]))]
    html = TEMPLATE.render(run=run, s=run["summary"], images=images, env_rows=env_rows)
    path = run_dir / f"reporte_{run['run_id']}.html"
    path.write_text(html, encoding="utf-8")
    return path
