from __future__ import annotations

import re


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "workspace"


def skill_identity(value: str) -> str:
    return slug(value)
