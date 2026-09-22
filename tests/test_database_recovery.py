from __future__ import annotations

import base64
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.operations.database_recovery import (
    MAGIC,
    NONCE_SIZE,
    RecoveryError,
    create_backup,
    database_fingerprint,
    database_parts,
    decode_encryption_key,
    decrypt_file,
    encrypt_file,
    same_database,
)


KEY = b"k" * 32

SOURCE_URL = (
    "postgresql+psycopg://source_user:"
    "source_password@db.internal:5432/cgms"
)


def _tamper_manifest_field(
    manifest: Path,
    field: str,
    value: object,
) -> None:
    payload = json.loads(
        manifest.read_text(
            encoding="utf-8"
        )
    )

    payload[field] = value

    manifest.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


class FakePostgresRunner:
    def __init__(self) -> None:
        self.calls: list[
            tuple[str, list[str], str | None]
        ] = []

    def __call__(
        self,
        executable: str,
        args: list[str],
        *,
        database_url: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = list(args)

        self.calls.append(
            (
                executable,
                command,
                database_url,
            )
        )

        if executable == "pg_dump":
            file_arg = next(
                item
                for item in command
                if item.startswith("--file=")
            )

            archive_path = Path(
                file_arg.split("=", 1)[1]
            )

            archive_path.write_bytes(
                b"mock-postgresql-custom-format-archive"
            )

            return subprocess.CompletedProcess(
                [executable, *command],
                0,
                "",
                "",
            )

        if executable == "pg_restore" and "--list" in command:
            return subprocess.CompletedProcess(
                [executable, *command],
                0,
                (
                    "; archive comment\n"
                    "1; 0 0 TABLE public memory postgres\n"
                    "2; 0 0 TABLE DATA public memory postgres\n"
                ),
                "",
            )

        if executable == "pg_restore":
            return subprocess.CompletedProcess(
                [executable, *command],
                0,
                "restore complete",
                "",
            )

        raise AssertionError(
            f"unexpected PostgreSQL tool: {executable}"
        )


def test_database_identity_ignores_credentials() -> None:
    alternate_credentials = (
        "postgresql://different:"
        "credentials@db.internal:5432/cgms"
    )

    different_database = (
        "postgresql://different:"
        "credentials@db.internal:5432/other"
    )

    parts = database_parts(SOURCE_URL)

    assert parts["host"] == "db.internal"
    assert parts["port"] == "5432"
    assert parts["database"] == "cgms"

    assert same_database(
        SOURCE_URL,
        alternate_credentials,
    )

    assert not same_database(
        SOURCE_URL,
        different_database,
    )

    assert database_fingerprint(
        SOURCE_URL
    ) == database_fingerprint(
        alternate_credentials
    )


def test_encryption_key_contract_accepts_padded_and_unpadded(
) -> None:
    padded = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    unpadded = padded.rstrip(
        "="
    )

    assert padded != unpadded

    assert decode_encryption_key(
        padded
    ) == KEY

    assert decode_encryption_key(
        unpadded
    ) == KEY


def test_encryption_key_contract_rejects_invalid_alphabet_without_secret_leak(
) -> None:
    invalid_secret = (
        "not-valid-@@-secret-value"
    )

    with pytest.raises(
        RecoveryError,
        match="not valid URL-safe base64",
    ) as captured:
        decode_encryption_key(
            invalid_secret
        )

    assert (
        invalid_secret
        not in str(
            captured.value
        )
    )


def test_encryption_key_contract_rejects_wrong_decoded_length(
) -> None:
    short_key = (
        base64.urlsafe_b64encode(
            b"short"
        )
        .decode("ascii")
        .rstrip("=")
    )

    with pytest.raises(
        RecoveryError,
        match="exactly 32 bytes",
    ):
        decode_encryption_key(
            short_key
        )


def test_encrypt_decrypt_round_trip(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.dump"
    encrypted = tmp_path / "source.dump.aesgcm"
    restored = tmp_path / "restored.dump"

    source.write_bytes(
        b"CAP-005 governed backup content"
    )

    encrypt_file(
        source,
        encrypted,
        KEY,
    )

    decrypt_file(
        encrypted,
        restored,
        KEY,
    )

    assert restored.read_bytes() == source.read_bytes()
    assert encrypted.read_bytes().startswith(MAGIC)
    assert source.read_bytes() not in encrypted.read_bytes()


def test_encrypted_artifact_tamper_is_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.dump"
    encrypted = tmp_path / "source.dump.aesgcm"
    restored = tmp_path / "restored.dump"

    source.write_bytes(
        b"authenticated recovery material"
    )

    encrypt_file(
        source,
        encrypted,
        KEY,
    )

    damaged = bytearray(
        encrypted.read_bytes()
    )

    damaged[
        len(MAGIC) + NONCE_SIZE
    ] ^= 1

    encrypted.write_bytes(
        damaged
    )

    with pytest.raises(
        RecoveryError,
        match="authentication failed",
    ):
        decrypt_file(
            encrypted,
            restored,
            KEY,
        )

    assert not restored.exists()


def test_create_backup_encrypts_and_removes_plaintext(
    tmp_path: Path,
) -> None:
    runner = FakePostgresRunner()

    created = datetime(
        2026,
        9,
        9,
        9,
        0,
        tzinfo=UTC,
    )

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=created,
        runner=runner,
    )

    assert artifact.is_file()
    assert manifest.is_file()

    assert not any(
        item.name.endswith(".dump.tmp")
        for item in tmp_path.iterdir()
    )

    manifest_text = manifest.read_text(
        encoding="utf-8"
    )

    assert "source_password" not in manifest_text
    assert SOURCE_URL not in manifest_text

    manifest_payload = json.loads(
        manifest_text
    )

    assert manifest_payload["version"] == 2

    manifest_hmac = manifest_payload[
        "manifest_hmac_sha256"
    ]

    assert len(manifest_hmac) == 64
    assert manifest_hmac == manifest_hmac.lower()

    assert any(
        executable == "pg_dump"
        for executable, _, _ in runner.calls
    )


def test_create_backup_failure_cleans_plaintext(
    tmp_path: Path,
) -> None:
    def failing_runner(
        executable: str,
        args: list[str],
        *,
        database_url: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del database_url

        if executable != "pg_dump":
            raise AssertionError(
                "unexpected tool invocation"
            )

        file_arg = next(
            item
            for item in args
            if item.startswith("--file=")
        )

        Path(
            file_arg.split("=", 1)[1]
        ).write_bytes(
            b"partial plaintext archive"
        )

        raise subprocess.CalledProcessError(
            1,
            [executable, *args],
        )

    with pytest.raises(
        subprocess.CalledProcessError
    ):
        create_backup(
            SOURCE_URL,
            tmp_path,
            KEY,
            runner=failing_runner,
        )

    assert list(tmp_path.iterdir()) == []
def test_verify_backup_detects_artifact_corruption(
    tmp_path: Path,
) -> None:
    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    damaged = bytearray(
        artifact.read_bytes()
    )
    damaged[-1] ^= 1
    artifact.write_bytes(damaged)

    from scripts.operations.database_recovery import verify_backup

    with pytest.raises(
        RecoveryError,
        match="encrypted backup SHA-256",
    ):
        verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )



def test_manifest_rejects_unsafe_artifact_name(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    manifest = tmp_path / "bad.json"

    payload = {
        "version": recovery.MANIFEST_VERSION,
        "created_at": "2026-09-09T09:00:00Z",
        "artifact": "../outside.dump.aesgcm",
        "encrypted_sha256": "a" * 64,
        "plaintext_sha256": "b" * 64,
        "source_fingerprint": "c" * 64,
        "archive_entries": 1,
        "rpo_hours": 24,
        "rto_hours": 4,
    }

    payload[
        recovery.MANIFEST_AUTH_FIELD
    ] = recovery._manifest_hmac_sha256(
        payload,
        KEY,
    )

    manifest.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RecoveryError,
        match="artifact name is unsafe",
    ):
        recovery.load_manifest(
            manifest,
            KEY,
        )


def test_restore_rejects_source_target_collision(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import restore_backup

    artifact = tmp_path / "unused.aesgcm"
    manifest = tmp_path / "unused.json"

    alternate_credentials = (
        "postgresql://other:"
        "password@db.internal:5432/cgms"
    )

    def forbidden_runner(
        executable: str,
        args: list[str],
        *,
        database_url: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del executable
        del args
        del database_url

        raise AssertionError(
            "runner must not execute on collision"
        )

    with pytest.raises(
        RecoveryError,
        match="restore target matches",
    ):
        restore_backup(
            artifact,
            manifest,
            KEY,
            source_url=SOURCE_URL,
            target_url=alternate_credentials,
            runner=forbidden_runner,
        )


def test_restore_uses_explicit_target_and_measures_rto(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import restore_backup

    runner = FakePostgresRunner()

    target_url = (
        "postgresql+psycopg://restore_user:"
        "restore_password@restore.internal:5432/cgms_restore"
    )

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    ticks = iter([100.0, 103.5])

    result = restore_backup(
        artifact,
        manifest,
        KEY,
        source_url=SOURCE_URL,
        target_url=target_url,
        runner=runner,
        clock=lambda: next(ticks),
    )

    assert result["elapsed_seconds"] == 3.5
    assert result["within_rto"] is True

    restore_calls = [
        call
        for call in runner.calls
        if call[0] == "pg_restore"
        and "--list" not in call[1]
    ]

    assert len(restore_calls) == 1
    assert restore_calls[0][2] == target_url


def test_restore_reports_rto_breach(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import restore_backup

    runner = FakePostgresRunner()

    target_url = (
        "postgresql+psycopg://restore_user:"
        "restore_password@restore.internal:5432/cgms_restore"
    )

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        rto_hours=1,
        runner=runner,
    )

    ticks = iter([0.0, 3601.0])

    result = restore_backup(
        artifact,
        manifest,
        KEY,
        source_url=SOURCE_URL,
        target_url=target_url,
        runner=runner,
        clock=lambda: next(ticks),
    )

    assert result["rto_hours"] == 1
    assert result["within_rto"] is False
def test_prune_backups_is_dry_run_by_default(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import prune_backups

    runner = FakePostgresRunner()

    older_artifact, older_manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=datetime(
            2026,
            9,
            7,
            9,
            0,
            tzinfo=UTC,
        ),
        runner=runner,
    )

    newer_artifact, newer_manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=datetime(
            2026,
            9,
            8,
            9,
            0,
            tzinfo=UTC,
        ),
        runner=runner,
    )

    result = prune_backups(
        tmp_path,
        key=KEY,
        daily=1,
        weekly=0,
        monthly=0,
    )

    assert result["dry_run"] is True
    assert result["candidate_count"] == 1
    assert result["candidates"] == [
        older_artifact.name
    ]
    assert result["deleted"] == []

    assert older_artifact.exists()
    assert older_manifest.exists()
    assert newer_artifact.exists()
    assert newer_manifest.exists()


def test_prune_backups_deletes_only_candidates_when_enabled(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import prune_backups

    runner = FakePostgresRunner()

    older_artifact, older_manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=datetime(
            2026,
            9,
            7,
            9,
            0,
            tzinfo=UTC,
        ),
        runner=runner,
    )

    newer_artifact, newer_manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=datetime(
            2026,
            9,
            8,
            9,
            0,
            tzinfo=UTC,
        ),
        runner=runner,
    )

    result = prune_backups(
        tmp_path,
        key=KEY,
        daily=1,
        weekly=0,
        monthly=0,
        dry_run=False,
    )

    assert result["dry_run"] is False
    assert result["candidate_count"] == 1
    assert result["deleted"] == [
        older_artifact.name
    ]

    assert not older_artifact.exists()
    assert not older_manifest.exists()

    assert newer_artifact.exists()
    assert newer_manifest.exists()


def test_retention_policy_rejects_all_zero_limits(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import prune_backups

    with pytest.raises(
        RecoveryError,
        match="retain at least one backup",
    ):
        prune_backups(
            tmp_path,
            key=KEY,
            daily=0,
            weekly=0,
            monthly=0,
        )


def test_recovery_status_without_backup_fails_rpo(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import recovery_status

    result = recovery_status(
        tmp_path,
        key=KEY,
        now=datetime(
            2026,
            9,
            9,
            9,
            0,
            tzinfo=UTC,
        ),
        rpo_hours=24,
    )

    assert result["backup_count"] == 0
    assert result["latest_artifact"] is None
    assert result["latest_created_at"] is None
    assert result["age_hours"] is None
    assert result["rpo_hours"] == 24
    assert result["within_rpo"] is False


def test_recovery_status_reports_rpo_met_and_breached(
    tmp_path: Path,
) -> None:
    from scripts.operations.database_recovery import recovery_status

    runner = FakePostgresRunner()

    artifact, _ = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        now=datetime(
            2026,
            9,
            8,
            9,
            0,
            tzinfo=UTC,
        ),
        runner=runner,
    )

    within = recovery_status(
        tmp_path,
        key=KEY,
        now=datetime(
            2026,
            9,
            9,
            8,
            0,
            tzinfo=UTC,
        ),
        rpo_hours=24,
    )

    breached = recovery_status(
        tmp_path,
        key=KEY,
        now=datetime(
            2026,
            9,
            9,
            10,
            0,
            tzinfo=UTC,
        ),
        rpo_hours=24,
    )

    assert within["backup_count"] == 1
    assert within["latest_artifact"] == artifact.name
    assert within["age_hours"] == 23.0
    assert within["within_rpo"] is True

    assert breached["backup_count"] == 1
    assert breached["age_hours"] == 25.0
    assert breached["within_rpo"] is False
def test_cli_does_not_fallback_to_database_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        "DATABASE_URL",
        SOURCE_URL,
    )
    monkeypatch.delenv(
        recovery.BACKUP_URL_ENV,
        raising=False,
    )
    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    result = recovery.main(
        [
            "backup",
            "--backup-dir",
            "unused",
        ]
    )

    captured = capsys.readouterr()

    assert result == 2
    assert recovery.BACKUP_URL_ENV in captured.err
    assert SOURCE_URL not in captured.err
    assert "source_password" not in captured.err


def test_cli_missing_encryption_key_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.operations.database_recovery as recovery

    monkeypatch.setenv(
        recovery.BACKUP_URL_ENV,
        SOURCE_URL,
    )
    monkeypatch.delenv(
        recovery.ENCRYPTION_KEY_ENV,
        raising=False,
    )

    def forbidden_backup(
        *args: object,
        **kwargs: object,
    ) -> tuple[Path, Path]:
        del args
        del kwargs

        raise AssertionError(
            "backup operation must not execute without key"
        )

    monkeypatch.setattr(
        recovery,
        "create_backup",
        forbidden_backup,
    )

    result = recovery.main(
        [
            "backup",
            "--backup-dir",
            "unused",
        ]
    )

    captured = capsys.readouterr()

    assert result == 2
    assert recovery.ENCRYPTION_KEY_ENV in captured.err
    assert "source_password" not in captured.err


def test_cli_prune_defaults_to_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    captured: dict[str, object] = {}

    def fake_prune(
        backup_dir: Path,
        *,
        key: bytes,
        daily: int,
        weekly: int,
        monthly: int,
        dry_run: bool,
    ) -> dict[str, object]:
        captured["backup_dir"] = backup_dir
        captured["key"] = key
        captured["daily"] = daily
        captured["weekly"] = weekly
        captured["monthly"] = monthly
        captured["dry_run"] = dry_run

        return {
            "dry_run": dry_run,
            "total_backups": 0,
            "retained_backups": 0,
            "candidate_count": 0,
            "candidates": [],
            "deleted": [],
        }

    monkeypatch.setattr(
        recovery,
        "prune_backups",
        fake_prune,
    )

    result = recovery.main(
        [
            "prune",
            "--backup-dir",
            "backups",
        ]
    )

    assert result == 0
    assert captured["key"] == KEY
    assert captured["dry_run"] is True


def test_cli_prune_requires_execute_for_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    captured: dict[str, object] = {}

    def fake_prune(
        backup_dir: Path,
        *,
        key: bytes,
        daily: int,
        weekly: int,
        monthly: int,
        dry_run: bool,
    ) -> dict[str, object]:
        del backup_dir
        del key
        del daily
        del weekly
        del monthly

        captured["dry_run"] = dry_run

        return {
            "dry_run": dry_run,
            "total_backups": 2,
            "retained_backups": 1,
            "candidate_count": 1,
            "candidates": ["old.dump.aesgcm"],
            "deleted": ["old.dump.aesgcm"],
        }

    monkeypatch.setattr(
        recovery,
        "prune_backups",
        fake_prune,
    )

    result = recovery.main(
        [
            "prune",
            "--backup-dir",
            "backups",
            "--execute",
        ]
    )

    assert result == 0
    assert captured["dry_run"] is False


def test_cli_restore_requires_explicit_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        recovery.BACKUP_URL_ENV,
        SOURCE_URL,
    )
    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )
    monkeypatch.delenv(
        recovery.RESTORE_URL_ENV,
        raising=False,
    )

    def forbidden_restore(
        *args: object,
        **kwargs: object,
    ) -> dict[str, object]:
        del args
        del kwargs

        raise AssertionError(
            "restore must not execute without target"
        )

    monkeypatch.setattr(
        recovery,
        "restore_backup",
        forbidden_restore,
    )

    result = recovery.main(
        [
            "restore",
            "--artifact",
            "backup.aesgcm",
            "--manifest",
            "backup.aesgcm.json",
        ]
    )

    captured = capsys.readouterr()

    assert result == 2
    assert recovery.RESTORE_URL_ENV in captured.err


