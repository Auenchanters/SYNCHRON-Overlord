# Runtime artefacts

`receipts/overlord_audit.jsonl` — append-only audit ledger (fsync'd per entry).
`exports/OVL-CERT-*.json` — downloadable compliance certificates.

Both are generated at runtime and git-ignored; keep the folder itself so a
fresh clone and the Docker image have a writable mount point.
