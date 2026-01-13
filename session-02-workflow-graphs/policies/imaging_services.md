# Policy: Imaging Services

**Policy ID:** POL-IMG-001  
**Version:** 1.0  
**Effective Date:** 2026-01-01  
**Category:** Diagnostic Services  

## Scope

This policy covers advanced diagnostic imaging:
- **MRI** (Magnetic Resonance Imaging)
- **CT** (Computed Tomography) scans
- **PET** scans
- **Nuclear medicine studies**

**Keywords to match:** MRI, CT scan, imaging, radiology, PET scan, nuclear medicine, lumbar spine, brain MRI, contrast

## Rules

### Rule IMG-1: Prior Authorization Required
- **Condition:** Request involves MRI, CT, or PET scan
- **Outcome:** `REQUIRES_REVIEW`
- **Requirement:** "Prior authorization required for imaging under most insurance plans. Verify coverage before scheduling."
- **Rationale:** Most insurers require pre-auth; scheduling without it may result in claim denial.

### Rule IMG-2: Clinical Evaluation First
- **Condition:** Request for imaging WITHOUT prior clinical evaluation documented
- **Outcome:** `REQUIRES_REVIEW`
- **Warning:** "Imaging is typically scheduled after clinical evaluation unless red-flag criteria are met."
- **Rationale:** Clinical assessment helps determine appropriate imaging modality.

### Rule IMG-3: Red-Flag Fast-Track
- **Condition:** Request mentions red-flag symptoms (sudden severe headache, neurological deficits, suspected stroke, trauma, cancer staging)
- **Outcome:** `REQUIRES_REVIEW` (expedited)
- **Requirement:** "Red-flag symptoms detected. Expedited scheduling and clinician notification required."
- **Rationale:** Urgent clinical scenarios may bypass standard scheduling.

### Rule IMG-4: Contrast Allergy Check
- **Condition:** Imaging with contrast AND patient has documented contrast/iodine allergy
- **Outcome:** `REQUIRES_REVIEW`
- **Warning:** "Patient has contrast allergy. Pre-medication protocol or alternative imaging may be required."
- **Rationale:** Contrast reactions can be severe; requires clinical planning.

## Decision Matrix

| Request | Prior Auth | Clinical Eval | Outcome |
|---------|-----------|---------------|---------|
| MRI lumbar spine | Not obtained | Completed | REQUIRES_REVIEW |
| MRI brain (headache) | Not obtained | Not completed | REQUIRES_REVIEW |
| CT head (trauma/ER) | Waived | Emergency | REQUIRES_REVIEW (expedited) |

## Pre-Authorization Checklist

Before scheduling imaging, verify:
1. [ ] Insurance plan identified
2. [ ] Prior authorization submitted or obtained
3. [ ] Clinical indication documented
4. [ ] Contrast allergy status checked
5. [ ] Patient informed of copay/cost-share
