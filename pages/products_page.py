from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage


class ProductsPage(BasePage):
    """Listado y búsqueda de productos (/products)."""
    PATH = "/products"
    SEARCH = (By.NAME, "search")
    STATUS = (By.NAME, "status")
    SEARCH_BUTTON = (By.XPATH, "//input[@name='search']/ancestor::form//button[@type='submit']")
    CARDS = (By.CSS_SELECTOR, "article[data-product-card]")
    SUCCESS_CREATED = "Producto creado exitosamente"

    def search(self, term):
        self.type(self.SEARCH, term)
        self.submit_and_wait(self.SEARCH_BUTTON)

    def rows_text(self):
        """Texto de cada tarjeta de producto (textContent: no depende de animaciones CSS)."""
        cards = self.driver.find_elements(*self.CARDS)
        return [" ".join(c.get_attribute("textContent").split()) for c in cards]


class ProductFormPage(BasePage):
    """Formulario de creación de productos (/products/create), solo Jefa."""
    PATH = "/products/create"
    NAME = (By.ID, "name")
    CATEGORY = (By.ID, "category_id")
    PRICE = (By.ID, "price")
    COST = (By.ID, "cost")
    PREP_TIME = (By.ID, "preparation_time")
    DESCRIPTION = (By.ID, "description")
    INGREDIENTS = (By.ID, "ingredients")
    SUBMIT = (By.CSS_SELECTOR, "form[action$='/products'] button[type='submit']")

    def fill(self, data):
        self.type(self.NAME, data["name"])
        Select(self.find(self.CATEGORY)).select_by_visible_text(data["category"])
        self.driver.execute_script("arguments[0].value=arguments[1];", self.find(self.PRICE), str(data["price"]))
        if data.get("cost") is not None:
            self.type(self.COST, str(data["cost"]))
        if data.get("preparation_time"):
            self.type(self.PREP_TIME, str(data["preparation_time"]))
        self.type(self.DESCRIPTION, data.get("description", ""))
        self.type(self.INGREDIENTS, data.get("ingredients", ""))

    def submit(self):
        self.submit_and_wait(self.SUBMIT)

    def field_error(self, text):
        return self.contains(text)
