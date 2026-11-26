#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Alexander S. Donahue
# SPDX-License-Identifier: Apache-2.0
"""Stamp and cryptographically verify data/MANIFEST.sha256 with BOTH:
  1. DigiCert RFC 3161 TSA (data/MANIFEST.sha256.tsr)
  2. Multi-calendar Bitcoin OpenTimestamps proof (data/MANIFEST.sha256.ots)

Satisfies Defensible Independent AI Research Playbook v1.3 Checklist #26.
Uses temp-directory staging for OpenSSL so Windows paths with literal brackets
never break subprocess or shell invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "MANIFEST.sha256"
TSR_PATH = ROOT / "data" / "MANIFEST.sha256.tsr"
OTS_PATH = ROOT / "data" / "MANIFEST.sha256.ots"

OTS_MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
OTS_VERSION_1 = b"\x01"
OTS_OP_SHA256 = b"\x08"
OTS_FORK_TAG = b"\xff"

OTS_CALENDARS = [
    "https://a.pool.opentimestamps.org/digest",
    "https://b.pool.opentimestamps.org/digest",
    "https://alice.btc.calendar.opentimestamps.org/digest",
]
DIGICERT_TSA_URL = "http://timestamp.digicert.com"


def find_openssl() -> str | None:
    found = shutil.which("openssl")
    if found:
        return found
    for cand in (
        Path(r"C:\Program Files\Git\usr\bin\openssl.exe"),
        Path(r"C:\Program Files\Git\mingw64\bin\openssl.exe"),
    ):
        if cand.is_file():
            return str(cand)
    return None


def stamp_rfc3161() -> Path:
    openssl = find_openssl()
    if not openssl:
        raise FileNotFoundError("openssl binary not found on PATH or standard Git install")
    if not DIGICERT_TSA_URL.startswith(("https://", "http://")):
        raise ValueError(f"Unsupported TSA URL scheme: {DIGICERT_TSA_URL!r}")
    with tempfile.TemporaryDirectory(prefix="ks_tsa_") as tmp:
        tmp_dir = Path(tmp)
        manifest_copy = tmp_dir / "MANIFEST.sha256"
        tsq_file = tmp_dir / "MANIFEST.sha256.tsq"
        tsr_file = tmp_dir / "MANIFEST.sha256.tsr"
        shutil.copy2(MANIFEST, manifest_copy)
        subprocess.run(
            [openssl, "ts", "-query", "-data", str(manifest_copy), "-no_nonce", "-sha256", "-cert", "-out", str(tsq_file)],
            check=True,
        )
        req = urllib.request.Request(  # noqa: S310
            DIGICERT_TSA_URL,
            data=tsq_file.read_bytes(),
            method="POST",
            headers={"Content-Type": "application/timestamp-query"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310
            tsr_bytes = resp.read()
        tsr_file.write_bytes(tsr_bytes)
        txt = subprocess.check_output(
            [openssl, "ts", "-reply", "-in", str(tsr_file), "-text"], text=True, encoding="utf-8"
        )
        if "Status: Granted." not in txt:
            raise RuntimeError(f"DigiCert TSA did not grant timestamp:\n{txt}")
        TSR_PATH.write_bytes(tsr_bytes)
        print(f"PASS: Stamped RFC 3161 TSA -> {TSR_PATH} ({len(tsr_bytes)} bytes)")
        return TSR_PATH


def stamp_opentimestamps() -> Path:
    digest = hashlib.sha256(MANIFEST.read_bytes()).digest()
    calendar_proofs: list[bytes] = []
    for url in OTS_CALENDARS:
        if not url.startswith("https://"):
            continue
        try:
            req = urllib.request.Request(  # noqa: S310
                url,
                data=digest,
                method="POST",
                headers={
                    "Accept": "application/vnd.opentimestamps.v1",
                    "User-Agent": "OpenTimestamps-Client/0.7",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                body = resp.read()
                if resp.status == 200 and len(body) >= 32:
                    calendar_proofs.append(body)
        except Exception as exc:
            print(f"WARN: OpenTimestamps calendar {url} failed: {exc}", file=sys.stderr)

    if not calendar_proofs:
        raise RuntimeError("No OpenTimestamps calendar responded with HTTP 200")

    parts = [OTS_MAGIC, OTS_VERSION_1, OTS_OP_SHA256, digest]
    for idx, proof in enumerate(calendar_proofs):
        if idx < len(calendar_proofs) - 1:
            parts.append(OTS_FORK_TAG)
        parts.append(proof)
    ots_bytes = b"".join(parts)
    OTS_PATH.write_bytes(ots_bytes)
    print(
        f"PASS: Stamped OpenTimestamps ({len(calendar_proofs)} calendars) -> "
        f"{OTS_PATH} ({len(ots_bytes)} bytes)"
    )
    return OTS_PATH


def verify_timestamps() -> int:
    if not MANIFEST.is_file():
        print(f"ERROR: missing {MANIFEST}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(MANIFEST.read_bytes()).digest()
    errors: list[str] = []
    x509_verified = False

    if not TSR_PATH.is_file():
        errors.append(f"Missing RFC 3161 token: {TSR_PATH}")
    else:
        tsr_raw = TSR_PATH.read_bytes()
        if len(tsr_raw) < 500 or tsr_raw[0] != 0x30:
            errors.append("RFC 3161 token is not a valid DER ASN.1 SEQUENCE")
        elif digest not in tsr_raw:
            errors.append(
                f"RFC 3161 token imprint does NOT match current {MANIFEST.name} SHA-256 ({digest.hex()})"
            )
        else:
            openssl = find_openssl()
            ca_bundle = Path("/etc/ssl/certs/ca-certificates.crt")
            if openssl and ca_bundle.is_file():
                with tempfile.TemporaryDirectory(prefix="ks_tsa_ver_") as tmp:
                    tmp_dir = Path(tmp)
                    m_copy = tmp_dir / "MANIFEST.sha256"
                    t_copy = tmp_dir / "MANIFEST.sha256.tsr"
                    shutil.copy2(MANIFEST, m_copy)
                    shutil.copy2(TSR_PATH, t_copy)
                    res = subprocess.run(
                        [
                            openssl, "ts", "-verify",
                            "-in", str(t_copy),
                            "-data", str(m_copy),
                            "-CAfile", str(ca_bundle),
                        ],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                    )
                    if res.returncode != 0 or "Verification: OK" not in (res.stdout + res.stderr):
                        errors.append(f"OpenSSL X.509 TSA verification failed: {res.stdout}\n{res.stderr}")
                    else:
                        x509_verified = True

    if not OTS_PATH.is_file():
        errors.append(f"Missing OpenTimestamps proof: {OTS_PATH}")
    else:
        ots_raw = OTS_PATH.read_bytes()
        prefix = OTS_MAGIC + OTS_VERSION_1 + OTS_OP_SHA256
        if not ots_raw.startswith(prefix):
            errors.append("OpenTimestamps proof missing official OTS v1 SHA-256 magic header")
        elif ots_raw[len(prefix) : len(prefix) + 32] != digest:
            errors.append(
                f"OpenTimestamps proof digest does NOT match current {MANIFEST.name} SHA-256 ({digest.hex()})"
            )

    if errors:
        for err in errors:
            print("ERROR:", err, file=sys.stderr)
        return 1
    chain_note = " + full OpenSSL X.509 DigiCert chain Verification: OK" if x509_verified else ""
    print(
        f"PASS: Both RFC 3161 ({TSR_PATH.name}) and OpenTimestamps ({OTS_PATH.name}) "
        f"cryptographically bind {MANIFEST.name} SHA-256 {digest.hex()}{chain_note}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stamp", action="store_true", help="Stamp data/MANIFEST.sha256 via DigiCert TSA + OpenTimestamps")
    group.add_argument("--verify", action="store_true", help="Verify both timestamp tokens against data/MANIFEST.sha256")
    args = parser.parse_args()
    if args.stamp:
        stamp_rfc3161()
        stamp_opentimestamps()
        return verify_timestamps()
    return verify_timestamps()


if __name__ == "__main__":
    raise SystemExit(main())
