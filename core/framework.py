"""Mini-framework propio (sin pytest): registro de casos, contexto y aserciones.

Cada caso se declara con el decorador @test_case y recibe un objeto Context con:
  ctx.driver        -> WebDriver listo para usar
  ctx.check(...)    -> aserción que se registra en el reporte (no detiene el caso)
  ctx.require(...)  -> aserción crítica (si falla, detiene el caso)
  ctx.screenshot()  -> captura de pantalla como evidencia
"""
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

REGISTRY = []


class CheckFailed(AssertionError):
    """Una aserción crítica falló: el sistema no se comportó como se esperaba."""


class Blocked(Exception):
    """El caso no puede ejecutarse por una condición externa (datos, ambiente)."""


@dataclass
class TestCaseDef:
    id: str
    title: str
    suite: str
    requirement: str
    priority: str
    technique: str
    expected: str
    func: object = None


def test_case(id, title, suite, requirement, priority="Alta", technique="Partición de equivalencia", expected=""):
    def wrap(func):
        REGISTRY.append(TestCaseDef(id, title, suite, requirement, priority, technique, expected, func))
        return func
    return wrap


@dataclass
class Check:
    description: str
    passed: bool
    detail: str = ""


@dataclass
class Context:
    driver: object
    case: TestCaseDef
    evidence_dir: Path
    checks: list = field(default_factory=list)
    screenshots: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    def check(self, condition, description, detail=""):
        self.checks.append(Check(description, bool(condition), "" if condition else detail))
        return bool(condition)

    def require(self, condition, description, detail=""):
        if not self.check(condition, description, detail):
            raise CheckFailed(f"{description}. {detail}".strip())

    def screenshot(self, label):
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", label)[:40]
        time.sleep(0.9)  # deja terminar las animaciones de entrada antes de capturar
        path = self.evidence_dir / f"{self.case.id}_{len(self.screenshots) + 1:02d}_{safe}.png"
        self.driver.save_screenshot(str(path))
        self.screenshots.append({"label": label, "path": str(path)})
        return path

    def measure(self, name, start):
        self.metrics[name] = round(time.perf_counter() - start, 3)
        return self.metrics[name]


def load_all_tests():
    """Importa los módulos de tests para que se registren los casos."""
    import importlib
    import pkgutil
    import tests
    for mod in pkgutil.iter_modules(tests.__path__):
        if mod.name.startswith("test_"):
            importlib.import_module(f"tests.{mod.name}")
    return REGISTRY
