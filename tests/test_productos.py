"""Suite PRODUCTOS - RF-07 (catálogo, búsqueda y alta de productos)."""
from core.config import config
from core.framework import Blocked, test_case
from pages.login_page import LoginPage
from pages.products_page import ProductFormPage, ProductsPage
from tests.data import DATA, unique_suffix

D = DATA["productos"]


def _login_jefa(ctx):
    email, pwd = config.user("jefa")
    if not pwd:
        raise Blocked("Falta HGW_JEFA_PASSWORD en el archivo .env")
    page = LoginPage(ctx.driver)
    page.open()
    page.login(email, pwd)
    ctx.require(page.wait_url_contains("/dashboard"), "Precondición: sesión de Jefa iniciada")


@test_case("TC-010", "Búsqueda de producto existente por nombre", "productos", "RF-07",
           expected="El listado muestra solo el producto 'Vitaloe' (Jugo de Aloe Vera)")
def tc_buscar_existente(ctx):
    _login_jefa(ctx)
    page = ProductsPage(ctx.driver)
    page.open()
    page.search(D["search_existing"])
    rows = " ".join(page.rows_text())
    ctx.check(D["expected_match"] in rows, f"Aparece '{D['expected_match']}' en los resultados")
    ctx.check(D["expected_absent"] not in rows, f"No aparece '{D['expected_absent']}' (no coincide)")
    ctx.check("search=" in page.url, "La búsqueda se refleja en la URL")
    ctx.screenshot("busqueda_vitaloe")


@test_case("TC-011", "Búsqueda de producto inexistente", "productos", "RF-07", priority="Media",
           expected="El listado no muestra productos")
def tc_buscar_inexistente(ctx):
    _login_jefa(ctx)
    page = ProductsPage(ctx.driver)
    page.open()
    page.search(D["search_missing"])
    rows = " ".join(page.rows_text())
    ctx.check(D["expected_match"] not in rows, "No aparecen productos del catálogo")
    ctx.check(D["search_missing"] not in rows, "No existe ninguna fila con el término buscado")
    ctx.screenshot("busqueda_sin_resultados")


@test_case("TC-012", "Registro de un producto nuevo con datos válidos", "productos", "RF-07",
           expected="Muestra 'Producto creado exitosamente' y el producto aparece en la búsqueda")
def tc_crear_producto(ctx):
    _login_jefa(ctx)
    data = dict(D["nuevo"], name=f"{D['nuevo']['name_prefix']} {unique_suffix()}")
    form = ProductFormPage(ctx.driver)
    form.open()
    form.fill(data)
    ctx.screenshot("formulario_producto")
    form.submit()
    listing = ProductsPage(ctx.driver)
    listing.wait_url_contains("/products?", timeout=1) or listing.wait.until(lambda d: "/create" not in d.current_url)
    ctx.require(not listing.server_error(), "El servidor procesa el alta sin error interno",
                f"Página de error: {listing.title[:150]}")
    ctx.check(listing.wait_in_dom(ProductsPage.SUCCESS_CREATED), "Muestra 'Producto creado exitosamente'")
    listing.search(data["name"])
    ctx.check(data["name"] in " ".join(listing.rows_text()), "El nuevo producto aparece al buscarlo")
    ctx.metrics["producto_creado"] = data["name"]
    ctx.screenshot("producto_creado")


@test_case("TC-013", "Registro de producto con precio negativo", "productos", "RF-07",
           technique="Valores límite (precio < 0)",
           expected="El sistema rechaza el precio negativo y no crea el producto")
def tc_producto_precio_negativo(ctx):
    _login_jefa(ctx)
    data = dict(D["nuevo"], name=f"QA Precio Negativo {unique_suffix()}", price=D["precio_negativo"])
    form = ProductFormPage(ctx.driver)
    form.open()
    form.fill(data)
    form.submit()
    ctx.check("/products/create" in form.url, "Permanece en el formulario de creación", f"URL: {form.url}")
    ctx.check(not form.in_dom(ProductsPage.SUCCESS_CREATED), "No muestra 'Producto creado exitosamente'")
    ctx.screenshot("precio_negativo")


@test_case("TC-019", "Búsqueda de productos sin distinguir mayúsculas", "productos", "RF-07, RNF-07",
           priority="Media", technique="Partición de equivalencia (mayúsculas / minúsculas)",
           expected="Buscar 'vitaloe' en minúsculas también lista 'Vitaloe – Jugo de Aloe Vera'")
def tc_buscar_minusculas(ctx):
    _login_jefa(ctx)
    page = ProductsPage(ctx.driver)
    page.open()
    page.search(D["search_lowercase"])
    rows = " ".join(page.rows_text())
    ctx.screenshot("busqueda_minusculas")
    ctx.check("search=" in page.url, "La búsqueda se refleja en la URL")
    ctx.check(D["expected_lowercase_match"] in rows,
              f"Aparece '{D['expected_lowercase_match']}' al buscar '{D['search_lowercase']}'",
              "La consulta usa LIKE, que en PostgreSQL distingue mayúsculas y minúsculas")
