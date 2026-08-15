"""Prueba de carga / estabilidad — simula N usuarios concurrentes con
credenciales reales navegando la plataforma (login + lectura de datos).

No ejecuta el solver (eso es una prueba distinta y mucho más pesada) —
mide cuántos usuarios simultáneos aguanta la API antes de degradarse.

Uso (desde la carpeta backend, con el venv activado):
    pip install locust
    locust -f locustfile.py --host http://<IP>:8000 \
        --users 20 --spawn-rate 5 --run-time 3m --headless \
        --csv=resultados_carga

Sube --users progresivamente (20, 50, 100...) entre corridas para
encontrar el punto donde empiezan a aparecer fallos o la latencia se
dispara.
"""
from __future__ import annotations

import random

from locust import HttpUser, between, task

CREDENTIALS = [
    ("director@udemo.edu", "director123"),
    ("coordinador@udemo.edu", "coordinador123"),
]


class HorarioUser(HttpUser):
    """Un usuario autenticado navegando la plataforma."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        email, password = random.choice(CREDENTIALS)
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="/api/v1/auth/login",
        )
        if resp.status_code != 200:
            self.environment.runner.quit()
            return
        token = resp.json()["data"]["tokens"]["accessToken"]
        self.headers = {"Authorization": f"Bearer {token}"}

        insts = self.client.get(
            "/api/v1/institutions", headers=self.headers
        ).json().get("data") or []
        self.institution_id = insts[0]["id"] if insts else None

    @task(3)
    def health(self) -> None:
        self.client.get("/health")

    @task(2)
    def me(self) -> None:
        self.client.get("/api/v1/auth/me", headers=self.headers)

    @task(2)
    def institutions(self) -> None:
        self.client.get("/api/v1/institutions", headers=self.headers)

    @task(3)
    def dashboard(self) -> None:
        if self.institution_id:
            self.client.get(
                f"/api/v1/institutions/{self.institution_id}/dashboard",
                headers=self.headers,
                name="/api/v1/institutions/[id]/dashboard",
            )
