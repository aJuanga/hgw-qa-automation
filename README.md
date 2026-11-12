# HGW QA Automation

Solución de automatización de pruebas del **Sistema HGW – Cafetería Saludable** (Laravel 10 + PostgreSQL).
Proyecto Integrador · Testing & Quality Assurance · UNIFRANZ · Juan Gabriel Ibañez Copatiti

- **Framework principal:** Selenium WebDriver 4 + Python 3, patrón **Page Object Model** (sin pytest, con un runner propio)
- **Interfaz web** para elegir suites o casos, lanzar la ejecución y ver el estado y el historial (Flask)
- **Reportes:** HTML autocontenido + informe **Word (.docx)** con capturas, por cada corrida
- **Correo automático** con el resumen y los reportes adjuntos (SMTP / Gmail)
- **IA:** análisis de resultados y generación de escenarios con Claude (Anthropic), con respaldo por reglas
- **No funcionales:** Locust (carga y estrés) + medición de tiempos de carga en el navegador (RNF-05)

> Este repositorio **lanza** las pruebas. La aplicación probada es el Sistema HGW, que corre aparte (`http://localhost:8000`).

## Estructura

```
hgw-qa-automation/
├── ai/                  # IA: analyzer.py (análisis de resultados) y case_generator.py (escenarios Gherkin)
├── config/              # config.yaml (URL, navegador, tiempos) y test_data.yaml (datos de prueba)
├── core/                # framework.py (casos y aserciones), runner.py, driver_factory.py,
│                        # report_html.py, report_docx.py, mailer.py, images.py, config.py
├── pages/               # Page Objects: base_page, login_page, dashboard_page,
│                        # register_client_page, products_page
├── tests/               # Suites: autenticacion, registro, productos, seguridad, rendimiento
├── performance/         # locustfile.py (pruebas de carga y estrés)
├── web/                 # app.py + templates/index.html (HGW QA Runner)
├── docs/evidencias/     # Evidencias oficiales: ejecuciones, bugs, runner, no_funcionales
├── docs/correcciones_hgw/  # Parche con las correcciones de BUG-001 a BUG-003 para HGW
├── reports/             # Salida de cada corrida (no se versiona)
├── run_tests.py         # Ejecución por consola
├── requirements.txt
└── .env.example         # Plantilla de variables (sin secretos)
```

## Requisitos previos

1. Python 3.10 o superior y Google Chrome (o Edge/Firefox). Selenium Manager descarga el driver automáticamente.
2. Sistema HGW en ejecución (`php artisan serve`), con la base de datos sembrada (`php artisan migrate --seed`)
   y el servidor WebSocket activo (`php artisan websockets:serve`), por ejemplo con `INICIAR-SISTEMA.bat`.
3. El catálogo debe tener el menú real de HGW (13 productos, por ejemplo "VITALOE - Jugo de Aloe Vera…" y los cafés con Cordyceps),
   que usan TC-010 y TC-019. Si tu menú es otro, cambia `search_existing`, `expected_match`, `expected_absent`,
   `search_lowercase` y `expected_lowercase_match` en `config/test_data.yaml`.
4. La contraseña de la Jefa en `.env` debe ser la que realmente quedó en la base. Ojo: en el `.env` de HGW,
   `JEFA_PASSWORD=CambiarEstaClaveAhora#2026` sin comillas se lee como `CambiarEstaClaveAhora` (el `#` inicia un comentario).

## Instalación

```bash
git clone https://github.com/aJuanga/hgw-qa-automation.git
cd hgw-qa-automation
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux/Mac: cp .env.example .env
```

Completa `.env` con las contraseñas de los usuarios de prueba, los datos SMTP y, si quieres usar IA, `ANTHROPIC_API_KEY`.
**Nunca subas `.env` a GitHub** (ya está en `.gitignore`).

## Ejecución

### Interfaz web (recomendado)

```bash
python -m web.app
```

Abre `http://localhost:5000`, marca suites o casos, escribe el correo destino y pulsa **Ejecutar pruebas**.
El panel muestra el avance en vivo y, al terminar, el historial con enlaces al reporte HTML y al informe Word.

### Consola

```bash
python run_tests.py --list                              # lista suites y casos
python run_tests.py                                     # todas las suites
python run_tests.py --suite autenticacion seguridad     # suites específicas
python run_tests.py --ids TC-012 TC-016                 # casos específicos (retesting)
python run_tests.py --mail destino@gmail.com            # envía el resultado por correo
python run_tests.py --no-ai                             # análisis sin IA
```

