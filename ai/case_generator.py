"""Generador de escenarios de prueba con IA a partir de un requisito.

Uso:
    python -m ai.case_generator "RF-07: El sistema debe gestionar un catálogo de productos..."
Guarda la respuesta en docs/ia/ para revisión humana. Los casos generados NO se
consideran válidos hasta revisarlos, adaptarlos y ejecutarlos.
"""
import os
import sys
from datetime import datetime

from core.config import ROOT

PROMPT = """Actúa como analista QA. A partir del siguiente requisito del Sistema HGW (cafetería
saludable, Laravel), genera en español:
- 3 escenarios positivos, 3 negativos y 2 de valores límite en formato Gherkin (Dado/Cuando/Entonces).
- Para cada uno indica la técnica de diseño (partición de equivalencia, valores límite o tabla de decisión).
- Marca cuáles conviene automatizar con Selenium y por qué.
Requisito: {req}"""


def main():
    req = " ".join(sys.argv[1:]).strip()
    if not req:
        sys.exit("Indica el requisito entre comillas.")
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        sys.exit("Configura ANTHROPIC_API_KEY en el archivo .env para usar el generador.")
    import anthropic
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    msg = anthropic.Anthropic(api_key=key).messages.create(
        model=model, max_tokens=2000, messages=[{"role": "user", "content": PROMPT.format(req=req)}])
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    out_dir = ROOT / "docs" / "ia"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"escenarios_{datetime.now():%Y%m%d_%H%M%S}.md"
    out.write_text(f"# Escenarios generados con IA ({model})\n\n**Prompt:**\n\n{PROMPT.format(req=req)}\n\n"
                   f"**Respuesta:**\n\n{text}\n\n**Revisión del estudiante:** (completar)\n", encoding="utf-8")
    print(text)
    print(f"\nGuardado en {out}")


if __name__ == "__main__":
    main()
