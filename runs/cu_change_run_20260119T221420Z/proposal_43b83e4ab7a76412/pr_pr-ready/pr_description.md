# Proposal: Guidance for consumer unit replacement — condition assessment & certification (capture 43b83e4ab7a76412)

## Summary

This proposal packages a human-approved capture into a formal guidance artifact for maintainers to review. It recommends introducing a condition-based assessment and clearer certification guidance when replacing or altering consumer units, scaled to installation type and supply characteristics.

## Proposed guidance (exact text)

> When replacing or altering a consumer unit, first determine the installation context by reference to a condition-based assessment:
> – Identify the location discipline (domestic, commercial, industrial, or specialised installation).
> – Confirm the supply characteristics (single-phase or three-phase; low-voltage AC within the typical 55–400 V range).
>
> Where the wider installation condition, bonding adequacy, documentation quality, or installation complexity is unclear, a condition report (EICR or equivalent condition assessment) should be used to establish the baseline before or alongside certification of new work.
>
> Verify and document protective measures, including bonding and earthing continuity, appropriate to the identified installation type and supply.
>
> Issue the appropriate certificate for the work undertaken (EIC for new or substantially altered work; Minor Works Certificate only where scope is strictly limited), and retain test results and condition findings as part of the job record.

## Rationale

- Introduces condition reporting as a decision gate, not an afterthought.  
- Forces sector classification before certification.  
- Explicitly handles single vs three-phase without inventing thresholds.  
- Keeps BS 7671 aligned without quoting Appendix 6 or hard reg numbers.  
- Scales cleanly from domestic to industrial.

## Related artifacts

- Capture: `captures/captures.log` (capture_id: `43b83e4ab7a76412`)  
- Run: `runs/cu_change_run_20260119T221420Z`  
- Proposal JSON: `runs/cu_change_run_20260119T221420Z/proposal_43b83e4ab7a76412/proposal.json`  
- Evidence excerpt: `runs/cu_change_run_20260119T221420Z/evidence/evidence.json`

## Acceptance criteria

- Technical lead confirms wording is accurate and not prescriptive beyond scope.  
- Compliance reviewer confirms the guidance sits as non-normative guidance and does not create unintended regulatory obligations.  
- Extractor/validator test added to ensure future runs recognise "condition report" and sector classification signals.  
- Draft guidance is added to the guidance repository under a specific guidance namespace (or as a guidance document linked from the relevant CONTRACT/MANIFEST).

## Reviewers

- electrical-team  
- compliance-team  
- governance

**Requested reviewers for PR:** `electrical-team`, `compliance`, `governance`

## Review checklist

- [ ] Technical accuracy (electrical-team): confirm the guidance is technically correct and non-prescriptive.
- [ ] Regulatory alignment (compliance): confirm the guidance does not conflict with statutory requirements and is clearly non-normative.
- [ ] Governance approval (governance): confirm acceptance into the guidance namespace and that acceptance criteria are met.

## Labels

- proposal  
- needs-review  
- guidance

---

*Prepared from capture `43b83e4ab7a76412` and validated run `cu_change_run_20260119T221420Z` by `operator`.*
