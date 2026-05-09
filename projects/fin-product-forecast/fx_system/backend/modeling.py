from __future__ import annotations

import json
import math
import random
from typing import Sequence


def linreg_predict(series: Sequence[float], horizon: int) -> tuple[float, float, list[float]]:
    n = len(series)
    x = list(range(n))
    mx = sum(x) / n
    my = sum(series) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, series))
    den = sum((xi - mx) ** 2 for xi in x) or 1.0
    slope = num / den
    intercept = my - slope * mx
    preds = [slope * (n + i) + intercept for i in range(1, horizon + 1)]
    return slope, intercept, preds


def returns(series: Sequence[float]) -> list[float]:
    out = []
    for i in range(1, len(series)):
        prev = series[i - 1]
        out.append(0.0 if prev == 0 else series[i] / prev - 1)
    return out


def rolling_vol(rets: Sequence[float], window: int = 10) -> list[float]:
    out = [0.0] * len(rets)
    for i in range(window - 1, len(rets)):
        sample = rets[i - window + 1 : i + 1]
        m = sum(sample) / len(sample)
        v = sum((x - m) ** 2 for x in sample) / len(sample)
        out[i] = math.sqrt(max(v, 0.0))
    return out


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def kmeans2(features: list[tuple[float, float]], seed: int = 42, max_iter: int = 60):
    if len(features) < 8:
        return [0] * len(features), [(0.0, 0.0), (0.0, 0.0)], 0.0

    rng = random.Random(seed)
    c1, c2 = rng.sample(features, 2)

    labels = [0] * len(features)
    for _ in range(max_iter):
        changed = False
        for i, p in enumerate(features):
            l = 0 if _dist(p, c1) <= _dist(p, c2) else 1
            if l != labels[i]:
                labels[i] = l
                changed = True

        g0 = [p for p, l in zip(features, labels) if l == 0]
        g1 = [p for p, l in zip(features, labels) if l == 1]
        if g0:
            c1 = (sum(x for x, _ in g0) / len(g0), sum(y for _, y in g0) / len(g0))
        if g1:
            c2 = (sum(x for x, _ in g1) / len(g1), sum(y for _, y in g1) / len(g1))
        if not changed:
            break

    inertia = 0.0
    for p, l in zip(features, labels):
        c = c1 if l == 0 else c2
        inertia += _dist(p, c) ** 2
    return labels, [c1, c2], inertia


def unsupervised_regimes(series: Sequence[float]) -> dict:
    rets = returns(series)
    vols = rolling_vol(rets, window=10)
    feats = list(zip(rets, vols))
    labels, centers, inertia = kmeans2(feats)
    counts = {0: 0, 1: 0}
    for l in labels:
        counts[l] += 1
    return {
        "centers": centers,
        "counts": counts,
        "inertia": inertia,
        "labels": labels,
    }


def regimes_json(regimes: dict) -> str:
    safe = {
        "centers": regimes["centers"],
        "counts": regimes["counts"],
        "inertia": regimes["inertia"],
    }
    return json.dumps(safe, ensure_ascii=False)
