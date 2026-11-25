"""Suite IA, AGENTES Y MCP - Auditor de procesos, agentes proactivos, reseñas con IA,
recomendaciones por valoraciones y seguridad del servidor MCP."""
import json
import urllib.error
import urllib.request

from core.config import config
from core.framework import test_case
from tests.test_seguridad import _login


def _modulo(ctx, ruta, palabras, captura):
    page = _login(ctx, "jefa")
    page.open(ruta)
    page.wait_for_page()
    texto = page.body_text().lower()
    ctx.check(not page.server_error(), f"{ruta} carga sin error 500", texto[:120])
    ctx.check("/login" not in page.url, "La sesión de la Jefa tiene acceso al módulo", f"URL: {page.url}")
    ctx.check(any(p in texto for p in palabras), f"El módulo muestra su contenido ({' / '.join(palabras)})",
              texto[:160])
    ctx.screenshot(captura)
    return page


@test_case("TC-020", "Agente Auditor de procesos: panel de hallazgos", "ia_agentes", "Aporte 1 - Auditor",
           technique="Caja negra - caso de uso", expected="El panel del Auditor carga con sus hallazgos y controles")
def tc_auditor(ctx):
    _modulo(ctx, "/jefa/auditor", ["auditor", "hallazgo", "auditoría"], "auditor_procesos")


@test_case("TC-021", "Agentes proactivos: actividad registrada", "ia_agentes", "Agente proactivo",
           technique="Caja negra - caso de uso", expected="Se muestra la actividad de los agentes de IA")
def tc_agentes_actividad(ctx):
    _modulo(ctx, "/jefa/agent-activity", ["agente", "actividad"], "agentes_actividad")


@test_case("TC-022", "Configuración del agente proactivo", "ia_agentes", "Agente proactivo",
           technique="Caja negra - caso de uso", expected="Se muestra la configuración del agente")
def tc_agente_config(ctx):
    _modulo(ctx, "/jefa/agent-config", ["agente", "configuraci"], "agente_configuracion")


@test_case("TC-023", "Análisis de reseñas con IA (panel de la Jefa)", "ia_agentes", "Aporte 2 - Valoraciones",
           technique="Caja negra - caso de uso", expected="El panel de reseñas muestra el análisis con IA")
def tc_resenas_ia(ctx):
    _modulo(ctx, "/jefa/reviews", ["reseñ", "valoraci", "opini"], "resenas_ia")


@test_case("TC-024", "Recomendaciones por valoraciones confiables (portal del cliente)", "ia_agentes",
           "Aporte 2 - Recomendaciones", technique="Caja negra - caso de uso",
           expected="El cliente ve recomendaciones basadas en valoraciones")
def tc_recomendaciones(ctx):
    page = _login(ctx, "cliente")
    page.open("/client/recomendaciones/valoraciones")
    page.wait_for_page()
    texto = page.body_text().lower()
    ctx.check(not page.server_error(), "La página de recomendaciones carga sin error 500", texto[:120])
    ctx.check(any(p in texto for p in ["recomend", "valoraci", "producto"]), "Se muestran recomendaciones",
              texto[:160])
    ctx.screenshot("recomendaciones_cliente")


@test_case("TC-025", "Servidor MCP rechaza peticiones sin token", "ia_agentes", "MCP - RNF-01 Seguridad",
           technique="Prueba de seguridad - autenticación", expected="La API MCP responde 401 sin token")
def tc_mcp_sin_token(ctx):
    estados = {}
    for ep in ("business-summary", "stock-forecast", "audit/findings"):
        req = urllib.request.Request(f"{config.base_url}/api/mcp/{ep}", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                estados[ep] = r.status
        except urllib.error.HTTPError as e:
            estados[ep] = e.code
        except Exception as e:  # servidor caído o ruta inexistente
            estados[ep] = str(e)[:40]
    for ep, st in estados.items():
        ctx.check(st in (401, 403), f"/api/mcp/{ep} sin token responde 401/403", f"respuesta: {st}")
    ctx.driver.get(f"{config.base_url}/api/mcp/business-summary")
    ctx.screenshot("mcp_sin_token")
    ctx.notes.append(json.dumps(estados))
