# Validators v1 — three-state outcome: accept | needs_review | reject

import re

# Known precise regulation references to accept immediately
KNOWN_REGS = ["411.3.3", "643.3", "134.1.1"]

# Keyword signals that indicate a verification/inspection concept (needs human review)
KEYWORD_SIGNALS = [
    "verification",
    "inspection",
    "testing",
    "extent of installation",
    "extent",
    "origin",
    "circuit origin",
    "protective",
    "new work",
    "alteration",
    "addition",
    "minor works",
    "minor works certificate",
    "certificate",
    "periodic",
    "in-service",
    "in service",
    "condition reporting",
    "bond",
    "bonding",
    "earthing",
    "earth",
    "earth leakage",
    "rcd",
    "30ma",
    "30 mA",
    "r1+",
    "r1 + r2",
    "fault loop",
    "z s",
    "zs",
    "r1",
]


def find_regulation(claim_text: str):
    # look for explicit patterns like 411.3.3 or 132.16
    m = re.search(r"\b\d{1,3}(?:\.\d+)+\b", claim_text)
    if m:
        return m.group(0)
    # fall back to KNOWN_REGS
    for r in KNOWN_REGS:
        if r in claim_text:
            return r
    return None


def find_signals(claim_text: str):
    text = claim_text.lower()
    signals = []
    for k in KEYWORD_SIGNALS:
        if k in text:
            signals.append(k)
    return signals


def simple_validate(claim_text: str):
    claim_text = (claim_text or "").strip()
    if not claim_text:
        return {"status": "reject", "reason": "empty claim"}

    reg = find_regulation(claim_text)
    if reg:
        return {"status": "accept", "regulation": reg}

    signals = find_signals(claim_text)
    if signals:
        return {"status": "needs_review", "signals": signals}

    return {"status": "reject", "reason": "no matching regulation or verification signals found"}
