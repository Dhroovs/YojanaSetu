"""Conservative coverage checks over reviewed metadata, never inferred scheme rules."""

from collections import defaultdict
from datetime import date


def coverage_report(sources, max_age_days=365):
    groups, hashes = defaultdict(list), defaultdict(list)
    for source in sources:
        groups[source.scheme_id].append(source)
        hashes[source.content_hash].append(source.source_id)
    schemes = []
    for scheme_id, records in sorted(groups.items()):
        thresholds = defaultdict(set)
        for record in records:
            for rule in record.rules:
                thresholds[(rule.field, rule.operator)].add(str(rule.value))
        conflicts = [
            f"{field}/{op}: differing reviewed values; human reconciliation required"
            for (field, op), values in thresholds.items()
            if len(values) > 1
        ]
        schemes.append(
            {
                "scheme_id": scheme_id,
                "scheme_name": records[0].scheme_name,
                "sources": [
                    {
                        "source_id": r.source_id,
                        "official_url": str(r.official_url),
                        "department": r.department,
                        "document_title": r.document_title,
                        "published_at": str(r.published_at) if r.published_at else None,
                        "retrieved_at": r.retrieved_at.isoformat(),
                        "last_verified_at": str(r.reviewed_at),
                        "content_hash": r.content_hash,
                        "version": r.index_version,
                        "geographic_coverage": r.geographic_coverage,
                        "completeness": r.completeness,
                        "dated": (date.today() - (r.published_at or r.reviewed_at)).days
                        > max_age_days,
                        "missing_fields": [
                            key
                            for key in (
                                "required_documents",
                                "benefits",
                                "application_process",
                                "application_url",
                            )
                            if getattr(r, key) is None
                        ],
                        "application_url_reviewed_at": str(r.application_url_reviewed_at)
                        if r.application_url_reviewed_at
                        else None,
                    }
                    for r in records
                ],
                "potential_conflicts": conflicts,
                "requires_reconciliation": len(records) > 1,
            }
        )
    return {
        "scheme_count": len(schemes),
        "source_count": len(sources),
        "schemes": schemes,
        "duplicate_content": [ids for ids in hashes.values() if len(ids) > 1],
        "notice": "Partial evidence is not complete eligibility. Conflicts require human review.",
    }