Los resultados quedan en `reports/RUN_AAAAMMDD_HHMMSS/` (`results.json`, `reporte_*.html`, `informe_*.docx`, `screenshots/`).

### Pruebas no funcionales (Locust)

```bash
# Carga: 20 usuarios, 2 por segundo, 2 minutos
locust -f performance/locustfile.py --host http://localhost:8000 --headless -u 20 -r 2 -t 2m --html reports/locust_carga.html --csv reports/locust_carga
# Estrés: 100 usuarios, 5 por segundo, 2 minutos
locust -f performance/locustfile.py --host http://localhost:8000 --headless -u 100 -r 5 -t 2m --html reports/locust_estres.html --csv reports/locust_estres
```

### Generador de escenarios con IA

```bash
python -m ai.case_generator "RF-07: El sistema debe gestionar un catálogo de productos con categorías..."
```

La respuesta se guarda en `docs/ia/` para revisarla antes de usarla.

## Casos automatizados

| ID | Suite | Caso | Requisito |
|----|-------|------|-----------|
| TC-001 | autenticacion | Inicio de sesión válido (Jefa) | RF-01, RF-02 |
| TC-002 | autenticacion | Contraseña incorrecta | RF-01 |
| TC-003 | autenticacion | Campos vacíos | RF-01 |
| TC-004 | autenticacion | Correo sin formato válido | RF-01 |
| TC-005 | autenticacion | Cierre de sesión | RF-01 |
| TC-006 | registro | Registro de cliente válido | RF-01, RF-10 |
| TC-007 | registro | Contraseñas que no coinciden | RF-01 |
| TC-008 | registro | Contraseña menor a 8 caracteres | RF-01 |
| TC-009 | registro | Correo ya registrado | RF-01 |
| TC-010 | productos | Búsqueda de producto existente | RF-07 |
| TC-011 | productos | Búsqueda sin resultados | RF-07 |
| TC-012 | productos | Alta de producto válido | RF-07 |
| TC-013 | productos | Alta con precio negativo | RF-07 |
| TC-014 | seguridad | Empleado sin acceso a Reportes (403) | RF-02 |
| TC-015 | seguridad | Usuario anónimo redirigido a login | RF-02, RNF-01 |
| TC-016 | seguridad | Cliente accede a su portal | RF-02, RF-12 |
| TC-017 | rendimiento | Tiempos de carga < 3 s | RNF-05 |
| TC-018 | autenticacion | Mensaje de credenciales inválidas en español | RF-01, RNF-07 |
| TC-019 | productos | Búsqueda sin distinguir mayúsculas | RF-07, RNF-07 |

## Notas importantes

- **Límite de registros (RNF-03):** HGW permite 5 registros públicos por hora por IP (`throttle:5,60`).
  Si se supera, los casos de la suite *registro* quedan como **BLOCKED** (no FAIL). Para volver a ejecutarla,
  corre `php artisan cache:clear` en HGW o espera 60 minutos.
- **Contraseña de la Jefa en HGW:** en `.env` de HGW, un valor sin comillas con `#` se corta en el `#`
  (por ejemplo `CambiarEstaClaveAhora#2026` queda como `CambiarEstaClaveAhora`). Usa comillas en ese archivo.
- **Estados:** PASS (cumple lo esperado), FAIL (no cumple o hubo una excepción), BLOCKED (falta una precondición externa).
- Cada caso abre su propio navegador, así que las pruebas son independientes entre sí.

## Defectos encontrados por la automatización

| ID | Caso | Descripción | Severidad | Estado |
|----|------|-------------|-----------|--------|
| BUG-001 | TC-016 | Portal del cliente con error 500 (restricción `recommendation_type` en PostgreSQL) | Alta | Cerrado (retest PASS) |
| BUG-002 | TC-018 | Mensaje de credenciales inválidas en inglés | Baja | Cerrado (retest PASS) |
| BUG-003 | TC-019 | La búsqueda de productos distingue mayúsculas ("vitaloe" no encuentra "Vitaloe") | Media | Cerrado (retest PASS) |
| OBS-01 | — | En `.env`, `JEFA_PASSWORD` con `#` sin comillas se trunca y la clave documentada no funciona | Baja | Abierto (configuración) |

Las correcciones están en `docs/correcciones_hgw/` (aplicar en HGW, rama `rediseno-ui`, con `git am docs/correcciones_hgw/*.patch`).

> Nota (RNF-03): HGW limita el registro público a 5 por hora. Si TC-006 a TC-009 salen BLOCKED con HTTP 429,
> ejecutar `php artisan cache:clear` en HGW y volver a correr.
