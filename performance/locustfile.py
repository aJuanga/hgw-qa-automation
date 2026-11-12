"""Prueba de carga del Sistema HGW con Locust.

Modela dos tipos de usuario:
  - VisitanteAnonimo: abre el login y el registro público de clientes.
  - JefaAutenticada: inicia sesión una vez y consulta productos, búsqueda e inventario.

Ejemplo (20 usuarios, 2 por segundo, 2 minutos, reporte HTML):
  locust -f performance/locustfile.py --host http://localhost:8000 --headless \
         -u 20 -r 2 -t 2m --html reports/locust_carga.html --csv reports/locust_carga
"""
import os
import re

from dotenv import load_dotenv
from locust import HttpUser, between, task

load_dotenv()
TOKEN = re.compile(r'name="_token" value="([^"]+)"')


class VisitanteAnonimo(HttpUser):
    weight = 1
    wait_time = between(1, 3)

    @task(3)
    def ver_login(self):
        self.client.get("/login", name="GET /login")

    @task(1)
    def ver_registro(self):
        self.client.get("/register-client", name="GET /register-client")


class JefaAutenticada(HttpUser):
    weight = 2
    wait_time = between(1, 3)

    def on_start(self):
        page = self.client.get("/login", name="GET /login")
        token = TOKEN.search(page.text)
        self.client.post("/login", name="POST /login", data={
            "_token": token.group(1) if token else "",
            "email": os.getenv("HGW_JEFA_EMAIL", ""),
            "password": os.getenv("HGW_JEFA_PASSWORD", ""),
        })

    def _get_autenticado(self, url, name):
        """GET que falla si el servidor redirige al login (sesión perdida) o responde error."""
        with self.client.get(url, name=name, catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
            elif "/login" in r.url:
                r.failure("Redirigido a /login: sesión no válida")
            else:
                r.success()

    @task(3)
    def listar_productos(self):
        self._get_autenticado("/products", "GET /products")

    @task(2)
    def buscar_producto(self):
        self._get_autenticado("/products?search=Caf%C3%A9", "GET /products?search")

    @task(1)
    def ver_inventario(self):
        self._get_autenticado("/inventory", "GET /inventory")