def test_cli_restore_rto_breach_returns_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    target_url = (
        "postgresql+psycopg://restore_user:"
        "restore_password@restore.internal:5432/cgms_restore"
    )

    monkeypatch.setenv(
        recovery.BACKUP_URL_ENV,
        SOURCE_URL,
    )
    monkeypatch.setenv(
        recovery.RESTORE_URL_ENV,
        target_url,
    )
    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    captured: dict[str, object] = {}

    def fake_restore(
        artifact: Path,
        manifest_path: Path,
        key: bytes,
        *,
        source_url: str,
        target_url: str,
    ) -> dict[str, object]:
        captured["artifact"] = artifact
        captured["manifest"] = manifest_path
        captured["key"] = key
        captured["source_url"] = source_url
        captured["target_url"] = target_url

        return {
            "elapsed_seconds": 14401.0,
            "rto_hours": 4,
            "within_rto": False,
            "target_fingerprint": "target-fingerprint",
        }

    monkeypatch.setattr(
        recovery,
        "restore_backup",
        fake_restore,
    )

    result = recovery.main(
        [
            "restore",
            "--artifact",
            "backup.aesgcm",
            "--manifest",
            "backup.aesgcm.json",
        ]
    )

    assert result == 2
    assert captured["source_url"] == SOURCE_URL
    assert captured["target_url"] == target_url
    assert captured["key"] == KEY


