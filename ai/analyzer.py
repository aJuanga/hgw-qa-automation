"""Análisis de resultados: IA (Claude) si hay ANTHROPIC_API_KEY, si no, reglas locales.

Antes de enviar datos a la IA se anonimizan correos, se eliminan rutas locales y
nunca se envían contraseñas (el runner no las guarda en los resultados).
"""
import json
import os
import re

import core.config  # noqa: F401  (carga las variables del archivo .env)

PROMPT = """Eres un analista QA senior. Analiza los resultados de una corrida de pruebas
automatizadas (Selenium WebDriver, patrón POM) del Sistema HGW, una aplicación web Laravel
para gestionar una cafetería saludable. Responde en español, en texto plano (sin markdown),
con estas secciones:
1. Resumen general (2-3 oraciones).
2. Análisis de cada caso FAIL o BLOCKED: clasifica la causa probable como
   DEFECTO DEL SISTEMA, PROBLEMA DEL SCRIPT, DATOS DE PRUEBA o AMBIENTE, y justifica.
   Sugiere severidad (Crítica/Alta/Media/Baja) para los defectos del sistema.
3. Riesgos de regresión: qué funcionalidades conviene volver a probar.
4. Tres casos de prueba nuevos recomendados (ID sugerido, título, resultado esperado).
No inventes datos que no estén en el JSON.

Resultados (JSON):
{payload}"""


def _anonymize(run):
    slim = {
        "summary": run["summary"],
        "environment": {k: v for k, v in run["environment"].items() if k != "base_url"},
        "results": [{k: r[k] for k in ("id", "title", "suite", "requirement", "status", "error", "expected")}
                    | {"checks": r["checks"], "metrics": r["metrics"]} for r in run["results"]],
    }
    text = json.dumps(slim, ensure_ascii=False)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<correo>", text)
    text = re.sub(r"(/home|/Users|[A-Z]:\\\\)[^\s\"']+", "<ruta>", text)
    return text


def _rules(run):
    lines = []
    s = run["summary"]
    lines.append(f"Resumen general: se ejecutaron {s['total']} casos; {s['PASS']} aprobados, "
                 f"{s['FAIL']} fallidos y {s['BLOCKED']} bloqueados (aprobación {s['pass_rate']}%).")
    problems = [r for r in run["results"] if r["status"] != "PASS"]
    if not problems:
        lines.append("Todos los casos cumplieron el resultado esperado. No se identifican defectos en esta corrida.")
    for r in problems:
        err = r["error"] or ""
        if r["status"] == "BLOCKED":
            cause = "DATOS DE PRUEBA / AMBIENTE: el caso no pudo ejecutarse por una precondición externa."
        elif re.search(r"Timeout|NoSuchElement|StaleElement|WebDriver|Session", err):
            cause = ("PROBLEMA DEL SCRIPT O AMBIENTE: excepción de Selenium; revisar localizadores, "
                     "tiempos de espera o disponibilidad del servidor antes de reportar un defecto.")
        elif re.search(r"SQLSTATE|Exception|500|error del servidor", err + json.dumps(r["checks"], ensure_ascii=False)):
            cause = "DEFECTO DEL SISTEMA (severidad sugerida: Alta): el servidor devolvió un error interno."
        else:
            cause = ("POSIBLE DEFECTO DEL SISTEMA (severidad sugerida: Media): la aplicación respondió, "
                     "pero el resultado no coincide con lo esperado.")
        lines.append(f"{r['id']} ({r['title']}): {cause} Detalle: {err}")
    suites = sorted({r["suite"] for r in problems})
    if suites:
        lines.append("Riesgos de regresión: volver a ejecutar las suites " + ", ".join(suites)
                     + " después de corregir los defectos.")
    return "\n".join(lines)


def analyze(run, use_ai=True):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if use_ai and key:
        try:
            import anthropic
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(model=model, max_tokens=1500,
                                         messages=[{"role": "user", "content": PROMPT.format(payload=_anonymize(run))}])
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            return {"source": "ia", "model": model, "text": text.strip()}
        except Exception as exc:
            fallback = _rules(run)
            return {"source": "reglas", "model": None,
                    "text": f"(No se pudo usar la IA: {type(exc).__name__}. Se aplicó el analizador por reglas.)\n{fallback}"}
    return {"source": "reglas", "model": None, "text": _rules(run)}
