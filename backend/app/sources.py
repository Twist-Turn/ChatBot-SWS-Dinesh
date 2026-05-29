"""Filename -> friendly display name for the source-badge UI."""
from __future__ import annotations

FRIENDLY_NAMES: dict[str, str] = {
    "SWS-AI-company-overview.pdf": "Company Overview",
    "SWS-AI-hr-policy.pdf": "HR Policy",
    "SWS-AI-leave-policy.pdf": "Leave Policy",
    "SWS-AI-resignation-policy.pdf": "Resignation & Exit Policy",
    "SWS-AI-code-of-conduct.pdf": "Code of Conduct",
    "SWS-AI-wfh-policy.pdf": "Work From Home Policy",
    "SWS-AI-performance-review.pdf": "Performance Review Policy",
    "SWS-AI-benefits-compensation.pdf": "Benefits & Compensation",
    "SWS-AI-onboarding-guide.pdf": "Employee Onboarding Guide",
    "SWS-AI-it-security-policy.pdf": "IT & Security Policy",
}


def friendly_name(filename: str) -> str:
    if filename in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[filename]
    stem = filename.rsplit(".", 1)[0]
    return stem.replace("-", " ").replace("_", " ").strip().title() or filename
