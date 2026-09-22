from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import unquote, urlparse

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


MAGIC = b"CGMSBK01"
NONCE_SIZE = 12
TAG_SIZE = 16
CHUNK_SIZE = 1024 * 1024
MANIFEST_VERSION = 2

MANIFEST_AUTH_FIELD = "manifest_hmac_sha256"
MANIFEST_AUTH_INFO = b"cgms-cap005-manifest-auth-v2"
MANIFEST_AUTHENTICATED_FIELDS = (
    "version",
    "created_at",
    "artifact",
    "encrypted_sha256",
    "plaintext_sha256",
    "source_fingerprint",
    "archive_entries",
    "rpo_hours",
    "rto_hours",
)

DEFAULT_RPO_HOURS = 24
DEFAULT_RTO_HOURS = 4
DEFAULT_DAILY_RETENTION = 7
DEFAULT_WEEKLY_RETENTION = 4
DEFAULT_MONTHLY_RETENTION = 3


class RecoveryError(RuntimeError):
    """Raised when a governed backup or recovery control fails."""


def database_parts(database_url: str) -> dict[str, str]:
    parsed = urlparse(database_url)

    if not parsed.scheme.startswith("postgresql"):
        raise RecoveryError(
            "only PostgreSQL database URLs are supported"
        )

    database = parsed.path.lstrip("/")

    if not parsed.hostname or not database:
        raise RecoveryError(
            "database URL must include host and database name"
        )

    return {
        "host": parsed.hostname.lower(),
        "port": str(parsed.port or 5432),
        "database": database,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
    }


