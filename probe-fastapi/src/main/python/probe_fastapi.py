"""Зонд: работает ли учебный FastAPI на Android (Chaquopy)."""
import json
import socket
import threading
import time
import traceback
import urllib.request


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run():
    res = {}
    try:
        import fastapi
        import pydantic
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        res["fastapi"] = fastapi.__version__
        res["pydantic"] = pydantic.VERSION if hasattr(pydantic, "VERSION") else pydantic.__version__

        app = FastAPI()

        class Item(BaseModel):
            name: str
            price: float

        db = {}

        @app.get("/items/{item_id}")
        def get_item(item_id: int):
            if item_id not in db:
                raise HTTPException(status_code=404, detail="not found")
            return db[item_id]

        @app.post("/items/{item_id}", status_code=201)
        def put_item(item_id: int, item: Item):
            db[item_id] = item.dict() if hasattr(item, "dict") else item.model_dump()
            return db[item_id]

        c = TestClient(app)
        res["post"] = c.post("/items/1", json={"name": "чай", "price": 2.5}).status_code
        res["get"] = c.get("/items/1").json()
        res["notFound"] = c.get("/items/9").status_code
        res["validation"] = c.post("/items/2", json={"name": "x"}).status_code
        res["badPath"] = c.get("/items/abc").status_code
        res["testclient"] = "OK"
    except BaseException:  # noqa: BLE001
        res["testclient"] = "FAIL"
        res["error"] = traceback.format_exc()[-3000:]
        return json.dumps(res, ensure_ascii=False)

    # Настоящий сервер на 127.0.0.1 (уровень A песочницы).
    try:
        import uvicorn

        port = _free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        t = threading.Thread(target=server.run, daemon=True)
        t0 = time.monotonic()
        t.start()
        while not server.started and time.monotonic() - t0 < 15:
            time.sleep(0.05)
        res["uvicornStartMs"] = int((time.monotonic() - t0) * 1000)
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/items/1", timeout=5).read().decode()
        res["uvicorn"] = "OK"
        res["uvicornBody"] = body
        server.should_exit = True
        t.join(5)
    except BaseException:  # noqa: BLE001
        res["uvicorn"] = "FAIL"
        res["uvicornError"] = traceback.format_exc()[-2000:]
    return json.dumps(res, ensure_ascii=False)
