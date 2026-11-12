"""Suite RENDIMIENTO PERCIBIDO (no funcional) - RNF-05: respuesta menor a 3 s."""
from core.config import config
from core.framework import Blocked, test_case
from pages.login_page import LoginPage


@test_case("TC-017", "Tiempo de carga de páginas principales menor a 3 s", "rendimiento", "RNF-05",
           priority="Media", technique="Medición de tiempo de carga (navegador)",
           expected="Login, dashboard y productos cargan en menos de 3 segundos")
def tc_tiempos_carga(ctx):
    email, pwd = config.user("jefa")
    if not pwd:
        raise Blocked("Falta HGW_JEFA_PASSWORD en el archivo .env")
    limit = config.page_load_limit
    page = LoginPage(ctx.driver)
    t_login = page.open()
    page.login(email, pwd)
    timings = {"/login": t_login}
    for path in ("/jefa/dashboard", "/products", "/inventory", "/orders"):
        timings[path] = page.open(path)
    ctx.metrics.update({f"carga {k} (s)": v for k, v in timings.items()})
    for path, t in timings.items():
        ctx.check(t < limit, f"{path} carga en {t} s (< {limit} s)", f"Tardó {t} s")
    ctx.screenshot("productos_cargado")