def database_fingerprint(database_url: str) -> str:
    parts = database_parts(database_url)
    identity = (
        f"{parts['host']}:{parts['port']}/{parts['database']}"
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


_POSTGRES_CHILD_STRIP_ENV = {
    "DATABASE_URL",
    "CGMS_BACKUP_DATABASE_URL",
    "CGMS_RESTORE_DATABASE_URL",
    "CGMS_BACKUP_ENCRYPTION_KEY",
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
    "PGPASSFILE",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGOPTIONS",
}


def _sanitized_postgres_env() -> dict[str, str]:
    env = dict(os.environ)

    for name in _POSTGRES_CHILD_STRIP_ENV:
        env.pop(
            name,
            None,
        )

    return env

def postgres_env(
    database_url: str,
) -> tuple[dict[str, str], str]:
    parts = database_parts(database_url)
    env = _sanitized_postgres_env()

    env["PGHOST"] = parts["host"]
    env["PGPORT"] = parts["port"]
    env["PGDATABASE"] = parts["database"]

    if parts["user"]:
        env["PGUSER"] = parts["user"]

    if parts["password"]:
        env["PGPASSWORD"] = parts["password"]

    return env, parts["database"]


def run_postgres_tool(
    executable: str,
    args: Iterable[str],
    *,
    database_url: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _sanitized_postgres_env()

    if database_url is not None:
        env, _ = postgres_env(database_url)

    return subprocess.run(
        [executable, *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def decode_encryption_key(encoded: str) -> bytes:
    try:
        encoded_bytes = encoded.encode(
            "ascii"
        )

        padded = (
            encoded_bytes
            + b"="
            * (
                -len(encoded_bytes)
                % 4
            )
        )

        key = base64.b64decode(
            padded,
            altchars=b"-_",
            validate=True,
        )

    except (
        UnicodeEncodeError,
        binascii.Error,
        ValueError,
    ) as exc:
        raise RecoveryError(
            "backup encryption key is not valid URL-safe base64"
        ) from exc

    if len(key) != 32:
        raise RecoveryError(
            "backup encryption key must decode to exactly 32 bytes"
        )

    return key


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(CHUNK_SIZE),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def encrypt_file(
    source: Path,
    destination: Path,
    key: bytes,
) -> None:
    if len(key) != 32:
        raise RecoveryError(
            "AES-256-GCM requires a 32-byte key"
        )

    nonce = secrets.token_bytes(NONCE_SIZE)

    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
    ).encryptor()

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with source.open("rb") as src, destination.open("wb") as dst:
        dst.write(MAGIC)
        dst.write(nonce)

        for chunk in iter(
            lambda: src.read(CHUNK_SIZE),
            b"",
        ):
            dst.write(encryptor.update(chunk))

        dst.write(encryptor.finalize())
        dst.write(encryptor.tag)


def decrypt_file(
    source: Path,
    destination: Path,
    key: bytes,
) -> None:
    if len(key) != 32:
        raise RecoveryError(
            "AES-256-GCM requires a 32-byte key"
        )

    size = source.stat().st_size
    minimum_size = len(MAGIC) + NONCE_SIZE + TAG_SIZE

    if size < minimum_size:
        raise RecoveryError(
            "encrypted backup artifact is truncated"
        )

    with source.open("rb") as src:
        if src.read(len(MAGIC)) != MAGIC:
            raise RecoveryError(
                "encrypted backup artifact has an invalid header"
            )

        nonce = src.read(NONCE_SIZE)

        ciphertext_length = (
            size
            - len(MAGIC)
            - NONCE_SIZE
            - TAG_SIZE
        )

        src.seek(size - TAG_SIZE)
        tag = src.read(TAG_SIZE)

        src.seek(
            len(MAGIC) + NONCE_SIZE
        )

        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
        ).decryptor()

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        remaining = ciphertext_length

        try:
            with destination.open("wb") as dst:
                while remaining:
                    chunk = src.read(
                        min(CHUNK_SIZE, remaining)
                    )

                    if not chunk:
                        raise RecoveryError(
                            "encrypted backup artifact ended unexpectedly"
                        )

                    remaining -= len(chunk)
                    dst.write(
                        decryptor.update(chunk)
                    )

                dst.write(
                    decryptor.finalize()
                )

        except InvalidTag as exc:
            destination.unlink(
                missing_ok=True
            )

            raise RecoveryError(
                "encrypted backup authentication failed"
            ) from exc

        except Exception:
            destination.unlink(
                missing_ok=True
            )
            raise


def same_database(
    source_url: str,
    target_url: str,
) -> bool:
    return (
        database_fingerprint(source_url)
        == database_fingerprint(target_url)
    )


def require_distinct_restore_target(
    source_url: str,
    target_url: str,
) -> None:
    if same_database(
        source_url,
        target_url,
    ):
        raise RecoveryError(
            "restore target matches the source database"
        )
Runner = Callable[..., subprocess.CompletedProcess[str]]


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RecoveryError(
            "invalid recovery timestamp"
        ) from exc

    if parsed.tzinfo is None:
        raise RecoveryError(
            "recovery timestamp must be timezone-aware"
        )

    return parsed.astimezone(UTC)


def _require_positive(
    value: int,
    name: str,
) -> int:
    if value <= 0:
        raise RecoveryError(
            f"{name} must be greater than zero"
        )

    return value


def _safe_artifact_name(value: str) -> str:
    candidate = Path(value)

    if (
        candidate.name != value
        or value in {"", ".", ".."}
    ):
        raise RecoveryError(
            "manifest artifact name is unsafe"
        )

    return value


def _manifest_path(
    artifact: Path,
) -> Path:
    return artifact.with_suffix(
        artifact.suffix + ".json"
    )


def _temporary_path(
    directory: Path,
    suffix: str,
) -> Path:
    token = secrets.token_hex(8)
    return directory / f".cgms-{token}{suffix}"


def _write_json_atomic(
    path: Path,
    payload: dict[str, Any],
) -> None:
    temporary = _temporary_path(
        path.parent,
        ".json.tmp",
    )

    try:
        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    finally:
        temporary.unlink(
            missing_ok=True
        )


def _manifest_integer(
    payload: dict[str, Any],
    name: str,
) -> int:
    try:
        value = int(payload[name])
    except (KeyError, TypeError, ValueError) as exc:
        raise RecoveryError(
            f"backup manifest {name} is invalid"
        ) from exc

    return _require_positive(
        value,
        name,
    )


def _manifest_sha256(
    payload: dict[str, Any],
    name: str,
) -> str:
    value = payload.get(
        name
    )

    if not isinstance(
        value,
        str,
    ):
        raise RecoveryError(
            f"backup manifest {name} must be a SHA-256 hex digest"
        )

    if (
        len(value) != 64
        or any(
            character not in "0123456789abcdef"
            for character in value
        )
    ):
        raise RecoveryError(
            f"backup manifest {name} must be a lowercase SHA-256 hex digest"
        )

    return value

def _manifest_authentication_bytes(
    payload: dict[str, Any],
) -> bytes:
    try:
        authenticated = {
            name: payload[name]
            for name in MANIFEST_AUTHENTICATED_FIELDS
        }
    except KeyError as exc:
        raise RecoveryError(
            "backup manifest is incomplete"
        ) from exc

    return json.dumps(
        authenticated,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _manifest_authentication_key(
    key: bytes,
) -> bytes:
    if len(key) != 32:
        raise RecoveryError(
            "backup encryption key must be exactly 32 bytes"
        )

    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=MANIFEST_AUTH_INFO,
    ).derive(key)


def _manifest_hmac_sha256(
    payload: dict[str, Any],
    key: bytes,
) -> str:
    authentication_key = (
        _manifest_authentication_key(
            key
        )
    )

    return hmac.new(
        authentication_key,
        _manifest_authentication_bytes(
            payload
        ),
        hashlib.sha256,
    ).hexdigest()


def _verify_manifest_authentication(
    payload: dict[str, Any],
    key: bytes,
) -> None:
    expected = _manifest_sha256(
        payload,
        MANIFEST_AUTH_FIELD,
    )

    actual = _manifest_hmac_sha256(
        payload,
        key,
    )

    if not hmac.compare_digest(
        actual,
        expected,
    ):
        raise RecoveryError(
            "backup manifest authentication failed"
        )


def load_manifest(
    path: Path,
    key: bytes,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise RecoveryError(
            "backup manifest is unreadable"
        ) from exc

    required = {
        "version",
        "created_at",
        "artifact",
        "encrypted_sha256",
        "plaintext_sha256",
        "source_fingerprint",
        "archive_entries",
        "rpo_hours",
        "rto_hours",
        MANIFEST_AUTH_FIELD,
    }

    if (
        not isinstance(payload, dict)
        or not required.issubset(payload)
    ):
        raise RecoveryError(
            "backup manifest is incomplete"
        )

    if payload["version"] != MANIFEST_VERSION:
        raise RecoveryError(
            "backup manifest version is unsupported"
        )

    _verify_manifest_authentication(
        payload,
        key,
    )

    _safe_artifact_name(
        str(payload["artifact"])
    )
    parse_timestamp(
        str(payload["created_at"])
    )
    _manifest_integer(
        payload,
        "archive_entries",
    )
    _manifest_integer(
        payload,
        "rpo_hours",
    )
    _manifest_integer(
        payload,
        "rto_hours",
    )

    _manifest_sha256(
        payload,
        "encrypted_sha256",
    )
    _manifest_sha256(
        payload,
        "plaintext_sha256",
    )
    _manifest_sha256(
        payload,
        "source_fingerprint",
    )

    return payload


def archive_entry_count(
    archive: Path,
    *,
    runner: Runner = run_postgres_tool,
) -> int:
    result = runner(
        "pg_restore",
        [
            "--list",
            str(archive),
        ],
    )

    entries = [
        line
        for line in result.stdout.splitlines()
        if (
            line.strip()
            and not line.lstrip().startswith(";")
        )
    ]

    if not entries:
        raise RecoveryError(
            "PostgreSQL backup archive contains no parseable entries"
        )

    return len(entries)


def create_backup(
    source_url: str,
    backup_dir: Path,
    key: bytes,
    *,
    now: datetime | None = None,
    rpo_hours: int = DEFAULT_RPO_HOURS,
    rto_hours: int = DEFAULT_RTO_HOURS,
    runner: Runner = run_postgres_tool,
) -> tuple[Path, Path]:
    _require_positive(
        rpo_hours,
        "rpo_hours",
    )
    _require_positive(
        rto_hours,
        "rto_hours",
    )

    created = (
        now or utc_now()
    ).astimezone(UTC)

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stem = (
        f"cgms-{created:%Y%m%dT%H%M%SZ}-"
        f"{secrets.token_hex(4)}"
    )

    plaintext = (
        backup_dir
        / f".{stem}.dump.tmp"
    )

    artifact = (
        backup_dir
        / f"{stem}.dump.aesgcm"
    )

    manifest_path = _manifest_path(
        artifact
    )

    if (
        artifact.exists()
        or manifest_path.exists()
    ):
        raise RecoveryError(
            "backup artifact collision detected"
        )

    try:
        runner(
            "pg_dump",
            [
                "--format=custom",
                "--no-password",
                f"--file={plaintext}",
            ],
            database_url=source_url,
        )

        if (
            not plaintext.exists()
            or plaintext.stat().st_size <= 0
        ):
            raise RecoveryError(
                "pg_dump did not produce a non-empty archive"
            )

        entries = archive_entry_count(
            plaintext,
            runner=runner,
        )

        plaintext_hash = sha256_file(
            plaintext
        )

        encrypt_file(
            plaintext,
            artifact,
            key,
        )

        if (
            not artifact.exists()
            or artifact.stat().st_size <= 0
        ):
            raise RecoveryError(
                "encrypted backup artifact was not created"
            )

        payload: dict[str, Any] = {
            "version": MANIFEST_VERSION,
            "created_at": iso_z(created),
            "artifact": artifact.name,
            "encrypted_sha256": sha256_file(
                artifact
            ),
            "plaintext_sha256": plaintext_hash,
            "source_fingerprint": database_fingerprint(
                source_url
            ),
            "archive_entries": entries,
            "rpo_hours": rpo_hours,
            "rto_hours": rto_hours,
        }

        payload[
            MANIFEST_AUTH_FIELD
        ] = _manifest_hmac_sha256(
            payload,
            key,
        )

        _write_json_atomic(
            manifest_path,
            payload,
        )

        return artifact, manifest_path

    except Exception:
        artifact.unlink(
            missing_ok=True
        )
        manifest_path.unlink(
            missing_ok=True
        )
        raise

    finally:
        plaintext.unlink(
            missing_ok=True
        )


def verify_backup(
    artifact: Path,
    manifest_path: Path,
    key: bytes,
    *,
    runner: Runner = run_postgres_tool,
) -> dict[str, Any]:
    payload = load_manifest(
        manifest_path,
        key,
    )

    if artifact.name != payload["artifact"]:
        raise RecoveryError(
            "backup artifact does not match its manifest"
        )

    if not artifact.is_file():
        raise RecoveryError(
            "encrypted backup artifact is missing"
        )

    if (
        sha256_file(artifact)
        != payload["encrypted_sha256"]
    ):
        raise RecoveryError(
            "encrypted backup SHA-256 verification failed"
        )

    temporary = _temporary_path(
        artifact.parent,
        ".verify.dump",
    )

    try:
        decrypt_file(
            artifact,
            temporary,
            key,
        )

        if (
            sha256_file(temporary)
            != payload["plaintext_sha256"]
        ):
            raise RecoveryError(
                "decrypted backup SHA-256 verification failed"
            )

        entries = archive_entry_count(
            temporary,
            runner=runner,
        )

        if (
            entries
            != _manifest_integer(
                payload,
                "archive_entries",
            )
        ):
            raise RecoveryError(
                "backup archive entry count changed"
            )

        return payload

    finally:
        temporary.unlink(
            missing_ok=True
        )


def restore_backup(
    artifact: Path,
    manifest_path: Path,
    key: bytes,
    *,
    source_url: str,
    target_url: str,
    runner: Runner = run_postgres_tool,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    require_distinct_restore_target(
        source_url,
        target_url,
    )

    started = clock()

    payload = verify_backup(
        artifact,
        manifest_path,
        key,
        runner=runner,
    )

    if (
        database_fingerprint(
            source_url
        )
        != payload["source_fingerprint"]
    ):
        raise RecoveryError(
            "source database does not match backup manifest"
        )

    temporary = _temporary_path(
        artifact.parent,
        ".restore.dump",
    )

    try:
        decrypt_file(
            artifact,
            temporary,
            key,
        )

        _, target_database = postgres_env(target_url)

        runner(
            "pg_restore",
            [
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                f"--dbname={target_database}",
                str(temporary),
            ],
            database_url=target_url,
        )

        elapsed_seconds = max(
            0.0,
            clock() - started,
        )

        rto_hours = _manifest_integer(
            payload,
            "rto_hours",
        )

        return {
            "elapsed_seconds": elapsed_seconds,
            "rto_hours": rto_hours,
            "rto_scope": "verification_decryption_restore",
            "restore_completed": True,
            "post_restore_validation_required": True,
            "post_restore_validation_performed": False,
            "within_rto": (
                elapsed_seconds
                <= rto_hours * 3600
            ),
            "target_fingerprint": database_fingerprint(
                target_url
            ),
        }

    finally:
        temporary.unlink(
            missing_ok=True
        )
def _require_non_negative(
    value: int,
    name: str,
) -> int:
    if value < 0:
        raise RecoveryError(
            f"{name} must not be negative"
        )

    return value


def backup_inventory(
    backup_dir: Path,
    *,
    key: bytes,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for manifest_path in sorted(
        backup_dir.glob(
            "*.dump.aesgcm.json"
        )
    ):
        payload = load_manifest(
            manifest_path,
            key,
        )

        artifact = backup_dir / str(
            payload["artifact"]
        )

        if (
            _manifest_path(artifact)
            != manifest_path
        ):
            raise RecoveryError(
                "backup manifest path does not match its artifact"
            )

        if not artifact.is_file():
            raise RecoveryError(
                "backup manifest references a missing artifact"
            )

        records.append(
            {
                "artifact": artifact,
                "manifest": manifest_path,
                "created_at": parse_timestamp(
                    str(
                        payload[
                            "created_at"
                        ]
                    )
                ),
                "payload": payload,
            }
        )

    records.sort(
        key=lambda item: item[
            "created_at"
        ],
        reverse=True,
    )

    return records


def _bucket_keep_names(
    records: list[dict[str, Any]],
    limit: int,
    bucket: Callable[[datetime], str],
) -> set[str]:
    if limit == 0:
        return set()

    seen: set[str] = set()
    keep: set[str] = set()

    for record in records:
        created = record["created_at"]
        name = record["artifact"].name

        bucket_name = bucket(
            created
        )

        if bucket_name in seen:
            continue

        seen.add(
            bucket_name
        )
        keep.add(
            name
        )

        if len(seen) >= limit:
            break

    return keep


def retention_keep_set(
    records: list[dict[str, Any]],
    *,
    daily: int = DEFAULT_DAILY_RETENTION,
    weekly: int = DEFAULT_WEEKLY_RETENTION,
    monthly: int = DEFAULT_MONTHLY_RETENTION,
) -> set[str]:
    _require_non_negative(
        daily,
        "daily",
    )
    _require_non_negative(
        weekly,
        "weekly",
    )
    _require_non_negative(
        monthly,
        "monthly",
    )

    if daily + weekly + monthly == 0:
        raise RecoveryError(
            "retention policy must retain at least one backup"
        )

    daily_keep = _bucket_keep_names(
        records,
        daily,
        lambda value: value.strftime(
            "%Y-%m-%d"
        ),
    )

    weekly_keep = _bucket_keep_names(
        records,
        weekly,
        lambda value: (
            f"{value.isocalendar().year}-"
            f"W{value.isocalendar().week:02d}"
        ),
    )

    monthly_keep = _bucket_keep_names(
        records,
        monthly,
        lambda value: value.strftime(
            "%Y-%m"
        ),
    )

    return (
        daily_keep
        | weekly_keep
        | monthly_keep
    )


def _delete_backup_pair(
    artifact: Path,
    manifest: Path,
) -> None:
    artifact_tombstone = artifact.with_name(
        f".{artifact.name}.prune"
    )
    manifest_tombstone = manifest.with_name(
        f".{manifest.name}.prune"
    )

    if (
        artifact_tombstone.exists()
        or manifest_tombstone.exists()
    ):
        raise RecoveryError(
            "backup prune tombstone already exists"
        )

    try:
        artifact.replace(
            artifact_tombstone
        )
    except OSError as exc:
        raise RecoveryError(
            "backup prune staging failed"
        ) from exc

    try:
        manifest.replace(
            manifest_tombstone
        )
    except OSError as exc:
        try:
            artifact_tombstone.replace(
                artifact
            )
        except OSError as rollback_exc:
            raise RecoveryError(
                "backup prune staging failed and artifact rollback failed"
            ) from rollback_exc

        raise RecoveryError(
            "backup prune staging failed"
        ) from exc

    try:
        artifact_tombstone.unlink()
        manifest_tombstone.unlink()
    except OSError as exc:
        raise RecoveryError(
            "backup prune deletion failed after pair staging"
        ) from exc

def prune_backups(
    backup_dir: Path,
    *,
    key: bytes,
    daily: int = DEFAULT_DAILY_RETENTION,
    weekly: int = DEFAULT_WEEKLY_RETENTION,
    monthly: int = DEFAULT_MONTHLY_RETENTION,
    dry_run: bool = True,
) -> dict[str, Any]:
    records = backup_inventory(
        backup_dir,
        key=key,
    )

    keep = retention_keep_set(
        records,
        daily=daily,
        weekly=weekly,
        monthly=monthly,
    )

    candidates = [
        record
        for record in records
        if record["artifact"].name not in keep
    ]

    candidate_names = [
        record["artifact"].name
        for record in candidates
    ]

    deleted: list[str] = []

    if not dry_run:
        for record in candidates:
            artifact = record["artifact"]
            manifest = record["manifest"]

            _delete_backup_pair(
                artifact,
                manifest,
            )

            deleted.append(
                artifact.name
            )

    return {
        "dry_run": dry_run,
        "total_backups": len(
            records
        ),
        "retained_backups": len(
            records
        )
        - len(
            candidates
        ),
        "candidate_count": len(
            candidates
        ),
        "candidates": candidate_names,
        "deleted": deleted,
        "daily_retention": daily,
        "weekly_retention": weekly,
        "monthly_retention": monthly,
    }


def recovery_status(
    backup_dir: Path,
    *,
    key: bytes,
    now: datetime | None = None,
    rpo_hours: int = DEFAULT_RPO_HOURS,
) -> dict[str, Any]:
    _require_positive(
        rpo_hours,
        "rpo_hours",
    )

    records = backup_inventory(
        backup_dir,
        key=key,
    )

    if not records:
        return {
            "backup_count": 0,
            "latest_artifact": None,
            "latest_created_at": None,
            "age_hours": None,
            "rpo_hours": rpo_hours,
            "within_rpo": False,
        }

    latest = records[0]
    latest_created = latest[
        "created_at"
    ]

    reference = (
        now or utc_now()
    ).astimezone(UTC)

    age_seconds = max(
        0.0,
        (
            reference
            - latest_created
        ).total_seconds(),
    )

    age_hours = (
        age_seconds / 3600
    )

    return {
        "backup_count": len(
            records
        ),
        "latest_artifact": latest[
            "artifact"
        ].name,
        "latest_created_at": iso_z(
            latest_created
        ),
        "age_hours": age_hours,
        "rpo_hours": rpo_hours,
        "within_rpo": (
            age_hours
            <= rpo_hours
        ),
    }
BACKUP_URL_ENV = "CGMS_BACKUP_DATABASE_URL"
RESTORE_URL_ENV = "CGMS_RESTORE_DATABASE_URL"
ENCRYPTION_KEY_ENV = "CGMS_BACKUP_ENCRYPTION_KEY"


def _required_env(
    name: str,
) -> str:
    value = os.environ.get(
        name,
        "",
    ).strip()

    if not value:
        raise RecoveryError(
            f"required environment variable is not set: {name}"
        )

    return value


def _environment_key() -> bytes:
    return decode_encryption_key(
        _required_env(
            ENCRYPTION_KEY_ENV
        )
    )


def _print_json(
    payload: dict[str, Any],
) -> None:
    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
    )


def _cli_backup(
    args: argparse.Namespace,
) -> int:
    source_url = _required_env(
        BACKUP_URL_ENV
    )
    key = _environment_key()

    artifact, manifest = create_backup(
        source_url,
        args.backup_dir,
        key,
        rpo_hours=args.rpo_hours,
        rto_hours=args.rto_hours,
    )

    _print_json(
        {
            "operation": "backup",
            "artifact": str(
                artifact
            ),
            "manifest": str(
                manifest
            ),
        }
    )

    return 0


def _cli_verify(
    args: argparse.Namespace,
) -> int:
    key = _environment_key()

    payload = verify_backup(
        args.artifact,
        args.manifest,
        key,
    )

    _print_json(
        {
            "operation": "verify",
            "verified": True,
            "artifact": payload[
                "artifact"
            ],
            "created_at": payload[
                "created_at"
            ],
            "archive_entries": payload[
                "archive_entries"
            ],
            "source_fingerprint": payload[
                "source_fingerprint"
            ],
            "rpo_hours": payload[
                "rpo_hours"
            ],
            "rto_hours": payload[
                "rto_hours"
            ],
        }
    )

    return 0


def _cli_restore(
    args: argparse.Namespace,
) -> int:
    source_url = _required_env(
        BACKUP_URL_ENV
    )
    target_url = _required_env(
        RESTORE_URL_ENV
    )
    key = _environment_key()

    result = restore_backup(
        args.artifact,
        args.manifest,
        key,
        source_url=source_url,
        target_url=target_url,
    )

    _print_json(
        {
            "operation": "restore",
            **result,
        }
    )

    if result["within_rto"]:
        return 0

    return 2


def _cli_prune(
    args: argparse.Namespace,
) -> int:
    key = _environment_key()

    result = prune_backups(
        args.backup_dir,
        key=key,
        daily=args.daily,
        weekly=args.weekly,
        monthly=args.monthly,
        dry_run=not args.execute,
    )

    _print_json(
        {
            "operation": "prune",
            **result,
        }
    )

    return 0


def _cli_status(
    args: argparse.Namespace,
) -> int:
    key = _environment_key()

    result = recovery_status(
        args.backup_dir,
        key=key,
        rpo_hours=args.rpo_hours,
    )

    _print_json(
        {
            "operation": "status",
            **result,
        }
    )

    if result["within_rpo"]:
        return 0

    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Governed CGMS PostgreSQL backup "
            "and recovery operations."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    backup = subparsers.add_parser(
        "backup",
        help="create an encrypted PostgreSQL backup",
    )
    backup.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
    )
    backup.add_argument(
        "--rpo-hours",
        type=int,
        default=DEFAULT_RPO_HOURS,
    )
    backup.add_argument(
        "--rto-hours",
        type=int,
        default=DEFAULT_RTO_HOURS,
    )
    backup.set_defaults(
        handler=_cli_backup
    )

    verify = subparsers.add_parser(
        "verify",
        help="verify an encrypted backup",
    )
    verify.add_argument(
        "--artifact",
        type=Path,
        required=True,
    )
    verify.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )
    verify.set_defaults(
        handler=_cli_verify
    )

    restore = subparsers.add_parser(
        "restore",
        help=(
            "restore only to the explicit "
            "CGMS_RESTORE_DATABASE_URL target"
        ),
    )
    restore.add_argument(
        "--artifact",
        type=Path,
        required=True,
    )
    restore.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )
    restore.set_defaults(
        handler=_cli_restore
    )

    prune = subparsers.add_parser(
        "prune",
        help=(
            "evaluate retention; deletion "
            "requires --execute"
        ),
    )
    prune.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
    )
    prune.add_argument(
        "--daily",
        type=int,
        default=DEFAULT_DAILY_RETENTION,
    )
    prune.add_argument(
        "--weekly",
        type=int,
        default=DEFAULT_WEEKLY_RETENTION,
    )
    prune.add_argument(
        "--monthly",
        type=int,
        default=DEFAULT_MONTHLY_RETENTION,
    )
    prune.add_argument(
        "--execute",
        action="store_true",
        help=(
            "perform deletion; without this "
            "flag the command is dry-run only"
        ),
    )
    prune.set_defaults(
        handler=_cli_prune
    )

    status = subparsers.add_parser(
        "status",
        help="evaluate current backup RPO status",
    )
    status.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
    )
    status.add_argument(
        "--rpo-hours",
        type=int,
        default=DEFAULT_RPO_HOURS,
    )
    status.set_defaults(
        handler=_cli_status
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(
        argv
    )

    try:
        return int(
            args.handler(
                args
            )
        )

    except RecoveryError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    except subprocess.CalledProcessError as exc:
        print(
            (
                "ERROR: PostgreSQL utility "
                f"failed with exit code {exc.returncode}"
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )