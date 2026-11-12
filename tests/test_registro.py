"""Suite REGISTRO DE CLIENTES - RF-01, RF-10, RF-12."""
from core.framework import Blocked, test_case
from pages.login_page import LoginPage
from pages.register_client_page import RegisterClientPage
from tests.data import DATA, unique_email

D = DATA["registro_cliente"]


def _register(ctx, data):
    page = RegisterClientPage(ctx.driver)
    page.open()
    page.register(data)
    if page.throttled():
        ctx.screenshot("limite_429")
        raise Blocked("RNF-03: el servidor aplicó el límite de 5 registros por hora (HTTP 429). "
                      "Ejecutar 'php artisan cache:clear' en HGW o esperar 60 minutos.")
    return page


@test_case("TC-006", "Registro de cliente con datos válidos", "registro", "RF-01, RF-10",
           expected="Muestra '¡Registro exitoso!' y el nuevo cliente puede iniciar sesión")
def tc_registro_valido(ctx):
    data = dict(D["valid"], email=unique_email())
    page = _register(ctx, data)
    ctx.check(page.in_dom(RegisterClientPage.SUCCESS_TEXT), "Se muestra el mensaje de registro exitoso")
    ctx.screenshot("registro_exitoso")
    login = LoginPage(ctx.driver)
    login.open()
    login.login(data["email"], data["password"])
    ctx.check("/login" not in login.url, "El cliente registrado puede iniciar sesión", f"URL: {login.url}")
    ctx.metrics["email_registrado"] = data["email"]
    ctx.screenshot("login_nuevo_cliente")


@test_case("TC-007", "Registro con contraseñas que no coinciden", "registro", "RF-01",
           expected="Rechaza el registro con 'Las contraseñas no coinciden'")
def tc_registro_password_distinto(ctx):
    data = dict(D["password_mismatch"], email=unique_email())
    page = _register(ctx, data)
    ctx.check(page.in_dom("Las contraseñas no coinciden"), "Muestra el mensaje de contraseñas distintas")
    ctx.check(not page.in_dom(RegisterClientPage.SUCCESS_TEXT), "No muestra registro exitoso")
    ctx.screenshot("password_no_coincide")


@test_case("TC-008", "Registro con contraseña menor a 8 caracteres", "registro", "RF-01",
           technique="Valores límite (7 caracteres < mínimo 8)",
           expected="Rechaza la contraseña corta con mensaje de mínimo 8 caracteres")
def tc_registro_password_corta(ctx):
    data = dict(D["short_password"], email=unique_email())
    page = _register(ctx, data)
    ctx.check(page.in_dom("al menos 8 caracteres"), "Muestra el mensaje de longitud mínima")
    ctx.check(not page.in_dom(RegisterClientPage.SUCCESS_TEXT), "No muestra registro exitoso")
    ctx.screenshot("password_corta")


@test_case("TC-009", "Registro con correo ya existente", "registro", "RF-01", priority="Media",
           expected="Rechaza el registro con 'Este correo electrónico ya está registrado'")
def tc_registro_duplicado(ctx):
    data = dict(D["valid"], email=D["duplicate_email"])
    page = _register(ctx, data)
    ctx.check(page.in_dom("ya está registrado"), "Muestra el mensaje de correo duplicado")
    ctx.check(not page.in_dom(RegisterClientPage.SUCCESS_TEXT), "No muestra registro exitoso")
    ctx.screenshot("correo_duplicado")
