# Policy: Visit Type Restrictions

**Policy ID:** POL-VIS-001  
**Version:** 1.0  
**Effective Date:** 2026-01-01  
**Category:** Scheduling  

## Scope

This policy governs when telehealth vs in-person visits are appropriate:
- **Telehealth** — Video or phone consultations
- **In-person** — Physical clinic visits

**Keywords to match:** telehealth, in-person, video visit, phone visit, virtual, remote, clinic visit, office visit

## Rules

### Rule VIS-1: Telehealth Prohibited Services
- **Condition:** Request involves any of the following AND visit type is telehealth:
  - Controlled substance prescribing (see POL-CS-001)
  - Physical examination required (e.g., new patient intake, annual physical)
  - Procedures or injections
  - Lab draws or specimen collection
- **Outcome:** `BLOCKED`
- **Violation Message:** "This service requires an in-person visit. Telehealth is not permitted."
- **Rationale:** Clinical necessity or regulatory requirement.

### Rule VIS-2: Telehealth Encouraged
- **Condition:** Request involves routine follow-up, medication management review, or care coordination
- **Outcome:** `PASS`
- **Note:** "Telehealth is appropriate for this visit type."
- **Rationale:** Convenience for patient; reduces unnecessary clinic utilization.

### Rule VIS-3: Patient Preference Override
- **Condition:** Patient explicitly requests in-person visit for telehealth-eligible service
- **Outcome:** `PASS`
- **Note:** "Patient preference for in-person noted. Schedule accordingly."
- **Rationale:** Patient autonomy.

### Rule VIS-4: Technology Barrier Accommodation
- **Condition:** Patient lacks technology access for telehealth
- **Outcome:** `PASS` (in-person)
- **Note:** "Schedule in-person due to technology limitations."
- **Rationale:** Ensure equitable access to care.

## Visit Type Decision Matrix

| Service | Telehealth OK | In-Person Required |
|---------|--------------|-------------------|
| Chronic condition follow-up | ✅ | Optional |
| Medication review | ✅ | Optional |
| New patient intake | ❌ | Required |
| Annual physical | ❌ | Required |
| Controlled substance | ❌ | Required |
| Post-procedure check | ✅ | Optional |
| Acute complaint (minor) | ✅ | Preferred |
| Procedure/injection | ❌ | Required |

## Hybrid Visit Option

Some visits may be scheduled as "hybrid":
1. Initial telehealth assessment
2. Follow-up in-person if clinically indicated

Document hybrid intent in scheduling notes.
