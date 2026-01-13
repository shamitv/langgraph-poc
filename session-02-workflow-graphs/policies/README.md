# Healthcare Policy Documentation

This directory contains policy documents that the healthcare care coordination agent uses to evaluate requests at runtime.

## How It Works

Instead of hardcoded if/else logic, the agent uses a **two-phase policy evaluation**:

### Phase 1: Policy Selection
1. Loads this README.md (policy index)
2. Asks LLM to identify which policies are relevant to the request
3. Returns a list of applicable policy file names

### Phase 2: Policy Evaluation
1. Loads only the selected policy documents
2. Passes them to the LLM along with the request
3. LLM interprets policies and returns a compliance decision

This approach reduces token usage and improves focus by only loading relevant policies.


## Available Policies

| Policy | File | Description |
|--------|------|-------------|
| Controlled Substances | [controlled_substances.md](./controlled_substances.md) | Opioids, Schedule II-V drugs |
| Medication Prescribing | [medication_prescribing.md](./medication_prescribing.md) | Antibiotics, allergy checks |
| Imaging Services | [imaging_services.md](./imaging_services.md) | MRI, CT, prior authorization |
| Patient Consent | [patient_consent.md](./patient_consent.md) | Minors, guardian requirements |
| Visit Type Restrictions | [visit_type_restrictions.md](./visit_type_restrictions.md) | Telehealth vs in-person |

## Policy Document Format

Each policy follows this structure:
- **Policy ID & Version** — For tracking and auditing
- **Scope** — What medications/services/scenarios it applies to
- **Rules** — Specific conditions and outcomes (PASS/REQUIRES_REVIEW/BLOCKED)
- **Examples** — Sample scenarios for clarity

## Modifying Policies

To update a policy:
1. Edit the relevant `.md` file
2. Update the version number
3. Re-run the agent — changes take effect immediately (no code deploy needed)