def test_cli_status_rpo_breach_returns_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    def fake_status(
        backup_dir: Path,
        *,
        key: bytes,
        rpo_hours: int,
    ) -> dict[str, object]:
        del backup_dir

        assert key == KEY

        return {
            "backup_count": 1,
            "latest_artifact": "backup.aesgcm",
            "latest_created_at": "2026-09-08T08:00:00Z",
            "age_hours": 25.0,
            "rpo_hours": rpo_hours,
            "within_rpo": False,
        }

    monkeypatch.setattr(
        recovery,
        "recovery_status",
        fake_status,
    )

    result = recovery.main(
        [
            "status",
            "--backup-dir",
            "backups",
            "--rpo-hours",
            "24",
        ]
    )

    assert result == 2


def test_cli_status_rpo_met_returns_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.operations.database_recovery as recovery

    encoded_key = base64.urlsafe_b64encode(
        KEY
    ).decode("ascii")

    monkeypatch.setenv(
        recovery.ENCRYPTION_KEY_ENV,
        encoded_key,
    )

    def fake_status(
        backup_dir: Path,
        *,
        key: bytes,
        rpo_hours: int,
    ) -> dict[str, object]:
        del backup_dir

        assert key == KEY

        return {
            "backup_count": 1,
            "latest_artifact": "backup.aesgcm",
            "latest_created_at": "2026-09-09T08:00:00Z",
            "age_hours": 1.0,
            "rpo_hours": rpo_hours,
            "within_rpo": True,
        }

    monkeypatch.setattr(
        recovery,
        "recovery_status",
        fake_status,
    )

    result = recovery.main(
        [
            "status",
            "--backup-dir",
            "backups",
            "--rpo-hours",
            "24",
        ]
    )

    assert result == 0
