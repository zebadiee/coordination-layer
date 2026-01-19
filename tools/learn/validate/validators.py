# Simple validators for v0

import re

KNOWN_REGS = ["411.3.3", "643.3", "134.1.1"]


def simple_validate(claim_text: str):
    # If the claim contains a known regulation number, accept
    for r in KNOWN_REGS:
        if r in claim_text:
            return {"status": "confirmed", "regulation": r}

    # if claim contains 'RCD' and '30mA' then it's plausibly a rule but mark as needs_review
    if "rcd" in claim_text.lower() and "30ma" in claim_text.lower():
        return {"status": "needs_review", "reason": "mentions RCD and 30mA"}

    # otherwise unknown
    return {"status": "rejected", "reason": "no matching regulation found"}
