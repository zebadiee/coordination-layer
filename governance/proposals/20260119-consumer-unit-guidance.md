# Proposal: Guidance for consumer unit replacement — condition assessment & certification

**Capture:** `43b83e4ab7a76412` (runs/cu_change_run_20260119T221420Z)

**Summary:**
Introduce a guidance document recommending a condition-based assessment before or alongside certification when replacing or altering consumer units. The guidance scales by installation type and supply characteristics and requires retaining test results and condition findings.

**Proposed guidance (exact text):**

> When replacing or altering a consumer unit, first determine the installation context by reference to a condition-based assessment:
> – Identify the location discipline (domestic, commercial, industrial, or specialised installation).
> – Confirm the supply characteristics (single-phase or three-phase; low-voltage AC within the typical 55–400 V range).
>
> Where the wider installation condition, bonding adequacy, documentation quality, or installation complexity is unclear, a condition report (EICR or equivalent condition assessment) should be used to establish the baseline before or alongside certification of new work.
>
> Verify and document protective measures, including bonding and earthing continuity, appropriate to the identified installation type and supply.
>
> Issue the appropriate certificate for the work undertaken (EIC for new or substantially altered work; Minor Works Certificate only where scope is strictly limited), and retain test results and condition findings as part of the job record.

**Rationale:**
- Uses condition reporting as a decision gate.
- Requires sector classification before certification.
- Handles single vs three-phase clearly without inventing numerical thresholds.
- Aligns with BS 7671 in a non-prescriptive manner.

**Related artifacts:**
- Run: `runs/cu_change_run_20260119T221420Z`
- Proposal artifact: `runs/cu_change_run_20260119T221420Z/proposal_43b83e4ab7a76412/` (contains `proposal.json`, `proposal_note.md`, `pr_pr-ready/`)
- Capture log: `captures/captures.log` (capture_id `43b83e4ab7a76412`)

**Acceptance criteria / next steps:**
- Technical review confirms wording and scope.
- Compliance review confirms non-normative nature.
- Tests added to extractor/validator to recognise condition-report signals.
- Add guidance to guidance namespace and link from relevant CONTRACT.md.

**Suggested reviewers:**
- electrical-team
- compliance-team
- governance

---

*Prepared from capture `43b83e4ab7a76412` by `operator` on 2026-01-19.*
