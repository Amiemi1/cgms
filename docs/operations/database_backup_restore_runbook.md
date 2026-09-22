# CGMS Database Backup and Restore Runbook

## Purpose

This runbook defines the governed operational procedure for CAP-005 database
backup, integrity verification, retention, recovery-status monitoring and
restore validation.

It applies to staging, pilot and production-like PostgreSQL environments.
It does not authorize a production restore by itself and does not replace
release-specific approval for destructive or schema-changing operations.

## Governing implementation

The governed operator interface is:

    scripts/operations/database_recovery.py

Supported commands are:

    backup
    verify
    restore
    prune
    status

Database credentials and encryption keys must not be supplied as command-line
arguments.

## Recovery service objectives

The pilot recovery contract is:

- Recovery Point Objective (RPO): no more than 24 hours.
- Recovery Time Objective (RTO): no more than 4 hours.
- Backup frequency: at least daily.
- Retention: 7 daily, 4 weekly and 3 monthly recovery points.
- Integrity control: SHA-256 verification is mandatory.
- Encryption control: AES-256-GCM authenticated encryption is mandatory.
- Manifest control: HMAC-SHA256 authentication of governance metadata is mandatory using an HKDF-SHA256-derived subkey.
- Restore validation: at least weekly.
- Restore validation is also mandatory before pilot authorization.
- Restore validation must be repeated after a material schema, PostgreSQL,
  backup-tool or recovery-tool change.

An RPO or RTO breach is a failed recovery control and must not be represented
as a successful readiness result.

## Required environment variables

The recovery operator uses three dedicated environment variables:

    CGMS_BACKUP_DATABASE_URL=<managed secret>
    CGMS_RESTORE_DATABASE_URL=<managed secret>
    CGMS_BACKUP_ENCRYPTION_KEY=<managed secret>

CGMS_BACKUP_DATABASE_URL identifies the database being backed up.

CGMS_RESTORE_DATABASE_URL identifies only the explicit restore target.
A restore must never default to DATABASE_URL or to the backup source.

CGMS_BACKUP_ENCRYPTION_KEY must be the URL-safe base64 encoding of exactly
32 random bytes. The decoded key is used for AES-256-GCM encryption. A
cryptographically separated manifest-authentication subkey is derived from
the same managed secret using HKDF-SHA256; the AES key is not directly reused
as the HMAC key.

Real values belong only in the approved secret-management mechanism. Do not
store populated values in the repository, deployment evidence, CI artifacts,
tickets, chat transcripts or operational logs.

## Source and restore-target isolation

The backup source and restore target must identify different databases.

Restore validation must use an explicitly provisioned disposable or otherwise
approved isolated target. The production/source database must never be used as
the restore target for a validation exercise.

The operator performs a source/target identity check. That check does not
replace infrastructure-level isolation, network controls or operator review.

## Backup prerequisites

Before creating a governed backup:

1. Confirm the approved backup directory.
2. Confirm pg_dump and pg_restore are available and compatible with the target
   PostgreSQL environment.
3. Confirm the backup source variable is supplied through the approved secret
   mechanism.
4. Confirm the 32-byte encryption-key contract passes production preflight.
5. Confirm sufficient storage exists for the encrypted artifact and manifest.
6. Confirm the backup operator and evidence owner.
7. Do not expose database URLs, passwords or the encryption key in evidence.

## Create an encrypted backup

Run:

    py -3.11 scripts/operations/database_recovery.py backup --backup-dir <approved-backup-directory>

The backup operation creates a PostgreSQL custom-format logical dump, verifies
that it has parseable archive entries, calculates the plaintext SHA-256,
encrypts the dump with AES-256-GCM, calculates the encrypted SHA-256 and writes
the governed version-2 manifest. The manifest carries an HMAC-SHA256 over all
control-critical metadata using the derived manifest-authentication subkey.

The temporary plaintext dump is removed after successful encryption and is
also cleaned up on controlled failure.

Record only non-secret evidence such as:

- backup timestamp;
- encrypted artifact name;
- manifest name;
- archive-entry count;
- non-secret source fingerprint;
- verification outcome;
- operator or automation reference.

## Verify a backup

Verification is mandatory after backup creation and before restore.

Run:

    py -3.11 scripts/operations/database_recovery.py verify --artifact <encrypted-artifact> --manifest <manifest-file>

Verification checks:

- manifest version and HMAC-SHA256 authentication before manifest metadata is trusted;
- encrypted artifact SHA-256;
- authenticated decryption;
- plaintext SHA-256;
- PostgreSQL archive readability;
- archive-entry count;
- manifest/artifact consistency.

