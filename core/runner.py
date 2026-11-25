"""Motor de ejecución: selecciona casos, los ejecuta, genera reportes y envía el correo."""
import json
import platform
import time
import traceback
from datetime import datetime

import selenium

from core.config import config
from core.driver_factory import create_driver
from core.framework import Blocked, CheckFailed, Context, load_all_tests


def list_suites():
    cases = load_all_tests()
    suites = {}
    for c in cases:
        suites.setdefault(c.suite, []).append(c)
    return suites


# Tipos de prueba (checklist del runner): cada tipo agrupa uno o más test cases
TIPOS = {
    "Smoke": ["TC-001", "TC-005", "TC-010", "TC-016", "TC-017"],
    "Regresión": "*",
    "Funcional (caja negra)": ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007", "TC-008",
                               "TC-009", "TC-010", "TC-011", "TC-012", "TC-013", "TC-018", "TC-019"],
    "Negativas (valores inválidos)": ["TC-002", "TC-003", "TC-004", "TC-007", "TC-008", "TC-009", "TC-011", "TC-013"],
    "Seguridad (roles y acceso)": ["TC-014", "TC-015", "TC-016"],
    "No funcional (rendimiento)": ["TC-017"],
}


def ids_por_tipo(tipos):
    todos = [c.id for c in load_all_tests()]
    ids = []
    for t in tipos or []:
        lista = todos if TIPOS.get(t) == "*" else TIPOS.get(t, [])
        ids += [i for i in lista if i not in ids]
    return ids


def select_cases(suites=None, ids=None):
    cases = load_all_tests()
    if ids:
        ids = {i.strip().upper() for i in ids}
        return [c for c in cases if c.id.upper() in ids]
    if suites:
        return [c for c in cases if c.suite in suites]
    return list(cases)


def run_case(case, evidence_dir, log):
    driver = None
    start = time.perf_counter()
    started_at = datetime.now()
    status, error = "PASS", ""
    ctx = None
    try:
        driver = create_driver()
        from core import live
        live.set_case(driver, f"{case.id} - {case.title}")
        ctx = Context(driver=driver, case=case, evidence_dir=evidence_dir)
        case.func(ctx)
        if any(not c.passed for c in ctx.checks):
            status = "FAIL"
            error = "; ".join(c.description for c in ctx.checks if not c.passed)
    except CheckFailed as exc:
        status, error = "FAIL", str(exc)
    except Blocked as exc:
        status, error = "BLOCKED", str(exc)
    except Exception as exc:  # error de script, localizador o ambiente
        status = "FAIL"
        error = f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}"
        log(traceback.format_exc(limit=2))
    finally:
        if ctx and status != "PASS":
            try:
                ctx.screenshot("estado_al_fallar")
            except Exception:
                pass
        if driver:
            driver.quit()
    duration = round(time.perf_counter() - start, 2)
    return {
        "id": case.id, "title": case.title, "suite": case.suite,
        "requirement": case.requirement, "priority": case.priority,
        "technique": case.technique, "expected": case.expected,
        "status": status, "error": error, "duration": duration,
        "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": [c.__dict__ for c in (ctx.checks if ctx else [])],
        "screenshots": ctx.screenshots if ctx else [],
        "metrics": ctx.metrics if ctx else {},
    }


def execute(suites=None, ids=None, mail_to=None, use_ai=True, log=print, run_name=None):
    """Ejecuta los casos y devuelve el diccionario de resultados de la corrida."""
    from core import mailer, report_docx, report_html
    from ai import analyzer

    cases = select_cases(suites, ids)
    run_id = run_name or datetime.now().strftime("RUN_%Y%m%d_%H%M%S")
    run_dir = config.reports_dir / run_id
    evidence_dir = run_dir / "screenshots"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    log(f"Corrida {run_id}: {len(cases)} caso(s) contra {config.base_url}")
    t0 = time.perf_counter()
    results = []
    for i, case in enumerate(cases, 1):
        log(f"[{i}/{len(cases)}] {case.id} - {case.title} ...")
        r = run_case(case, evidence_dir, log)
        results.append(r)
        log(f"      -> {r['status']} ({r['duration']} s) {r['error']}")

    summary = {s: sum(1 for r in results if r["status"] == s) for s in ("PASS", "FAIL", "BLOCKED", "NOT RUN")}
    summary["total"] = len(results)
    summary["pass_rate"] = round(summary["PASS"] * 100 / len(results), 1) if results else 0.0
    run = {
        "run_id": run_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": round(time.perf_counter() - t0, 2),
        "environment": {
            "base_url": config.base_url, "app": config.app_name, "app_version": config.app_version,
            "browser": config.browser, "headless": config.headless,
            "os": f"{platform.system()} {platform.release()}", "python": platform.python_version(),
            "selenium": selenium.__version__,
        },
        "suites": sorted({r["suite"] for r in results}),
        "summary": summary,
        "results": results,
    }

    log("Analizando resultados...")
    run["analysis"] = analyzer.analyze(run, use_ai=use_ai)

    (run_dir / "results.json").write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path = report_html.build(run, run_dir)
    docx_path = report_docx.build(run, run_dir)
    run["reports"] = {"html": str(html_path), "docx": str(docx_path)}
    log(f"Reporte HTML: {html_path}")
    log(f"Informe Word: {docx_path}")

    if mail_to:
        try:
            mailer.send_results(run, mail_to, [html_path, docx_path])
            run["mail"] = f"Enviado a {mail_to}"
        except Exception as exc:
            run["mail"] = f"No enviado: {exc}"
        log(f"Correo: {run['mail']}")
    (run_dir / "results.json").write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Resumen: {summary}")
    return run
