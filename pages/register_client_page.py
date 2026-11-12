from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class RegisterClientPage(BasePage):
    """Formulario público de registro de clientes (/register-client)."""
    PATH = "/register-client"
    NAME = (By.ID, "name")
    EMAIL = (By.ID, "email")
    PHONE = (By.ID, "phone")
    PASSWORD = (By.ID, "password")
    PASSWORD_CONFIRM = (By.NAME, "password_confirmation")
    CI = (By.ID, "ci")
    ADDRESS = (By.ID, "address")
    FIRST_ALLERGY = (By.XPATH, "(//input[@name='allergies[]'])[1]")
    SUBMIT = (By.CSS_SELECTOR, "form[action$='/register-client'] button[type='submit']")
    SUCCESS_TEXT = "¡Registro exitoso!"

    def register(self, data):
        self.type(self.NAME, data["name"])
        self.type(self.EMAIL, data["email"])
        self.type(self.PHONE, data["phone"])
        self.type(self.PASSWORD, data["password"])
        self.type(self.PASSWORD_CONFIRM, data["password_confirmation"])
        if data.get("ci"):
            self.type(self.CI, data["ci"])
        self.type(self.ADDRESS, data["address"])
        if data.get("with_allergy"):
            self.click(self.FIRST_ALLERGY)
        self.submit_and_wait(self.SUBMIT)