def test_postgres_subprocess_environment_is_sanitized(
    monkeypatch,
) -> None:
    import subprocess

    import scripts.operations.database_recovery as recovery

    ambient = {
        "DATABASE_URL": "postgresql://ambient.example/ambient",
        "CGMS_BACKUP_DATABASE_URL": "postgresql://backup.example/backup",
        "CGMS_RESTORE_DATABASE_URL": "postgresql://restore.example/restore",
        "CGMS_BACKUP_ENCRYPTION_KEY": "ambient-key",
        "PGHOST": "ambient-host",
        "PGHOSTADDR": "203.0.113.10",
        "PGPORT": "9999",
        "PGDATABASE": "ambient-db",
        "PGUSER": "ambient-user",
        "PGPASSWORD": "ambient-password",
        "PGPASSFILE": "ambient-passfile",
        "PGSERVICE": "ambient-service",
        "PGSERVICEFILE": "ambient-service-file",
        "PGOPTIONS": "--ambient-option",
    }

    for name, value in ambient.items():
        monkeypatch.setenv(name, value)

    captured: dict[str, object] = {}

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        captured["env"] = kwargs["env"]
        return subprocess.CompletedProcess(
            command,
            0,
            "",
            "",
        )

    monkeypatch.setattr(
        recovery.subprocess,
        "run",
        fake_run,
    )

    recovery.run_postgres_tool(
        "pg_restore",
        ["--list", "archive.dump"],
    )

    child_env = captured["env"]

    assert isinstance(child_env, dict)

    for name in ambient:
        assert name not in child_env

    explicit_env, database = recovery.postgres_env(
        SOURCE_URL
    )

    assert database == "cgms"
    assert explicit_env["PGHOST"] == "db.internal"
    assert explicit_env["PGPORT"] == "5432"
    assert explicit_env["PGDATABASE"] == "cgms"
    assert explicit_env["PGUSER"] == "source_user"
    assert explicit_env["PGPASSWORD"] == "source_password"

    assert "DATABASE_URL" not in explicit_env
    assert "CGMS_BACKUP_DATABASE_URL" not in explicit_env
    assert "CGMS_RESTORE_DATABASE_URL" not in explicit_env
    assert "CGMS_BACKUP_ENCRYPTION_KEY" not in explicit_env
    assert "PGPASSFILE" not in explicit_env
    assert "PGSERVICE" not in explicit_env
    assert "PGSERVICEFILE" not in explicit_env
    assert "PGOPTIONS" not in explicit_env

