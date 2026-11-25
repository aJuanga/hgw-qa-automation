"""Agente IA de Gherkin: convierte un test case (plantilla de clase) en escenario Gherkin
y en el código Selenium del proyecto. Usa Claude si hay clave configurada; si no, un motor local
de reglas de lenguaje natural (no necesita internet)."""
import os
import re
import unicodedata

from core.framework import load_all_tests

EJEMPLO = """ID: TC-020
Título: Inicio de sesión con credenciales válidas del empleado
Módulo: Autenticación
Precondición: El empleado está registrado y se encuentra en la página de login
Pasos:
1. Ingresar el correo empleado1@healthyglow.com
2. Ingresar la contraseña válida
3. Presionar el botón Ingresar
Resultado esperado: El sistema redirige al panel del empleado y muestra su rol"""


def _norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def parse(texto):
    tc = {"id": "TC-NUEVO", "titulo": "Caso de prueba", "modulo": "General", "pre": [], "pasos": [], "esperado": []}
    seccion = None
    for linea in texto.splitlines():
        l = linea.strip()
        if not l:
            continue
        k = _norm(l)
        valor = l.split(":", 1)[1].strip() if ":" in l else ""
        if k.startswith(("id", "codigo")) and ":" in l:
            tc["id"] = valor.upper() or tc["id"]; seccion = None
        elif k.startswith(("titulo", "nombre", "caso")) and ":" in l:
            tc["titulo"] = valor; seccion = None
        elif k.startswith(("modulo", "suite", "funcionalidad")) and ":" in l:
            tc["modulo"] = valor; seccion = None
        elif k.startswith(("precondicion", "pre-condicion", "precondiciones")):
            seccion = "pre"
            if valor: tc["pre"].append(valor)
        elif k.startswith(("pasos", "procedimiento", "acciones")):
            seccion = "pasos"
            if valor: tc["pasos"].append(valor)
        elif k.startswith(("resultado", "esperado", "salida esperada")):
            seccion = "esperado"
            if valor: tc["esperado"].append(valor)
        elif seccion:
            tc[seccion].append(re.sub(r"^(\d+[\.\)-]|[-*•])\s*", "", l))
    return tc


def _frase(s):
    s = s.strip().rstrip(".")
    return s[0].lower() + s[1:] if s else s


def _verbo(paso):
    """'Ingresar el correo X' -> 'ingreso el correo X' (primera persona, estilo Gherkin)."""
    mapa = {"ingresar": "ingreso", "presionar": "presiono", "hacer clic": "hago clic", "dar clic": "doy clic",
            "seleccionar": "selecciono", "abrir": "abro", "escribir": "escribo", "buscar": "busco",
            "navegar": "navego", "registrar": "registro", "completar": "completo", "enviar": "envío",
            "cerrar": "cierro", "iniciar": "inicio", "agregar": "agrego", "eliminar": "elimino", "editar": "edito"}
    f = _frase(paso)
    for inf, conj in mapa.items():
        if _norm(f).startswith(inf):
            return conj + f[len(inf):]
    return f


def a_gherkin(tc):
    lineas = ["# language: es", f"@{tc['id']} @{_norm(tc['modulo']).replace(' ', '_')}",
              f"Característica: {tc['modulo']}", "",
              f"  Escenario: {tc['id']} - {tc['titulo']}"]
    for i, p in enumerate(tc["pre"] or ["el sistema HGW está disponible"]):
        lineas.append(f"    {'Dado' if i == 0 else 'Y'} que {_frase(p)}")
    for i, p in enumerate(tc["pasos"]):
        lineas.append(f"    {'Cuando' if i == 0 else 'Y'} {_verbo(p)}")
    for i, e in enumerate(tc["esperado"] or ["el sistema responde correctamente"]):
        lineas.append(f"    {'Entonces' if i == 0 else 'Y'} {_frase(e)}")
    return "\n".join(lineas)


