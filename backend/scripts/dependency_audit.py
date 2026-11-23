"""Query public OSV advisories for pinned package names/versions; no source or secrets sent."""

import argparse
import json
import re
import ssl
from datetime import datetime, timezone
from pathlib import Path

import httpx
import truststore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", default=str(Path(__file__).parents[1] / "requirements.lock.txt"))
    parser.add_argument("--report", default="artifacts/python-security-audit.json")
    args = parser.parse_args()
    packages = []
    for line in Path(args.lock).read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^;\s]+)", line)
        if match:
            packages.append(match.groups())
    with httpx.Client(timeout=45, verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as client:
        response = client.post(
            "https://api.osv.dev/v1/querybatch",
            json={
                "queries": [
                    {"package": {"name": name, "ecosystem": "PyPI"}, "version": version}
                    for name, version in packages
                ]
            },
        )
        response.raise_for_status()
        results = response.json()["results"]
    if len(results) != len(packages):
        raise RuntimeError("Incomplete advisory response; no clean audit can be claimed")
    findings = [
        {
            "package": name,
            "version": version,
            "advisories": sorted(v["id"] for v in row.get("vulns", [])),
        }
        for (name, version), row in zip(packages, results)
        if row.get("vulns")
    ]
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "packages_checked": len(packages),
        "source": "https://api.osv.dev/v1/querybatch",
        "findings": findings,
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
