from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, Tuple


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _token_set(s: str) -> set:
    return set(re.findall(r"\w+", s.lower()))


def _ratio(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union


def score(prompt: str, expected: str, got: str, kind: str) -> Tuple[float, str]:
    kind = (kind or "").strip().lower()
    try:
        if kind in ("exact", "exact-case"):
            ok = got == expected if kind == "exact-case" else _norm_text(got) == _norm_text(expected)
            return (100.0 if ok else 0.0, kind)
        if kind in ("contains", "substring"):
            ok = _norm_text(expected) in _norm_text(got)
            return (100.0 if ok else 0.0, "contains")
        if kind in ("regex", "re"):
            pat = expected
            m = re.search(pat, got or "", flags=re.IGNORECASE | re.MULTILINE)
            return (100.0 if m else 0.0, f"regex:{'hit' if m else 'miss'}")
        if kind in ("json-equal", "json"):
            eg = json.loads(expected)
            gg = json.loads(got)
            return (100.0 if eg == gg else 0.0, "json-equal")
        if kind in ("number", "approx"):
            # expected may be "value[:tolerance]"
            parts = str(expected).split(":")
            target = float(parts[0])
            tol = float(parts[1]) if len(parts) > 1 else 0.0
            nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", got or "")
            vals = [float(n) for n in nums] if nums else []
            ok = any(abs(v - target) <= tol for v in vals)
            return (100.0 if ok else 0.0, f"approx tol={tol}")
        if kind in ("fuzzy", "bleu", "rouge"):
            r = _ratio(expected, got)
            return (100.0 * r, f"fuzzy={r:.3f}")
    except Exception as e:
        return (0.0, f"grade-error:{e}")
    return (0.0, "unknown-kind")

