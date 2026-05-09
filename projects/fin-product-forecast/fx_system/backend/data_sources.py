from __future__ import annotations

import csv
import datetime as dt
import io
import json
import urllib.request
import xml.etree.ElementTree as ET


USER_AGENT = "fx-predictor/1.0"


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def fetch_fred_usdcny() -> list[tuple[str, str, str, float]]:
    """Federal Reserve Bank of St. Louis (FRED, official): DEXCHUS."""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS"
    text = _fetch_text(url)
    out: list[tuple[str, str, str, float]] = []
    for row in csv.DictReader(io.StringIO(text)):
        rate = row.get("DEXCHUS", ".")
        if not rate or rate == ".":
            continue
        out.append(("FRED", "USDCNY", row["DATE"], float(rate)))
    return out


def fetch_ecb_usd_cny() -> list[tuple[str, str, str, float]]:
    """European Central Bank (official): EUR base fx reference rates."""
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
    xml_text = _fetch_text(url)
    root = ET.fromstring(xml_text)
    out: list[tuple[str, str, str, float]] = []

    ns = {"gesmes": "http://www.gesmes.org/xml/2002-08-01", "e": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    for cube_t in root.findall(".//e:Cube[@time]", ns):
        ts = cube_t.attrib["time"]
        values = {c.attrib["currency"]: float(c.attrib["rate"]) for c in cube_t.findall("e:Cube", ns)}
        if "USD" in values and "CNY" in values and values["USD"] > 0:
            # ECB gives X per EUR. Convert to CNY per USD.
            usdcny = values["CNY"] / values["USD"]
            out.append(("ECB", "USDCNY", ts, usdcny))
    return out


def fetch_boc_usdcad(days: int = 365) -> list[tuple[str, str, str, float]]:
    """Bank of Canada (official): JSON Valet API."""
    start = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    url = f"https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?start_date={start}"
    raw = _fetch_text(url)
    obj = json.loads(raw)
    out: list[tuple[str, str, str, float]] = []
    for item in obj.get("observations", []):
        v = item.get("FXUSDCAD", {}).get("v")
        if v:
            out.append(("BoC", "USDCAD", item["d"], float(v)))
    return out


def fetch_all_sources() -> tuple[list[tuple[str, str, str, float]], list[str]]:
    rows: list[tuple[str, str, str, float]] = []
    errors: list[str] = []
    for fn in (fetch_fred_usdcny, fetch_ecb_usd_cny, fetch_boc_usdcad):
        try:
            rows.extend(fn())
        except Exception as e:  # noqa: BLE001
            errors.append(f"{fn.__name__}: {e}")
    return rows, errors
