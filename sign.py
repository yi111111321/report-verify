"""Signing and validation of scan links.

The QR code carries a report number plus a truncated HMAC of that number.
Without the service secret a link cannot be minted, so a copied QR image cannot
be re-pointed at another report, and hand-written report numbers cannot be
turned into valid links.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

TAG_BYTES = 10  # 10 bytes -> 16 base32 characters


def _tag(secret: str, report_no: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), report_no.encode("utf-8"), hashlib.sha256).digest()[:TAG_BYTES]


def signature(secret: str, report_no: str) -> str:
    """The ``k`` parameter carried by a QR link."""
    return base64.b32encode(_tag(secret, report_no)).decode("ascii").rstrip("=")


def verify(secret: str, report_no: str, candidate: str) -> bool:
    expected = signature(secret, report_no)
    return hmac.compare_digest(expected, candidate.strip().upper())
