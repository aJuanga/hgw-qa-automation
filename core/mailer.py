"""Envío automático de resultados por correo (SMTP, p. ej. Gmail con contraseña de aplicación)."""
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import core.config  # noqa: F401  (carga las variables del archivo .env)


def _body(run):
    s = run["summary"]
    lines = [f"<h2>Resultados de pruebas automatizadas - {run['environment']['app']}</h2>",
             f"<p>Corrida <b>{run['run_id']}</b> ({run['date']}) contra {run['environment']['base_url']}</p>",
             f"<p>Total: <b>{s['total']}</b> · PASS: <b style='color:#1f8a4c'>{s['PASS']}</b> · "
             f"FAIL: <b style='color:#c0392b'>{s['FAIL']}</b> · BLOCKED: {s['BLOCKED']} · "
             f"Aprobación: {s['pass_rate']}% · Duración: {run['duration']} s</p><ul>"]
    for r in run["results"]:
        color = {"PASS": "#1f8a4c", "FAIL": "#c0392b"}.get(r["status"], "#b9770e")
        lines.append(f"<li><b style='color:{color}'>{r['status']}</b> {r['id']} - {r['title']}"
                     + (f"<br><small>{r['error']}</small>" if r["error"] else "") + "</li>")
    lines.append("</ul><p>Se adjuntan el reporte HTML y el informe Word con las evidencias.</p>")
    return "\n".join(lines)


def send_results(run, to, attachments):
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    s = run["summary"]
    msg = EmailMessage()
    msg["Subject"] = (f"[HGW QA] {run['run_id']}: {s['PASS']}/{s['total']} PASS"
                      + (f" · {s['FAIL']} FAIL" if s["FAIL"] else ""))
    msg["From"] = user or "hgw-qa@localhost"
    msg["To"] = to
    msg.set_content("Resultados de pruebas automatizadas HGW. Ver versión HTML y adjuntos.")
    msg.add_alternative(_body(run), subtype="html")
    for path in attachments:
        path = Path(path)
        ctype, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)

    with smtplib.SMTP(host, port, timeout=30) as server:
        if use_tls:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
