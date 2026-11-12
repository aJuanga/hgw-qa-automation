"""Ejecución por consola.

Ejemplos:
  python run_tests.py                         # todas las suites
  python run_tests.py --suite autenticacion   # una suite
  python run_tests.py --suite productos seguridad --mail destino@gmail.com
  python run_tests.py --ids TC-001 TC-014     # casos puntuales
  python run_tests.py --list                  # listar suites y casos
"""
import argparse
import sys

from core.runner import execute, list_suites


def main():
    ap = argparse.ArgumentParser(description="HGW QA Automation - Selenium WebDriver + POM")
    ap.add_argument("--suite", nargs="*", help="Suites a ejecutar")
    ap.add_argument("--ids", nargs="*", help="IDs de casos a ejecutar")
    ap.add_argument("--mail", help="Correo destino para enviar los resultados")
    ap.add_argument("--no-ai", action="store_true", help="No usar IA en el análisis")
    ap.add_argument("--list", action="store_true", help="Listar suites y casos")
    a = ap.parse_args()
    if a.list:
        for suite, cases in list_suites().items():
            print(f"[{suite}]")
            for c in cases:
                print(f"   {c.id}  {c.title}  ({c.requirement})")
        return 0
    run = execute(suites=a.suite, ids=a.ids, mail_to=a.mail, use_ai=not a.no_ai)
    return 1 if run["summary"]["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
