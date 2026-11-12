"""Acceso a datos de prueba y generación de valores únicos por ejecución."""
from datetime import datetime

import yaml

from core.config import ROOT

with open(ROOT / "config" / "test_data.yaml", encoding="utf-8") as fh:
    DATA = yaml.safe_load(fh)


def unique_suffix():
    return datetime.now().strftime("%m%d%H%M%S%f")[:-3]


def unique_email(prefix="qa.cliente"):
    return f"{prefix}.{unique_suffix()}@hgw-test.com"
