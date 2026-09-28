"""
Historical Production Post-Mortems and Institutional SRE Knowledge.
These records represent past painful debugging sessions whose institutional
memory is retained in Hindsight to prevent recurring outages.
"""

INITIAL_POST_MORTEMS = [
    {
        "id": "INC-2024-1014",
        "service": "kafka-ingress-cluster",
        "severity": "P1",
        "title": "Kafka Broker JVM Heap Exhaustion & Consumer Lag Spike",
        "date": "2024-10-14",
        "summary": "Kafka broker-02 experienced severe JVM heap exhaustion (99% heap usage) causing leader rebalance thrashing, 45,000 msg/sec consumer lag spike on topic 'payment-events.v1', and upstream 504 gateway timeouts.",
        "root_cause": "An upstream checkout microservice deployment deployed without compression, dumping uncompressed 64MB JSON batch payloads onto 'payment-events.v1'. Broker JVM default buffer pool allocation was overwhelmed, triggering Stop-The-World GC pauses.",
        "failed_attempts": [
            "Simply restarting kafka-broker-02 caused immediate cascading crash of broker-03 due to sudden partition replica reassignment.",
            "Increasing broker pod memory limit alone did not work because JVM max heap (-Xmx) was hard-coded in the helm chart template."
        ],
        "verified_mitigation": [
            "1. Apply dynamic topic payload restriction: bin/kafka-configs.sh --bootstrap-server kafka-broker:9092 --entity-type topics --entity-name payment-events.v1 --alter --add-config max.message.bytes=10485760",
            "2. Enable G1GC garbage collector flag: -XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=45",
            "3. Gracefully recycle brokers one-by-one with 10-minute wait interval between nodes.",
            "4. Roll back upstream checkout service to release v2.4.1."
        ],
        "tags": ["kafka", "jvm", "heap", "oom", "consumer-lag", "payment-events", "gc-pause", "buffer-overflow"],
        "telemetry_signatures": [
            "OutOfMemoryError: Java heap space",
            "org.apache.kafka.common.record.DefaultRecordBatch",
            "broker-02",
            "payment-events.v1"
        ]
    },
    {
        "id": "INC-2024-1102",
        "service": "postgres-primary-billing",
        "severity": "P0",
        "title": "PostgreSQL Connection Pool Starvation & Exclusive Lock Deadlock",
        "date": "2024-11-02",
        "summary": "Postgres database exhausted all 800 available connection slots ('FATAL: remaining connection slots are reserved for non-replication superuser connections'). All customer checkout and subscription renewal transactions stalled for 28 minutes.",
        "root_cause": "The monthly affiliate payout cron worker executed 'LOCK TABLE billing_ledger IN EXCLUSIVE MODE' inside an un-indexed batch transaction while thousands of concurrent live checkout updates were attempting row-level writes on the same table.",
        "failed_attempts": [
            "Restarting the PgBouncer pooler caused massive thunder herd connection spikes that took down the read replicas.",
            "Killing random idle connections did not relieve the lock wait queue."
        ],
        "verified_mitigation": [
            "1. Identify and terminate the blocking cron PID immediately: SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query ILIKE '%affiliate_payout%' AND state != 'idle';",
            "2. Pause the Celery cron schedule queue in Redis: celery -A core_tasks control cancel_consumer payout_queue",
            "3. Deploy emergency hotfix migration #94 which rewrites the payout query to use batched 'SELECT id FROM billing_ledger FOR UPDATE SKIP LOCKED LIMIT 100'.",
            "4. Reload PgBouncer pool with: pgbouncer -R -u postgres /etc/pgbouncer/pgbouncer.ini"
        ],
        "tags": ["postgres", "database", "deadlock", "connection-pool", "billing_ledger", "pgbouncer", "exclusive-lock"],
        "telemetry_signatures": [
            "remaining connection slots are reserved",
            "canceling statement due to lock timeout",
            "ExclusiveLock on relation billing_ledger",
            "503 Service Unavailable on /api/v2/checkout"
        ]
    },
    {
        "id": "INC-2024-1128",
        "service": "payment-gw-core",
        "severity": "P0",
        "title": "Kubernetes Payment Gateway CrashLoopBackOff & Envoy 503 Spikes",
        "date": "2024-11-28",
        "summary": "All 16 pods of payment-gw went into CrashLoopBackOff immediately following routine CI/CD container image release v2.15.0. 100% of debit/credit card tokenizations failed with Envoy 503 UF (upstream failure).",
        "root_cause": "The base Docker image was upgraded from alpine:3.18 to alpine:3.20 without installing the 'gcompat' musl libc package. The compiled Go payment microservice relied on dynamic CGO bindings for hardware security module (HSM) encryption, causing the binary execution to fail with 'exec user process caused: no such file or directory'.",
        "failed_attempts": [
            "Scaling up replicas from 16 to 32 exacerbated the kube-apiserver crash loop logging without fixing the missing library.",
            "Restarting ingress envoy controllers had zero effect since upstream pods were continuously failing startup probes."
        ],
        "verified_mitigation": [
            "1. Instantly roll back deployment to previous stable image tag: kubectl rollout undo deployment/payment-gw -n core-finance",
            "2. Verify pod readiness: kubectl rollout status deployment/payment-gw -n core-finance --timeout=60s",
            "3. Update Dockerfile to include 'apk add --no-cache gcompat libc6-compat' for all musl-based builds before re-promoting v2.15.1."
        ],
        "tags": ["kubernetes", "crashloopbackoff", "alpine", "gcompat", "musl", "cgo", "envoy-503", "payment-gw"],
        "telemetry_signatures": [
            "CrashLoopBackOff",
            "exec user process caused: no such file or directory",
            "OCI runtime create failed",
            "payment-gw-7b98d",
            "Envoy 503 UF"
        ]
    },
    {
        "id": "INC-2024-1215",
        "service": "redis-session-sentinel",
        "severity": "P1",
        "title": "Redis Sentinel Split-Brain & Authentication Desync",
        "date": "2024-12-15",
        "summary": "User session cache threw READONLY You can't write against a read only replica across all web instances. Millions of active login sessions were suddenly logged out.",
        "root_cause": "Transient network jitter between availability zones caused Sentinel quorum to elect a new master on redis-node-3, but redis-node-1 retained old master state without demotion due to a misconfigured 'min-replicas-to-write 1' threshold and delayed TLS renegotiation timeout.",
        "failed_attempts": [
            "Flushing redis keys caused catastrophic cache stampede on MySQL user authentication table.",
            "Manually forcing SLAVEOF NO ONE on node-1 created duplicate disparate datasets."
        ],
        "verified_mitigation": [
            "1. Demote stale node-1 to replica explicitly: redis-cli -h redis-node-1 -a $REDIS_PASS REPLICAOF redis-node-3 6379",
            "2. Force Sentinel reconfiguration: redis-cli -p 26379 SENTINEL reset session-cluster",
            "3. Patch redis.conf with 'min-replicas-to-write 2' and 'min-replicas-max-lag 10' to prevent future rogue unacknowledged writes.",
            "4. Warm user session cache via background pipeline script."
        ],
        "tags": ["redis", "sentinel", "split-brain", "readonly-replica", "cache-stampede", "session-store"],
        "telemetry_signatures": [
            "READONLY You can't write against a read only replica",
            "SENTINEL sdown",
            "redis-node-1",
            "session-cluster"
        ]
    }
]