def _accion(paso):
    n = _norm(paso)
    comillas = re.findall(r"[\w.\-+]+@[\w.\-]+|\"([^\"]+)\"", paso)
    dato = next((c for c in comillas if c), None)
    if "correo" in n or "email" in n:
        return f'    page.type(LoginPage.EMAIL, "{dato or "correo@ejemplo.com"}")'
    if "contrasena" in n or "password" in n:
        return '    page.type(LoginPage.PASSWORD, pwd)'
    if "boton" in n or "clic" in n or "presion" in n:
        return '    page.click(LoginPage.SUBMIT)'
    if "busc" in n:
        return f'    productos.buscar("{dato or "VITALOE"}")'
    return f"    # {paso}"


def a_codigo(tc):
    fn = "tc_" + re.sub(r"\W+", "_", _norm(tc["titulo"])).strip("_")[:40]
    esperado = "; ".join(tc["esperado"]) or "Resultado correcto"
    cuerpo = ["    page = LoginPage(ctx.driver)", "    page.open()", f'    ctx.screenshot("{tc["id"]}_inicio")']
    cuerpo += [_accion(p) for p in tc["pasos"]]
    cuerpo += [f'    ctx.check(page.contains("..."), "{esperado}")', f'    ctx.screenshot("{tc["id"]}_resultado")']
    return "\n".join([
        f'"""{tc["id"]} - generado por el agente IA de HGW QA a partir del test case."""',
        "from core.framework import test_case", "from pages.login_page import LoginPage", "",
        f'@test_case("{tc["id"]}", "{tc["titulo"]}", "{_norm(tc["modulo"])}", "RF-01",',
        f'           expected="{esperado}")', f"def {fn}(ctx):", *cuerpo])


def _claude(texto):
    import anthropic
    prompt = ("Eres un ingeniero QA del Sistema HGW (Laravel, cafetería). Convierte este test case en: "
              "1) un escenario Gherkin en español (# language: es, Característica/Escenario/Dado/Cuando/Entonces) y "
              "2) una función Python con Selenium para el framework del proyecto (decorador @test_case, ctx.driver, "
              "ctx.check, ctx.screenshot, Page Objects). Responde con dos bloques ```gherkin y ```python.\n\n" + texto)
    msg = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]).messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"), max_tokens=2000,
        messages=[{"role": "user", "content": prompt}])
    out = msg.content[0].text
    g = re.search(r"```gherkin\n(.*?)```", out, re.S)
    p = re.search(r"```python\n(.*?)```", out, re.S)
    if g and p:
        return g.group(1).strip(), p.group(1).strip()
    raise ValueError("respuesta sin bloques")


def generar(texto):
    tc = parse(texto)
    motor = "Motor local de lenguaje natural"
    gherkin, codigo = a_gherkin(tc), a_codigo(tc)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            gherkin, codigo = _claude(texto)
            motor = "Claude (IA generativa)"
        except Exception:
            pass
    existentes = {c.id for c in load_all_tests()}
    return {"tc": tc, "gherkin": gherkin, "codigo": codigo, "motor": motor,
            "ejecutable": tc["id"] in existentes}


def gherkin_proyecto():
    """Escenario Gherkin de cada test case automatizado del proyecto."""
    por_suite = {}
    for c in load_all_tests():
        por_suite.setdefault(c.suite, []).append(c)
    bloques = []
    for suite, casos in por_suite.items():
        b = ["# language: es", f"Característica: {suite.capitalize()} del Sistema HGW", ""]
        for c in casos:
            b += [f"  @{c.id} @{suite}", f"  Escenario: {c.id} - {c.title}",
                  "    Dado que el Sistema HGW está disponible en el navegador",
                  f"    Cuando se ejecuta el flujo «{_frase(c.title)}» ({c.technique})",
                  f"    Entonces {_frase(c.expected or 'el resultado es el esperado')}",
                  f"    # Requisito: {c.requirement} · Prioridad: {c.priority}", ""]
        bloques.append("\n".join(b))
    return bloques
