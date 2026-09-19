"""Thin client for the Elexon BMRS public API."""

from __future__ import annotations

import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT = 120


def _get(path: str, params: dict) -> list[dict]:
    response = requests.get(f"{BASE}{path}", params=params, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return payload.get("data", [])
    return payload


def fetch_units() -> list[dict]:
    """Every BM unit registered in the market."""
    return _get("/reference/bmunits/all", {})


def wind_units() -> dict[str, dict]:
    """Wind units, keyed by Elexon BM unit ID."""
    return {
        u["elexonBmUnit"]: u
        for u in fetch_units()
        if u.get("fuelType") == "WIND" and u.get("elexonBmUnit")
    }


def fetch_boalf(start: str, end: str) -> list[dict]:
    """Bid-offer acceptances: what units were instructed to do."""
    return _get("/datasets/BOALF", {"from": start, "to": end, "format": "json"})


def fetch_pn(unit: str, start: str, end: str) -> list[dict]:
    """Physical notifications: what one unit planned to do."""
    return _get("/balancing/physical",
                {"bmUnit": unit, "dataset": "PN", "from": start, "to": end})


def fetch_bod(unit: str, start: str, end: str) -> list[dict]:
    """Bid-offer prices. pairId -1 is the first reduction band."""
    return _get("/balancing/bid-offer",
                {"bmUnit": unit, "from": start, "to": end})
