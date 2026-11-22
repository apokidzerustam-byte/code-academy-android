"""Проверка заданий FastAPI (kind=fastapi) в песочнице ca_runner. В CI fastapi установлен (CA_REQUIRE_FASTAPI=1)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
import ca_runner  # noqa: E402

try:
    import fastapi  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

if not HAVE:
    if os.environ.get("CA_REQUIRE_FASTAPI"):
        raise RuntimeError("fastapi не установлен, а CA_REQUIRE_FASTAPI=1")
    pytest.skip("fastapi не установлен", allow_module_level=True)

APP = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
ITEMS = {1: "чай"}


class Item(BaseModel):
    name: str
    price: float


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in ITEMS:
        raise HTTPException(status_code=404, detail="нет")
    return {"id": item_id, "name": ITEMS[item_id]}


@app.post("/items")
def create(item: Item):
    return {"name": item.name, "double": item.price * 2}
'''

SPEC = {"kind": "fastapi", "cases": [
    {"id": "get", "path": "/items/1", "expected_json": {"id": 1, "name": "чай"}},
    {"id": "404", "path": "/items/2", "expected_status": 404, "expected_json": {"detail": "нет"}},
    {"id": "422", "path": "/items/abc", "expected_status": 422},
    {"id": "post", "method": "POST", "path": "/items", "json": {"name": "сок", "price": 1.5}, "expected_json": {"name": "сок", "double": 3.0}},
    {"id": "bad", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "сок"}, "expected_status": 422},
]}


def check(code, spec=SPEC):
    return json.loads(ca_runner.check(code, json.dumps(spec)))


def test_reference_passes():
    r = check(APP)
    assert r["allPassed"], r


def test_wrong_status_detected():
    r = check(APP.replace("status_code=404", "status_code=400"))
    assert not r["allPassed"]
    case = next(c for c in r["cases"] if c["id"] == "404")
    assert "400" in case["hint"]


def test_handler_exception_reported():
    r = check(APP.replace('return {"id": item_id, "name": ITEMS[item_id]}', "return 1 / 0"))
    assert not r["allPassed"]
    assert "ZeroDivisionError" in next(c for c in r["cases"] if c["id"] == "get")["error"]


def test_missing_app_and_syntax():
    assert "app" in check("x = 1")["loadError"]
    assert "SyntaxError" in check("def f(:\n")["compileError"]


def test_network_still_blocked_in_handler():
    code = APP + '''

@app.get("/net")
def net():
    import socket
    socket.create_connection(("example.com", 80), timeout=2)
    return {"ok": True}
'''
    r = check(code, {"kind": "fastapi", "cases": [{"id": "n", "path": "/net", "expected_json": {"ok": True}}]})
    assert not r["allPassed"]
    assert r["cases"][0].get("error"), r


def test_testclient_in_run_mode():
    code = APP + '''
from fastapi.testclient import TestClient
client = TestClient(app)
r = client.get("/items/1")
print(r.status_code, r.json())
'''
    out = json.loads(ca_runner.run(code, None, "", 4096))
    assert out.get("stdout", "").strip() == "200 {'id': 1, 'name': 'чай'}", out
