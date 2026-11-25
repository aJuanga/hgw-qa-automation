"""Interfaz web para lanzar las pruebas (HGW QA Runner).

Ejecutar:  python -m web.app   y abrir http://localhost:5000
Este sistema LANZA las pruebas; la aplicación probada es el Sistema HGW (otra URL).
"""
import json
import os
import threading
from datetime import datetime

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for

from core.config import config
from core.runner import TIPOS, execute, ids_por_tipo, list_suites

app = Flask(__name__)
STATE = {"running": False, "run_id": None, "log": [], "result": None}
LOCK = threading.Lock()


def _history():
    runs = []
    for d in sorted(config.reports_dir.glob("RUN_*"), reverse=True):
        f = d / "results.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            runs.append({"run_id": data["run_id"], "date": data["date"], "summary": data["summary"],
                         "suites": data["suites"], "mail": data.get("mail", "-"),
                         "html": f"reporte_{data['run_id']}.html", "docx": f"informe_{data['run_id']}.docx"})
    return runs[:20]


def _worker(suites, ids, mail_to, use_ai, headless, run_id):
    def log(msg):
        STATE["log"].append(f"{datetime.now():%H:%M:%S}  {msg}")
    try:
        config.headless = headless
        from core import live
        live.start()
        STATE["result"] = execute(suites=suites, ids=ids, mail_to=mail_to, use_ai=use_ai, log=log, run_name=run_id)
    except Exception as exc:
        log(f"ERROR: {exc}")
    finally:
        STATE["running"] = False
        from core import live
        live.stop()


@app.route("/ia", methods=["GET", "POST"])
def ia():
    from ai.gherkin import EJEMPLO, generar, gherkin_proyecto
    texto = request.form.get("tc", EJEMPLO)
    res = generar(texto) if request.method == "POST" else None
    return render_template("ia.html", texto=texto, res=res, proyecto=gherkin_proyecto())


@app.route("/")
def index():
    return render_template("index.html", tipos=TIPOS, suites=list_suites(), history=_history(), state=STATE,
                           base_url=config.base_url, default_mail=os.getenv("MAIL_TO", ""),
                           ai_ready=bool(os.getenv("ANTHROPIC_API_KEY")), headless=config.headless)


@app.post("/run")
def run():
    with LOCK:
        if STATE["running"]:
            return redirect(url_for("index"))
        suites = request.form.getlist("suite")
        ids = request.form.getlist("case")
        tipos = request.form.getlist("tipo")
        if tipos:
            ids = list(dict.fromkeys(ids + ids_por_tipo(tipos)))
        if not suites and not ids:
            return redirect(url_for("index"))
        run_id = datetime.now().strftime("RUN_%Y%m%d_%H%M%S")
        STATE.update(running=True, run_id=run_id, log=[], result=None)
        mail_to = request.form.get("mail", "").strip() or None
        use_ai = request.form.get("ai") == "on"
        headless = request.form.get("headless") == "on"
        threading.Thread(target=_worker, args=(suites or None, ids or None, mail_to, use_ai, headless, run_id),
                         daemon=True).start()
    return redirect(url_for("index") + "#estado")


@app.get("/live")
def live_view():
    from core.live import LIVE
    return jsonify(frame=LIVE["frame"], case=LIVE["case"], steps=LIVE["steps"][-14:], running=STATE["running"])


@app.get("/status")
def status():
    res = STATE["result"]
    return jsonify(running=STATE["running"], run_id=STATE["run_id"], log=STATE["log"][-200:],
                   summary=res["summary"] if res else None)


@app.get("/reports/<run_id>/<path:name>")
def report_file(run_id, name):
    folder = config.reports_dir / run_id
    if not folder.is_dir() or not run_id.startswith("RUN_"):
        abort(404)
    return send_from_directory(folder, name, as_attachment=name.endswith(".docx"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("QA_PORT", "5000")), debug=False)
