from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Panel ejecutivo de la Jefa y elementos comunes del layout autenticado."""
    PATH = "/jefa/dashboard"
    HEADER_TEXT = "Panel ejecutivo"  # título del panel tras el rediseño (rama rediseno-ui)
    SIDEBAR_PRODUCTS = (By.CSS_SELECTOR, "a[href$='/products']")
    SIDEBAR_REPORTS = (By.CSS_SELECTOR, "a[href$='/reports']")
    LOGOUT_FORM = (By.CSS_SELECTOR, "form[action$='/logout']")

    def logout(self):
        self.driver.execute_script("arguments[0].submit();", self.find(self.LOGOUT_FORM))
        self.wait_for_page()
