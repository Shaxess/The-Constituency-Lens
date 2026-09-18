# aggregator.py - Rolls up raw tagged complaints into ward/issue summaries.
# This is the ONLY thing the public Ward Pulse view and paid reports should
# ever read from - never raw rows. Keeps individual complaints out of
# anything that leaves the internal pipeline.

from collections import defaultdict


def _split_field(value):
    """Splits a comma-separated field like 'market_levy,light' into a clean list."""
    if not value:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


def filter_reviewed(records):
    """
    Drops rows flagged for human verification (unverified named accusations
    of violence). Nothing flagged reaches aggregated or public output until
    a human clears the flag in the sheet by emptying its needs_review cell.

    Returns (clean_records, skipped_count).
    """
    clean = [r for r in records if str(r.get("needs_review", "")).strip().upper() != "REVIEW"]
    skipped = len(records) - len(clean)
    return clean, skipped


def aggregate_by_ward(records):
    """
    Takes public-safe records (list of dicts, as returned by
    sheets_client.get_public_safe_data()) and rolls them up by ward.

    Returns a dict shaped like:
    {
        "Ward 02 Okokomaiko": {
            "complaint_count": 3,
            "avg_sentiment": -4.3,
            "top_issues": [("road", 2), ("market_levy", 1)],
            "top_politicians": [("lga_chairman", 1)],
        },
        ...
    }
    """
    ward_data = defaultdict(lambda: {
        "complaint_count": 0,
        "sentiment_scores": [],
        "issue_counts": defaultdict(int),
        "politician_counts": defaultdict(int),
    })

    for row in records:
        ward = row.get("ward", "Unknown")
        bucket = ward_data[ward]

        bucket["complaint_count"] += 1

        # sentiment_score is stored as a string in the sheet - convert safely
        try:
            score = float(row.get("sentiment_score", 0))
        except (ValueError, TypeError):
            score = 0
        bucket["sentiment_scores"].append(score)

        for issue in _split_field(row.get("issues", "")):
            bucket["issue_counts"][issue] += 1

        for politician in _split_field(row.get("politicians_mentioned", "")):
            bucket["politician_counts"][politician] += 1

    # Build the final clean summary
    summary = {}
    for ward, bucket in ward_data.items():
        scores = bucket["sentiment_scores"]
        avg_sentiment = round(sum(scores) / len(scores), 2) if scores else 0

        top_issues = sorted(bucket["issue_counts"].items(), key=lambda x: -x[1])
        top_politicians = sorted(bucket["politician_counts"].items(), key=lambda x: -x[1])

        summary[ward] = {
            "complaint_count": bucket["complaint_count"],
            "avg_sentiment": avg_sentiment,
            "top_issues": top_issues,
            "top_politicians": top_politicians,
        }

    return summary


def aggregate_by_issue(records):
    """
    Same idea, rolled up by issue instead of ward - useful for
    'what's the biggest problem across all of Ojo right now' views.
    """
    issue_data = defaultdict(lambda: {"count": 0, "sentiment_scores": []})

    for row in records:
        try:
            score = float(row.get("sentiment_score", 0))
        except (ValueError, TypeError):
            score = 0

        for issue in _split_field(row.get("issues", "")):
            issue_data[issue]["count"] += 1
            issue_data[issue]["sentiment_scores"].append(score)

    summary = {}
    for issue, bucket in issue_data.items():
        scores = bucket["sentiment_scores"]
        avg_sentiment = round(sum(scores) / len(scores), 2) if scores else 0
        summary[issue] = {
            "count": bucket["count"],
            "avg_sentiment": avg_sentiment,
        }

    return dict(sorted(summary.items(), key=lambda x: -x[1]["count"]))


if __name__ == "__main__":
    # Standalone test against real sheet data
    from sheets_client import get_client, get_sheet, get_public_safe_data

    client = get_client()
    sheet = get_sheet(client)
    records = get_public_safe_data(sheet)

    print(f"\nLoaded {len(records)} public-safe rows")

    records, skipped = filter_reviewed(records)
    if skipped:
        print(f"Held back {skipped} row(s) flagged for review - excluded from all aggregates.")
    print(f"Aggregating {len(records)} cleared rows\n")

    # Leak check - confirm no internal fields snuck through
    if records:
        assert not any(f in records[0] for f in ("author", "link")), \
            "Leak detected: internal-only field present in aggregator input"
        print("Leak check passed - no author/link fields present.\n")

    print("=== BY WARD ===")
    ward_summary = aggregate_by_ward(records)
    for ward, data in ward_summary.items():
        print(f"\n{ward}")
        print(f"  Complaints: {data['complaint_count']}")
        print(f"  Avg sentiment: {data['avg_sentiment']}")
        print(f"  Top issues: {data['top_issues']}")
        print(f"  Top politicians: {data['top_politicians']}")

    print("\n=== BY ISSUE (LGA-wide) ===")
    issue_summary = aggregate_by_issue(records)
    for issue, data in issue_summary.items():
        print(f"  {issue}: {data['count']} complaints, avg sentiment {data['avg_sentiment']}")