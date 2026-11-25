"""Vista en vivo: el runner muestra la pantalla del HGW y cada validación mientras se prueba."""
import threading
import time

LIVE = {"driver": None, "frame": None, "case": "", "steps": [], "on": False}


def set_case(driver, titulo):
    LIVE.update(driver=driver, case=titulo)
    LIVE["steps"].append({"t": "case", "txt": titulo})


def step(ok, txt):
    LIVE["steps"].append({"t": "ok" if ok else "ko", "txt": txt})
    LIVE["steps"][:] = LIVE["steps"][-60:]


def info(txt):
    LIVE["steps"].append({"t": "info", "txt": txt})


def _loop():
    while LIVE["on"]:
        d = LIVE["driver"]
        if d is not None:
            try:
                LIVE["frame"] = d.get_screenshot_as_base64()
            except Exception:
                pass
        time.sleep(0.7)


def start():
    LIVE.update(on=True, frame=None, case="", steps=[], driver=None)
    threading.Thread(target=_loop, daemon=True).start()


def stop():
    LIVE.update(on=False, driver=None)