def test_manifest_rejects_malformed_sha256_fields(
    tmp_path,
) -> None:
    import scripts.operations.database_recovery as recovery

    valid = {
        "version": recovery.MANIFEST_VERSION,
        "created_at": "2026-09-17T08:00:00Z",
        "artifact": "backup.dump.aesgcm",
        "encrypted_sha256": "a" * 64,
        "plaintext_sha256": "b" * 64,
        "source_fingerprint": "c" * 64,
        "archive_entries": 1,
        "rpo_hours": 24,
        "rto_hours": 4,
    }

    valid[
        recovery.MANIFEST_AUTH_FIELD
    ] = recovery._manifest_hmac_sha256(
        valid,
        KEY,
    )

    malformed = {
        "encrypted_sha256": "A" * 64,
        "plaintext_sha256": "g" * 64,
        "source_fingerprint": "c" * 63,
        recovery.MANIFEST_AUTH_FIELD: "D" * 64,
    }

    for field, value in malformed.items():
        payload = dict(
            valid
        )

        payload[
            field
        ] = value

        if (
            field
            != recovery.MANIFEST_AUTH_FIELD
        ):
            payload[
                recovery.MANIFEST_AUTH_FIELD
            ] = recovery._manifest_hmac_sha256(
                payload,
                KEY,
            )

        manifest = (
            tmp_path
            / f"{field}.json"
        )

        manifest.write_text(
            json.dumps(
                payload
            ),
            encoding="utf-8",
        )

        with pytest.raises(
            recovery.RecoveryError,
            match=field,
        ):
            recovery.load_manifest(
                manifest,
                KEY,
            )


