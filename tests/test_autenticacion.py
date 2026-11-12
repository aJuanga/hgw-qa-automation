"""Suite AUTENTICACIÓN - RF-01 / RF-02."""
from core.config import config
from core.framework import Blocked, test_case
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from tests.data import DATA

D = DATA["login"]


def _jefa():
    email, pwd = config.user("jefa")
    if not pwd:
        raise Blocked("Falta HGW_JEFA_PASSWORD en el archivo .env")
    return email, pwd


@test_case("TC-001", "Inicio de sesión con credenciales válidas (Jefa)", "autenticacion", "RF-01, RF-02",
           expected="Redirige al Dashboard Ejecutivo y muestra el rol Jefa")
def tc_login_valido(ctx):
    email, pwd = _jefa()
    page = LoginPage(ctx.driver)
    page.open()
    ctx.screenshot("formulario_login")
    page.login(email, pwd)
    ctx.require(page.wait_url_contains("/jefa/dashboard"), "La URL cambia a /jefa/dashboard", f"URL actual: {page.url}")
    ctx.check(DashboardPage.HEADER_TEXT in ctx.driver.title, "Se muestra el 'Panel ejecutivo'", f"título: {ctx.driver.title}")
    ctx.check(page.contains("Jefa"), "Se muestra el rol 'Jefa' en el panel")
    ctx.screenshot("dashboard_jefa")


@test_case("TC-002", "Inicio de sesión con contraseña incorrecta", "autenticacion", "RF-01",
           expected="Permanece en /login y muestra mensaje de credenciales inválidas")
def tc_login_invalido(ctx):
    page = LoginPage(ctx.driver)
    page.open()
    page.login(D["invalid_email"], D["invalid_password"])
    ctx.check("/login" in page.url, "Permanece en la página /login", f"URL actual: {page.url}")
    ctx.check(bool(page.error_text()), "Muestra el mensaje de credenciales inválidas", "no apareció ningún mensaje de error")
    ctx.check(DashboardPage.HEADER_TEXT not in ctx.driver.title, "No se accede al Panel ejecutivo")
    ctx.screenshot("error_credenciales")


@test_case("TC-003", "Inicio de sesión con campos vacíos", "autenticacion", "RF-01",
           technique="Valores límite (longitud 0)",
           expected="El navegador bloquea el envío por campos obligatorios")
def tc_login_vacio(ctx):
    page = LoginPage(ctx.driver)
    page.open()
    page.click(LoginPage.SUBMIT)
    msg = page.validation_message(LoginPage.EMAIL)
    ctx.check(msg != "", "El campo correo muestra validación de obligatorio", "validationMessage vacío")
    ctx.check("/login" in page.url, "El formulario no se envía (permanece en /login)")
    ctx.metrics["validation_message"] = msg
    ctx.screenshot("campos_vacios")


@test_case("TC-004", "Inicio de sesión con correo sin formato válido", "autenticacion", "RF-01",
           expected="El campo de correo rechaza el valor sin '@'")
def tc_login_email_malformado(ctx):
    page = LoginPage(ctx.driver)
    page.open()
    page.type(LoginPage.EMAIL, D["malformed_email"])
    page.type(LoginPage.PASSWORD, "cualquiera123")
    page.click(LoginPage.SUBMIT)
    msg = page.validation_message(LoginPage.EMAIL)
    ctx.check("@" in msg or msg != "", "El navegador indica formato de correo inválido", f"Mensaje: '{msg}'")
    ctx.check("/login" in page.url, "Permanece en /login")
    ctx.screenshot("correo_malformado")


@test_case("TC-005", "Cierre de sesión de la Jefa", "autenticacion", "RF-01", priority="Media",
           expected="Se cierra la sesión y las rutas protegidas vuelven a pedir login")
def tc_logout(ctx):
    email, pwd = _jefa()
    page = LoginPage(ctx.driver)
    page.open()
    page.login(email, pwd)
    ctx.require(page.wait_url_contains("/jefa/dashboard"), "Sesión iniciada")
    DashboardPage(ctx.driver).logout()
    page.open("/jefa/dashboard")
    ctx.check("/login" in page.url, "Al volver al dashboard redirige a /login", f"URL: {page.url}")
    ctx.check(page.is_visible(LoginPage.EMAIL), "Se muestra el formulario de inicio de sesión")
    ctx.screenshot("sesion_cerrada")


@test_case("TC-018", "Mensaje de credenciales inválidas en español", "autenticacion", "RF-01, RNF-07",
           priority="Baja", technique="Prueba de usabilidad (idioma de la interfaz)",
           expected="Todo el mensaje de error se muestra en español, igual que el resto de la interfaz")
def tc_login_mensaje_espanol(ctx):
    page = LoginPage(ctx.driver)
    page.open()
    page.login(D["invalid_email"], D["invalid_password"])
    ctx.require("/login" in page.url, "Permanece en la página /login", f"URL actual: {page.url}")
    ctx.screenshot("mensaje_error_idioma")
    ctx.check(not page.contains("These credentials do not match our records"),
              "El detalle del error no aparece en inglés",
              "Se muestra 'These credentials do not match our records.' (texto por defecto de Laravel en inglés)")
