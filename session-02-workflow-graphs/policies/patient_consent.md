# Policy: Patient Consent

**Policy ID:** POL-CON-001  
**Version:** 1.0  
**Effective Date:** 2026-01-01  
**Category:** Administrative / Compliance  

## Scope

This policy covers consent and authorization requirements for:
- **Minors** (patients under 18 years of age)
- **Dependent adults** (patients with legal guardians)
- **Sensitive services** requiring explicit consent

**Keywords to match:** minor, age, guardian, consent, parent, under 18, pediatric, child, dependent, legal guardian

## Rules

### Rule CON-1: Guardian Consent for Minors
- **Condition:** Patient age is under 18 years
- **Outcome:** `REQUIRES_REVIEW`
- **Requirement:** "Guardian consent required for scheduling and communications. Verify guardian contact information."
- **Rationale:** Legal requirement for minors; HIPAA considerations for communication.

### Rule CON-2: Emancipated Minor Exception
- **Condition:** Patient is minor BUT has documented emancipated status
- **Outcome:** `PASS` (with documentation)
- **Note:** "Emancipated minor — may consent independently. Verify documentation on file."
- **Rationale:** Emancipated minors have legal authority to consent.

### Rule CON-3: Mature Minor for Sensitive Services
- **Condition:** Minor patient AND request involves reproductive health, mental health, or substance abuse treatment
- **Outcome:** `REQUIRES_REVIEW`
- **Note:** "Mature minor doctrine may apply for sensitive services. State law varies — verify with compliance."
- **Rationale:** Many states allow minors to consent to certain sensitive services.

### Rule CON-4: Communication Restrictions
- **Condition:** Patient is minor
- **Outcome:** `REQUIRES_REVIEW`
- **Requirement:** "Direct communications (reminders, results, follow-up) must go to guardian unless otherwise authorized."
- **Rationale:** HIPAA and state privacy laws govern minor communications.

## Age Thresholds

| Age | Classification | Consent Requirement |
|-----|---------------|---------------------|
| 0-12 | Pediatric | Guardian required |
| 13-17 | Adolescent | Guardian required (exceptions apply) |
| 18+ | Adult | Self-consent |

## Guardian Verification Checklist

Before scheduling for a minor:
1. [ ] Guardian name and relationship documented
2. [ ] Guardian contact information verified
3. [ ] Guardian consent obtained (verbal or written per protocol)
4. [ ] Communication preferences noted (who receives reminders/results)
