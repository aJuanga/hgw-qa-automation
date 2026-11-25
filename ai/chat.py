"""Asistente QA conversacional: entiende órdenes en español y opera el runner."""
import re
import unicodedata

from core.framework import load_all_tests
from core.runner import TIPOS, ids_por_tipo

ALIAS = [("smoke", "Smoke"), ("regresion", "Regresión"), ("negativ", "Negativas (valores inválidos)"),
         ("funcional", "Funcional (caja negra)"), ("segur", "Seguridad (roles y acceso)"),
         ("rendimiento", "No funcional (rendimiento)"), ("no funcional", "No funcional (rendimiento)"),
         ("auditor", "IA, agentes y MCP"), ("agente", "IA, agentes y MCP"), ("mcp", "IA, agentes y MCP"),
         (" ia", "IA, agentes y MCP")]


def _n(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def responder(msg, ultimo=None):
    t = " " + _n(msg) + " "
    correo = re.search(r"[\w.\-+]+@[\w\-]+\.[\w.]+", msg)
    ids = [i.upper() for i in re.findall(r"tc-?\d{3}", t)]
    ids = [i if "-" in i else i[:2] + "-" + i[2:] for i in ids]
    quiere_correr = any(v in t for v in ("corre", "ejecut", "lanza", "prueba", "testea", "valida", "play", "inicia"))

    if "gherkin" in t and ids:
        from ai.gherkin import gherkin_proyecto
        bloques = [b for b in gherkin_proyecto() for i in ids if f"@{i} " in b]
        if bloques:
            lineas = []
            for b in bloques:
                ini = b.index(f"@{ids[0]} ")
                lineas.append(b[ini:].split("\n\n")[0])
            return {"texto": "Este es el escenario Gherkin:\n\n" + "\n\n".join(lineas)}
    if quiere_correr and ids:
        validos = {c.id for c in load_all_tests()}
        ids = [i for i in ids if i in validos]
        if ids:
            return {"texto": f"Listo, ejecuto {', '.join(ids)} contra el HGW. Míralo EN VIVO en el panel de estado.",
                    "run": {"ids": ids, "mail": correo.group(0) if correo else None}}
    if quiere_correr:
        for clave, tipo in ALIAS:
            if clave in t:
                casos = ids_por_tipo([tipo])
                return {"texto": f"Ejecutando pruebas de tipo «{tipo}» ({len(casos)} casos: {', '.join(casos)})."
                                 + (f" Al terminar envío el reporte a {correo.group(0)}." if correo else "")
                                 + " Míralo EN VIVO en el panel de estado.",
                        "run": {"ids": casos, "mail": correo.group(0) if correo else None, "tipo": tipo}}
    if any(p in t for p in ("fallo", "resultado", "resumen", "como salio", "como fue", "estado")):
        if not ultimo:
            return {"texto": "Todavía no hay ejecuciones. Pídeme por ejemplo: «corre las pruebas smoke»."}
        s = ultimo["summary"]
        malos = [f"• {r['id']} {r['title']}: {r['error'][:120]}" for r in ultimo["results"] if r["status"] != "PASS"]
        return {"texto": f"Última corrida {ultimo['run_id']}: {s['PASS']}/{s['total']} PASS ({s['pass_rate']}%)."
                         + ("\nFallaron:\n" + "\n".join(malos) if malos else "\nTodo pasó correctamente ✔")}
    if any(p in t for p in ("casos", "lista", "que pruebas", "tipos", "cuantos")):
        lineas = [f"• {k}: {len(ids_por_tipo([k]))} casos" for k in TIPOS]
        return {"texto": f"Tengo {len(load_all_tests())} test cases automatizados del HGW:\n" + "\n".join(lineas)}
    return {"texto": "Soy el asistente QA de HGW Sentinel. Puedo:\n"
                     "• «corre las pruebas smoke» / «ejecuta seguridad» / «prueba el auditor y el MCP»\n"
                     "• «ejecuta TC-001 y manda el reporte a correo@gmail.com»\n"
                     "• «muéstrame el gherkin del TC-010»\n"
                     "• «¿qué falló?» o «lista de casos»"}
