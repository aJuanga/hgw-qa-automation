"""Clase base del patrón Page Object Model (POM).

Agrupa las acciones comunes (abrir, esperar, escribir, hacer clic, leer texto)
para que las páginas concretas solo declaren sus localizadores y acciones de negocio.
"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.config import config


class BasePage:
    PATH = "/"
    BODY = (By.TAG_NAME, "body")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.explicit_wait)

    # --- navegación -------------------------------------------------------
    def open(self, path=None):
        """Abre la página y devuelve el tiempo de carga en segundos."""
        start = time.perf_counter()
        self.driver.get(config.base_url + (path or self.PATH))
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        return round(time.perf_counter() - start, 3)

    @property
    def url(self):
        return self.driver.current_url

    @property
    def title(self):
        return self.driver.title

    # --- esperas y acciones -------------------------------------------------
    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        el = self.wait.until(EC.element_to_be_clickable(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()

    def type(self, locator, text):
        el = self.visible(locator)
        el.clear()
        el.send_keys(text)

    def is_visible(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except Exception:
            return False

    def body_text(self):
        return self.find(self.BODY).text

    def server_error(self):
        """True si el servidor devolvió una página de error (500, Ignition de Laravel, SQLSTATE)."""
        t = self.driver.title or ""
        if any(k in t for k in ("Exception", "SQLSTATE", "Server Error", "500")):
            return True
        src = self.driver.page_source[:20000]
        return "flareapp.io" in src or "Illuminate\\" in src

    def throttled(self):
        """True si el servidor respondió 429 (límite de solicitudes, RNF-03)."""
        t = (self.driver.title or "") + " " + self.body_text()[:200]
        return "Too Many Requests" in t or "429" in (self.driver.title or "")

    def in_dom(self, text):
        """Busca el texto en el HTML recibido (sirve para mensajes flash animados u ocultos)."""
        return text in self.driver.page_source

    def wait_in_dom(self, text, timeout=6):
        """Espera (hasta timeout) a que el texto aparezca en el HTML recibido."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: text in d.page_source)
            return True
        except Exception:
            return False

    def contains(self, text):
        return text in self.body_text()

    def wait_url_contains(self, fragment, timeout=None):
        try:
            WebDriverWait(self.driver, timeout or config.explicit_wait).until(EC.url_contains(fragment))
            return True
        except Exception:
            return False

    def submit_and_wait(self, locator):
        """Hace clic en un botón de envío y espera la nueva página."""
        old = self.find(self.BODY)
        self.click(locator)
        try:
            self.wait.until(EC.staleness_of(old))
        except Exception:
            pass
        self.wait_for_page()

    def wait_for_page(self):
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