def test_manifest_authentication_field_is_required(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    payload = json.loads(
        manifest.read_text(
            encoding="utf-8"
        )
    )

    payload.pop(
        recovery.MANIFEST_AUTH_FIELD
    )

    manifest.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest is incomplete",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_manifest_authentication_rejects_wrong_key(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest authentication failed",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            b"z" * 32,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_manifest_authentication_rejects_source_fingerprint_tamper(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    _tamper_manifest_field(
        manifest,
        "source_fingerprint",
        "d" * 64,
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest authentication failed",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_manifest_authentication_rejects_created_at_tamper(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    _tamper_manifest_field(
        manifest,
        "created_at",
        "2000-01-01T00:00:00Z",
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest authentication failed",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_manifest_authentication_rejects_rpo_hours_tamper(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    _tamper_manifest_field(
        manifest,
        "rpo_hours",
        2400,
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest authentication failed",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_manifest_authentication_rejects_rto_hours_tamper(
    tmp_path: Path,
) -> None:
    import scripts.operations.database_recovery as recovery

    runner = FakePostgresRunner()

    artifact, manifest = create_backup(
        SOURCE_URL,
        tmp_path,
        KEY,
        runner=runner,
    )

    _tamper_manifest_field(
        manifest,
        "rto_hours",
        400,
    )

    before = len(
        runner.calls
    )

    with pytest.raises(
        RecoveryError,
        match="manifest authentication failed",
    ):
        recovery.verify_backup(
            artifact,
            manifest,
            KEY,
            runner=runner,
        )

    assert len(
        runner.calls
    ) == before


def test_restore_rto_covers_verification_and_flags_post_validation(
    monkeypatch,
    tmp_path,
) -> None:
    import subprocess

    import scripts.operations.database_recovery as recovery

    target_url = (
        "postgresql+psycopg://restore_user:"
        "restore_password@restore.internal:5432/cgms_restore"
    )

    events: list[str] = []
    ticks = iter(
        [
            100.0,
            115.0,
        ]
    )

    def fake_clock() -> float:
        events.append("clock")
        return next(ticks)

    def fake_verify(
        artifact,
        manifest_path,
        key,
        *,
        runner,
    ):
        del artifact
        del manifest_path
        del key
        del runner

        assert events == ["clock"]

        return {
            "source_fingerprint": recovery.database_fingerprint(
                SOURCE_URL
            ),
            "rto_hours": 1,
        }

    def fake_decrypt(
        source,
        destination,
        key,
    ) -> None:
        del source
        del key
        destination.write_bytes(
            b"restore-dump"
        )

    def fake_runner(
        executable: str,
        args,
        *,
        database_url: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        assert executable == "pg_restore"
        assert database_url == target_url
        assert len(args) > 0

        return subprocess.CompletedProcess(
            [executable, *args],
            0,
            "restore complete",
            "",
        )

    monkeypatch.setattr(
        recovery,
        "verify_backup",
        fake_verify,
    )

    monkeypatch.setattr(
        recovery,
        "decrypt_file",
        fake_decrypt,
    )

    result = recovery.restore_backup(
        tmp_path / "unused.dump.aesgcm",
        tmp_path / "unused.json",
        b"k" * 32,
        source_url=SOURCE_URL,
        target_url=target_url,
        runner=fake_runner,
        clock=fake_clock,
    )

    assert result["elapsed_seconds"] == 15.0
    assert result["within_rto"] is True

    assert (
        result["rto_scope"]
        == "verification_decryption_restore"
    )

    assert result["restore_completed"] is True
    assert result["post_restore_validation_required"] is True
    assert result["post_restore_validation_performed"] is False
def test_delete_backup_pair_rolls_back_on_manifest_staging_failure(
    monkeypatch,
    tmp_path,
) -> None:
    from pathlib import Path

    import pytest

    import scripts.operations.database_recovery as recovery

    artifact = tmp_path / "backup.dump.aesgcm"
    manifest = tmp_path / "backup.dump.aesgcm.json"

    artifact.write_bytes(
        b"encrypted-backup"
    )

    manifest.write_text(
        "{}",
        encoding="utf-8",
    )

    original_replace = Path.replace

    def controlled_replace(
        self,
        target,
    ):
        if self == manifest:
            raise OSError(
                "simulated manifest staging failure"
            )

        return original_replace(
            self,
            target,
        )

    monkeypatch.setattr(
        Path,
        "replace",
        controlled_replace,
    )

    with pytest.raises(
        recovery.RecoveryError,
        match="backup prune staging failed",
    ):
        recovery._delete_backup_pair(
            artifact,
            manifest,
        )

    assert artifact.exists()
    assert manifest.exists()

    artifact_tombstone = tmp_path / (
        ".backup.dump.aesgcm.prune"
    )

    manifest_tombstone = tmp_path / (
        ".backup.dump.aesgcm.json.prune"
    )

    assert not artifact_tombstone.exists()
    assert not manifest_tombstone.exists()

def test_restore_passes_explicit_dbname_without_credentials(
    monkeypatch,
    tmp_path,
) -> None:
    import subprocess

    import scripts.operations.database_recovery as recovery

    artifact = tmp_path / "backup.dump.aesgcm"
    manifest = tmp_path / "backup.dump.aesgcm.json"

    artifact.write_bytes(b"encrypted")
    manifest.write_text("{}", encoding="utf-8")

    source_url = (
        "postgresql+psycopg://"
        "source_user:source_secret@source.internal:5432/cgms_source"
    )

    target_url = (
        "postgresql+psycopg://"
        "restore_user:restore_secret@restore.internal:5432/cgms_restore"
    )

    def fake_verify(*args, **kwargs):
        del args
        del kwargs

        return {
            "source_fingerprint": recovery.database_fingerprint(
                source_url
            ),
            "rto_hours": 1,
        }

    def fake_decrypt(
        source,
        destination,
        key,
    ) -> None:
        del source
        del key
        destination.write_bytes(b"restore-dump")

    runner_calls = []

    def fake_runner(
        executable,
        args,
        *,
        database_url=None,
    ):
        runner_calls.append(
            (
                executable,
                list(args),
                database_url,
            )
        )

        return subprocess.CompletedProcess(
            [executable, *args],
            0,
            "",
            "",
        )

    ticks = iter([100.0, 101.0])

    monkeypatch.setattr(
        recovery,
        "verify_backup",
        fake_verify,
    )

    monkeypatch.setattr(
        recovery,
        "decrypt_file",
        fake_decrypt,
    )

    result = recovery.restore_backup(
        artifact,
        manifest,
        b"k" * 32,
        source_url=source_url,
        target_url=target_url,
        runner=fake_runner,
        clock=lambda: next(ticks),
    )

    assert len(runner_calls) == 1

    executable, args, database_url = runner_calls[0]

    assert executable == "pg_restore"
    assert database_url == target_url

    dbname_args = [
        arg
        for arg in args
        if arg.startswith("--dbname=")
    ]

    assert dbname_args == [
        "--dbname=cgms_restore"
    ]

    rendered_args = "\n".join(args)

    assert target_url not in rendered_args
    assert "restore_secret" not in rendered_args
    assert "restore_user" not in rendered_args
    assert "restore.internal" not in rendered_args

    assert result["restore_completed"] is True
    assert result["within_rto"] is True
