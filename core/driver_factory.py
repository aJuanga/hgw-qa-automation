"""Crea el WebDriver según la configuración (Selenium Manager descarga el driver)."""
from selenium import webdriver

from core.config import config


def create_driver():
    w, h = config.window_size.split(",")
    name = config.browser.lower()
    if name == "edge":
        opts = webdriver.EdgeOptions()
    elif name == "firefox":
        opts = webdriver.FirefoxOptions()
    else:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    if config.headless:
        opts.add_argument("--headless=new" if name != "firefox" else "-headless")
    if name == "edge":
        driver = webdriver.Edge(options=opts)
    elif name == "firefox":
        driver = webdriver.Firefox(options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    driver.set_window_size(int(w), int(h))
    driver.set_page_load_timeout(30)
    return driver
