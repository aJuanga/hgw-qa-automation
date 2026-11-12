"""Suite CONTROL DE ACCESO POR ROL - RF-02, RF-12, RNF-01."""
from core.config import config
from core.framework import Blocked, test_case
from pages.base_page import BasePage
from pages.login_page import LoginPage


def _login(ctx, role):
    email, pwd = config.user(role)
    if not pwd:
        raise Blocked(f"Falta HGW_{role.upper()}_PASSWORD en el archivo .env")
    page = LoginPage(ctx.driver)
    page.open()
    page.login(email, pwd)
    ctx.require("/login" not in page.url, f"Precondición: sesión de {role} iniciada", f"URL: {page.url}")
    return page


@test_case("TC-014", "Empleado intenta acceder a Reportes (exclusivo de Jefa)", "seguridad", "RF-02",
           technique="Tabla de decisión (rol x recurso)",
           expected="El sistema responde 403 'No tienes permiso'")
def tc_empleado_sin_reportes(ctx):
    page = _login(ctx, "empleado")
    page.open("/reports")
    text = page.body_text()
    ctx.check("403" in text or "No tienes permiso" in text or "Forbidden" in text,
              "Se muestra acceso denegado (403)", text[:120])
    ctx.check("Reporte de Ventas" not in text, "No se muestra el contenido de reportes")
    ctx.screenshot("empleado_403")


@test_case("TC-015", "Usuario no autenticado intenta crear productos", "seguridad", "RF-02, RNF-01",
           technique="Tabla de decisión (rol x recurso)",
           expected="Redirige a /login sin mostrar el formulario")
def tc_anonimo_redirigido(ctx):
    page = BasePage(ctx.driver)
    page.open("/products/create")
    ctx.check("/login" in page.url, "Redirige a /login", f"URL: {page.url}")
    ctx.check(page.is_visible(LoginPage.EMAIL), "Se muestra el formulario de inicio de sesión")
    ctx.screenshot("anonimo_redirigido")


@test_case("TC-016", "Cliente inicia sesión y accede a su portal", "seguridad", "RF-02, RF-12",
           expected="Redirige a /client/dashboard y muestra el portal del cliente sin errores")
def tc_cliente_portal(ctx):
    page = _login(ctx, "cliente")
    ctx.check("/client/dashboard" in page.url, "Redirige a /client/dashboard", f"URL: {page.url}")
    ctx.check(not page.server_error(), "El portal carga sin error del servidor",
              f"Título de la página: {page.title[:160]}")
    ctx.screenshot("portal_cliente")
