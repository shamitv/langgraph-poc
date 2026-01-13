# Policy: Medication Prescribing

**Policy ID:** POL-MED-001  
**Version:** 1.0  
**Effective Date:** 2026-01-01  
**Category:** Medication  

## Scope

This policy covers prescribing requirements for:
- **Antibiotics:** amoxicillin, azithromycin, ciprofloxacin, doxycycline, penicillin-class drugs
- **Allergy-sensitive medications:** penicillin, sulfa drugs, cephalosporins

**Keywords to match:** antibiotic, amoxicillin, azithromycin, penicillin, sulfa, cephalosporin, prescription, prescribe

## Rules

### Rule MED-1: Clinician Assessment for Antibiotics
- **Condition:** Request involves antibiotic prescription
- **Outcome:** `REQUIRES_REVIEW`
- **Warning:** "Antibiotics require clinician assessment before prescribing. Direct dispensing without evaluation is not permitted."
- **Rationale:** Antibiotic stewardship; prevent inappropriate antibiotic use.

### Rule MED-2: Allergy Conflict Check
- **Condition:** Requested medication is in penicillin family AND patient has documented penicillin allergy
- **Outcome:** `BLOCKED`
- **Violation Message:** "Potential penicillin allergy conflict detected. Alternative medication must be assessed by clinician."
- **Rationale:** Patient safety; allergic reactions can be life-threatening.

### Rule MED-3: Cross-Reactivity Warning
- **Condition:** Patient has penicillin allergy AND request involves cephalosporin
- **Outcome:** `REQUIRES_REVIEW`
- **Warning:** "Cross-reactivity possible between penicillin and cephalosporins. Clinician review required."
- **Rationale:** ~1-10% cross-reactivity rate requires clinical judgment.

## Decision Matrix

| Request | Patient Allergy | Outcome |
|---------|----------------|---------|
| Amoxicillin | None | REQUIRES_REVIEW |
| Amoxicillin | Penicillin | BLOCKED |
| Azithromycin | Penicillin | REQUIRES_REVIEW |
| Cephalexin | Penicillin | REQUIRES_REVIEW (with warning) |

## Compliant Alternatives

When penicillin-family antibiotic is BLOCKED due to allergy:
1. Suggest clinician evaluate for azithromycin (Z-pack) if appropriate
2. Suggest fluoroquinolone alternatives if clinically indicated
3. Document allergy prominently in scheduling notes
