# Aetherial Systems: Security Protocol v2.4

## IAM Policies
- **Rule 1:** All employees must use MFA (TOTP or FIDO2).
- **Rule 2:** Root accounts are strictly locked in the Cyber-Vault.
- **Rule 3:** Permissions follow the Principle of Least Privilege (PoLP).

## Encryption
- **Data at Rest:** AES-256 via AWS KMS.
- **Data in Transit:** TLS 1.3 only.

## Credential Rotation
- Database passwords: Every 90 days.
- SSH Keys: Every 180 days.
