"""
lab_prep.py — Lab prep script

What it does
------------
1) Creates input and output folders:
   - ./meetings  (input .txt files)
   - ./minutes   (output .json files)

2) Hydrates sample meeting notes (.txt) into ./meetings.

Safe-by-default behavior
------------------------
- If a sample file already exists, it will NOT overwrite it unless you pass --force.
- You can optionally wipe old outputs in ./minutes with --clean-minutes.

Run
---
python tool_prep.py
python tool_prep.py --force
python tool_prep.py --clean-minutes

Tip
---
Run this once before the tool-calling lab script.
"""

from __future__ import annotations

import argparse
from pathlib import Path


SAMPLES: list[tuple[str, str]] = [
    (
        "meeting_001_weekly_eng_sync.txt",
        """Reference date: 2026-01-05
Meeting: Weekly Engineering Sync
Attendees: Rahul, Neha, SRE Oncall

Notes:
- API latency spikes after 6pm IST. Might be batch job related?
- Observed p95 jumps from ~220ms to ~900ms after 18:00.
- Decided: move nightly job from 6pm to 11pm (IST) starting tomorrow.
- Rahul to add dashboard panel for p95 + error rate by tomorrow.
- Neha to check if Redis eviction policy changed in the last deploy.
- Next sync: Friday.
""",
    ),
    (
        "meeting_002_product_roadmap.txt",
        """Reference date: 2026-01-05
Meeting: Product Roadmap Discussion

Transcript snippets:
- PM: "We should ship onboarding v2 this sprint."
- Eng: "Risky unless we drop analytics refactor."
- Decision: onboarding v2 ships this sprint; analytics refactor moved to next sprint.
- Action: Aditi to update Jira epics and sprint board today.
- Action: Mohit to write migration notes for support team (no date mentioned).
""",
    ),
    (
        "meeting_003_incident_postmortem.txt",
        """Reference date: 2026-01-05
Meeting: Incident Postmortem - Export Service

Timeline (UTC):
- 02:10 alert fired
- 02:18 rollback started
- 02:27 recovery confirmed

Discussion:
- Root cause suspected: config flag enabled in prod without canary.
- Decision: enforce change management checklist for prod flags.
- Action: SRE team to add "flag diff" step in deploy pipeline by 2026-01-10.
- Action: Riya to draft a short RCA summary for leadership.
""",
    ),
    (
        "meeting_004_hiring_debrief.txt",
        """Reference date: 2026-01-05
Meeting: Hiring Loop Debrief (Backend Engineer)

Notes:
- Candidate strong in systems, weaker in SQL.
- Team split: 2 "hire", 1 "no hire".
- Decision: request a 30-min SQL exercise before final decision.
- Action: Sameer to prepare SQL exercise and send to recruiter by Wednesday.
- Action: Kavita to schedule follow-up interview.
""",
    ),
    (
        "meeting_005_launch_readiness.txt",
        """Reference date: 2026-01-05
Meeting: Launch Readiness - New Billing UI

Notes:
- Launch date proposed: Jan 20. Marketing says OK; Sales wants Jan 27.
- Decision: soft launch Jan 20, full launch Jan 27.
- Action: Priya to finalize press draft by 2026-01-12.
- Action: Arjun to confirm pricing page copy by 2026-01-14.
- Action: Dev team to implement feature flag + rollback plan. (Owner not specified)
""",
    ),
    (
        "meeting_006_vendor_procurement.txt",
        """Reference date: 2026-01-05
Meeting: Vendor / Procurement - Observability Suite

Notes:
- Vendor offering 15% discount if 2-year commitment.
- We need annual payment option; legal review pending.
- Decision: proceed with 1-year contract only (no 2-year).
- Action: Nitin to request revised quote by Monday.
- Action: Legal to review DPA and share redlines. (No due date)
""",
    ),
    (
        "meeting_007_research_reranker.txt",
        """Reference date: 2026-01-05
Meeting: Research Discussion - Retrieval/Reranker

Notes:
- "Maybe we should try reranker model X" (not finalized)
- "Let's definitely benchmark on dataset Y first" (agreed)
- Action: Anjali to run baseline eval on dataset Y by 2026-01-08.
- "Could also add multilingual tests later" (optional idea)
""",
    ),
    (
        "meeting_008_customer_feedback.txt",
        """Reference date: 2026-01-05
Meeting: Customer Feedback Review

Bullets:
- Top complaints: slow exports, confusing billing labels.
- Decision: exports performance is P0 for next sprint.
- Decision: rename "Usage Units" to "Credits" on invoices.
- Action: Farhan to open performance investigation ticket today.
- Action: Design team to propose invoice wording changes by next Thursday.
""",
    ),
    (
        "meeting_009_leadership_update.txt",
        """Reference date: 2026-01-05
Meeting: Leadership Update

Notes:
- Decision: We will not expand to 2 new countries in Q1. Focus on existing market retention.
- Decision: Budget approved for 2 additional support hires.
- Action: HR to start hiring pipeline. (No date)
- Action: Finance to circulate updated budget sheet by 2026-01-07.
""",
    ),
    (
        "meeting_010_chaos_notes.txt",
        """Reference date: 2026-01-05
Meeting: Misc / Chaos Notes

- decid: stop using old auth endpoint by feb
- ai: update docs + notify integrators
- ai: rotate api keys for partnerX (urgent)
- next meeting maybe Tue?
- also talked about "rate limit errors" after new release
""",
    ),
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text_if_needed(path: Path, content: str, force: bool) -> bool:
    """
    Returns True if file was written/overwritten, False if skipped.
    """
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def clean_minutes_dir(minutes_dir: Path) -> int:
    """
    Remove *.json outputs from minutes_dir. Returns number removed.
    """
    removed = 0
    if minutes_dir.exists() and minutes_dir.is_dir():
        for p in minutes_dir.glob("*.json"):
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def main() -> None:
    # Default root is this script's directory (not CWD)
    script_dir = str(Path(__file__).parent.resolve())
    
    parser = argparse.ArgumentParser(description="Prepare tool-calling lab folders and sample meeting notes.")
    parser.add_argument("--root", default=script_dir, help="Root folder for lab directories (default: script directory).")
    parser.add_argument("--meetings-dir", default="../data/meetings/transcripts", help="Meetings input directory path (default: ../data/meetings/transcripts).")
    parser.add_argument("--minutes-dir", default="../data/meetings/minutes", help="Minutes output directory path (default: ../data/meetings/minutes).")
    parser.add_argument("--force", action="store_true", help="Overwrite existing sample files if they already exist.")
    parser.add_argument(
        "--clean-minutes",
        action="store_true",
        help="Delete existing *.json files in minutes directory before lab run.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    meetings_dir = (root / args.meetings_dir).resolve()
    minutes_dir = (root / args.minutes_dir).resolve()

    ensure_dir(meetings_dir)
    ensure_dir(minutes_dir)

    if args.clean_minutes:
        removed = clean_minutes_dir(minutes_dir)
        print(f"Cleaned {removed} old output file(s) from: {minutes_dir}")

    written = 0
    skipped = 0
    for filename, content in SAMPLES:
        path = meetings_dir / filename
        did_write = write_text_if_needed(path, content, force=args.force)
        if did_write:
            written += 1
        else:
            skipped += 1

    # Optional: add a tiny README for learners
    readme = meetings_dir / "README.txt"
    readme_content = (
        "This folder contains sample meeting notes (*.txt) for the tool-calling lab.\n"
        "The lab script will list these files, read them, and save minutes JSON into ../minutes.\n"
        "You can add your own .txt files here and rerun the lab.\n"
    )
    write_text_if_needed(readme, readme_content, force=False)

    print("\nPrep complete:")
    print(f"  Meetings dir: {meetings_dir}")
    print(f"  Minutes dir : {minutes_dir}")
    print(f"  Sample files written: {written}")
    print(f"  Sample files skipped (already existed): {skipped}")
    print("\nNext: run your tool-calling lab script to process transcripts into minutes.")


if __name__ == "__main__":
    main()
