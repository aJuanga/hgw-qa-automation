"""Carga de configuración: config/config.yaml (general) + .env (secretos)."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Config:
    def __init__(self, path: Path = ROOT / "config" / "config.yaml"):
        with open(path, encoding="utf-8") as fh:
            self._data = yaml.safe_load(fh)
        self.base_url = os.getenv("HGW_BASE_URL", self._data["app"]["base_url"]).rstrip("/")
        self.app_name = self._data["app"]["name"]
        self.app_version = self._data["app"]["version"]
        b = self._data["browser"]
        self.browser = os.getenv("HGW_BROWSER", b["name"])
        env_headless = os.getenv("HGW_HEADLESS")
        self.headless = (env_headless.lower() == "true") if env_headless else bool(b["headless"])
        self.window_size = b["window_size"]
        self.explicit_wait = int(b["explicit_wait"])
        self.page_load_limit = float(b["page_load_limit"])
        self.reports_dir = ROOT / self._data["reports"]["output_dir"]
        self.evidence_dir = ROOT / self._data["reports"]["evidence_dir"]
        self.reports_dir.mkdir(exist_ok=True)
        self.evidence_dir.mkdir(exist_ok=True)

    @staticmethod
    def user(role: str):
        """Devuelve (email, password) del rol pedido: jefa, empleado o cliente."""
        role = role.upper()
        return os.getenv(f"HGW_{role}_EMAIL", ""), os.getenv(f"HGW_{role}_PASSWORD", "")


config = Config()