Do not continue to restore when verification fails.

## RPO status

Run:

    py -3.11 scripts/operations/database_recovery.py status --backup-dir <approved-backup-directory> --rpo-hours 24

A successful status requires the latest governed backup to be no older than
24 hours. Status authenticates each manifest with CGMS_BACKUP_ENCRYPTION_KEY
before trusting its creation timestamp.

The command returns a non-zero operational result when the RPO is breached.

## Retention

The default retention policy is:

    Daily:   7
    Weekly:  4
    Monthly: 3

Retention evaluation is dry-run by default. Retention inventory authenticates
manifest metadata with CGMS_BACKUP_ENCRYPTION_KEY before using timestamps or
artifact identities to select candidates.

Review candidates first:

    py -3.11 scripts/operations/database_recovery.py prune --backup-dir <approved-backup-directory> --daily 7 --weekly 4 --monthly 3

Only after the candidate set has been reviewed and deletion is authorized,
apply it explicitly:

    py -3.11 scripts/operations/database_recovery.py prune --backup-dir <approved-backup-directory> --daily 7 --weekly 4 --monthly 3 --execute

Never automate --execute without an approved retention-control owner and
evidence trail.

## Restore validation prerequisites

Before restore validation:

1. Verify the encrypted backup and manifest.
2. Provision an isolated compatible PostgreSQL restore target.
3. Provision required extensions, including pgvector where applicable.
4. Set CGMS_RESTORE_DATABASE_URL only to that explicit target.
5. Confirm the restore target is not the backup source.
6. Confirm the restore target may be safely mutated or destroyed.
7. Record the validation authorization and target identifier without recording
   credentials or the full database URL.

## Restore to the explicit target

Run:

    py -3.11 scripts/operations/database_recovery.py restore --artifact <encrypted-artifact> --manifest <manifest-file>

The restore operator does not default the target to DATABASE_URL.

A restore is successful only when:

- backup verification succeeds;
- source and target identities differ;
- authenticated decryption succeeds;
- pg_restore succeeds against the explicit target; and
- the tool-reported restore duration remains within the governed RTO.

An RTO breach produces a non-zero operational result even when the PostgreSQL
restore command itself completes.

## Post-restore validation

A successful pg_restore is necessary but not sufficient evidence of
recoverability.

After an isolated restore:

1. Verify expected schemas and critical tables.
2. Verify required extensions.
3. Verify critical persisted records using non-secret acceptance checks.
4. Run the approved application/database smoke validation against the isolated
   target when authorized.
5. Record restore start and completion timestamps.
6. Record the tool-reported RTO outcome.
7. Record the validation result and cleanup reference.
8. Remove the disposable restore target under its separately approved cleanup
   procedure.

Do not point the normal application runtime at the isolated restore target
unless that action is explicitly authorized.

## Restore-validation cadence

A governed restore test is required:

- at least weekly;
- before pilot authorization;
- after a material database schema change;
- after a material PostgreSQL version change;
- after a material pg_dump or pg_restore tool change;
- after a material change to database_recovery.py; and
- after a recovery failure that could affect recoverability.

A backup without current restore-validation evidence does not satisfy the
CAP-005 recoverability control.

## Failure handling

If backup, verification, status, retention or restore validation fails:

1. Preserve the relevant encrypted artifact and manifest unless their
   integrity is itself in question.
2. Do not represent the failed control as a readiness pass.
3. Do not silently retry against a different database.
4. Do not weaken encryption, integrity, RPO or RTO controls to obtain a pass.
5. Record only non-secret failure evidence.
6. Escalate repeated or unexplained failures to the recovery owner.
7. Require a new successful governed validation before readiness reassessment.

## Evidence record

The non-secret recovery evidence should include:

    Validation reference:
    Environment classification:
    Backup artifact name:
    Manifest name:
    Backup timestamp:
    Verification result:
    RPO result:
    Restore-validation target reference:
    Restore result:
    RTO result:
    Retention-policy result:
    Operator/automation reference:
    Cleanup reference:

Never include:

- database passwords;
- full database URLs containing credentials;
- encryption keys;
- decrypted backup content;
- production secrets; or
- plaintext logical dumps.

## CAP-005 readiness boundary

This runbook defines the operational procedure but does not by itself close
CAP-005.

CAP-005 readiness promotion requires separate governed evidence that the
backup and restore implementation has been validated against an isolated
PostgreSQL environment and that the required recovery controls operate as
specified.

Governance/current-state documents must not be promoted until that validation
and the subsequent readiness reassessment are separately completed.
