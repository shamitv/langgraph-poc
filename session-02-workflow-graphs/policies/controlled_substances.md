# Policy: Controlled Substances

**Policy ID:** POL-CS-001  
**Version:** 1.0  
**Effective Date:** 2026-01-01  
**Category:** Medication  

## Scope

This policy applies to all controlled substances including but not limited to:
- **Opioids:** oxycodone, hydrocodone, morphine, fentanyl, codeine, tramadol
- **Benzodiazepines:** alprazolam, diazepam, lorazepam, clonazepam
- **Stimulants:** amphetamine, methylphenidate
- **Other Schedule II-V substances**

**Keywords to match:** oxycodone, opioid, controlled, hydrocodone, morphine, fentanyl, codeine, tramadol, benzodiazepine, alprazolam, schedule II, schedule III, schedule IV

## Rules

### Rule CS-1: Telehealth Prohibition
- **Condition:** Request involves controlled substance AND requested visit type is telehealth
- **Outcome:** `BLOCKED`
- **Violation Message:** "Controlled substance requests are not permitted via telehealth. In-person evaluation is required."
- **Rationale:** DEA regulations and organizational policy require in-person assessment for controlled substance initiation or refill.

### Rule CS-2: Identity Verification Required
- **Condition:** Any controlled substance request (regardless of visit type)
- **Outcome:** `REQUIRES_REVIEW`
- **Requirement:** "Verify patient identity using controlled-substance protocol before scheduling."
- **Rationale:** Identity verification prevents prescription fraud.

### Rule CS-3: Clinician Assessment Mandatory
- **Condition:** Any controlled substance request
- **Outcome:** `REQUIRES_REVIEW`
- **Requirement:** "Clinician assessment required; schedule with MD/DO only (no NP/PA for new controlled substance)."
- **Rationale:** Initial controlled substance prescriptions require physician-level evaluation in many states.

## Decision Matrix

| Request | Visit Type | Has Prior Rx | Outcome |
|---------|------------|--------------|---------|
| Oxycodone refill | Telehealth | Yes | BLOCKED |
| Oxycodone refill | In-person | Yes | REQUIRES_REVIEW |
| New opioid request | Telehealth | No | BLOCKED |
| New opioid request | In-person | No | REQUIRES_REVIEW |

## Compliant Alternatives

When a controlled substance request is BLOCKED, suggest:
1. Schedule an in-person visit with the patient's primary care provider
2. If urgent pain management needed, recommend urgent care or ER evaluation
3. Discuss non-controlled alternatives with clinician (NSAIDs, physical therapy referral)
