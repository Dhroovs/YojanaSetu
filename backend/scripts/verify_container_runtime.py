"""CI-only synthetic smoke test of the existing loopback Compose environment."""

import json
import secrets
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8080"


def request(method, path, body=None, token=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=20) as response:
            status, data = response.status, response.read()
    except HTTPError as error:
        status, data = error.code, error.read()
    if status != expected:
        raise RuntimeError(f"Container route {method} {path}: {status}, expected {expected}")
    return json.loads(data) if data else None


def execute(code):
    subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )


def wait_ready():
    for _ in range(45):
        try:
            request("GET", "/api/ready")
            break
        except (URLError, RuntimeError):
            time.sleep(2)
    else:
        raise RuntimeError("Compose readiness failed")


def main():
    wait_ready()
    with urlopen(BASE + "/", timeout=20) as response:
        assert response.status == 200 and b"<html" in response.read().lower()
    credentials = {"username": "ci-" + secrets.token_hex(8), "password": secrets.token_urlsafe(24)}
    request("POST", "/api/auth/register", {**credentials, "consent": True}, expected=201)
    token = request("POST", "/api/auth/login", credentials)["access_token"]
    assert request("GET", "/api/cases", token=token)["items"] == []
    request("GET", "/api/admin/users", token=token, expected=403)
    request("GET", "/api/cases", expected=401)
    execute(
        "from pathlib import Path; import chromadb; "
        "Path('/app/data/private-documents/ci-synthetic-marker').write_text('SYNTHETIC'); "
        "c=chromadb.PersistentClient(path='/app/data/chroma'); "
        "s=c.get_or_create_collection('ci_runtime_smoke',embedding_function=None); "
        "s.upsert(ids=['synthetic'],embeddings=[[1.,0.,0.]],documents=['SYNTHETIC'])"
    )
    subprocess.run(["docker", "compose", "restart", "backend", "worker"], check=True)
    subprocess.run(["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "180"], check=True)
    wait_ready()
    # Replacement may change the Docker service IP; the proxy must resolve it again.
    subprocess.run(
        ["docker", "compose", "up", "-d", "--no-deps", "--force-recreate", "backend", "worker"],
        check=True,
    )
    wait_ready()
    token = request("POST", "/api/auth/login", credentials)["access_token"]
    execute(
        "from pathlib import Path; import chromadb; "
        "assert Path('/app/data/private-documents/ci-synthetic-marker').read_text()=='SYNTHETIC'; "
        "c=chromadb.PersistentClient(path='/app/data/chroma'); "
        "s=c.get_collection('ci_runtime_smoke',embedding_function=None); "
        "assert s.query(query_embeddings=[[1.,0.,0.]],n_results=1)['ids']==[['synthetic']]"
    )
    request("POST", "/api/auth/logout", token=token, expected=204)
    request("GET", "/api/auth/me", token=token, expected=401)
    services = subprocess.check_output(
        ["docker", "compose", "ps", "--status", "running", "--services"], text=True
    ).splitlines()
    assert set(services) == {"mongo", "backend", "worker", "frontend"}, services
    logs = subprocess.check_output(["docker", "compose", "logs", "--no-color", "worker"], text=True)
    assert "Worker sweep failed" not in logs and "Durable case sweep" in logs
    print("PASS: four Compose services, frontend/proxy/readiness, auth/RBAC/logout,")
    print("Mongo/account, private-file and embedded-vector persistence across service restart.")
    print("Synthetic vector collection only; no official RAG/model or full backup drill claimed.")


if __name__ == "__main__":
    main()
