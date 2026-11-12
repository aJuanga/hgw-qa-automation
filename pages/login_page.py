from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login"
    EMAIL = (By.NAME, "email")
    PASSWORD = (By.NAME, "password")
    REMEMBER = (By.ID, "remember_me")
    SUBMIT = (By.CSS_SELECTOR, "form[action$='/login'] button[type='submit']")
    FORGOT_LINK = (By.XPATH, "//a[contains(@href,'forgot-password')]")
    ERROR_MESSAGE = "Error al iniciar sesión"  # versión anterior de la vista
    FIELD_ERROR = (By.CSS_SELECTOR, "#f-email-error, .hgw-field-error[role='alert']")

    def error_text(self):
        """Mensaje de error de credenciales (rediseño: debajo del campo correo)."""
        els = self.driver.find_elements(*self.FIELD_ERROR)
        return " ".join(" ".join((e.get_attribute("textContent") or "").split()) for e in els).strip()

    def login(self, email, password):
        self.type(self.EMAIL, email)
        self.type(self.PASSWORD, password)
        form = self.find(self.EMAIL)
        self.click(self.SUBMIT)
        try:  # espera a que el navegador cargue la respuesta del servidor
            self.wait.until(EC.staleness_of(form))
        except Exception:
            pass  # validación HTML5: el formulario no se envía
        self.wait_for_page()

    def validation_message(self, locator):
        """Mensaje de validación HTML5 del navegador (campo requerido, formato, etc.)."""
        return self.find(locator).get_attribute("validationMessage") or ""
