# On-Call Handover & Troubleshooting Guide

## Database Latency (PostgreSQL)
1. Check CloudWatch for CPU spikes on `db-prod-cluster`.
2. Run `EXPLAIN ANALYZE` on long-running queries.
3. Check `pg_stat_activity` for locks.

## Cache Misses (Redis)
1. Verify memory usage on `cache-prod-01`.
2. Check eviction policy (Should be `volatile-lru`).
3. Increase maxmemory if usage > 85%.

## Contact
- Escalation: #ops-critical on Slack.
