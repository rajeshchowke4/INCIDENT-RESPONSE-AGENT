"""
Real-World Production Alert Scenarios.
Includes recurring institutional failures and novel incidents
to demonstrate the Hindsight learning lifecycle.
"""

SCENARIOS = {
    "kafka_heap_exhaustion": {
        "id": "SCN-KAFKA-01",
        "title": "Kafka Broker 02 JVM Heap Exhaustion (Recurring)",
        "service": "kafka-ingress-cluster",
        "severity": "P1",
        "alert_name": "KafkaBrokerJVMHeapCriticallyHigh",
        "timestamp": "2026-09-28T17:45:00Z",
        "summary": "Alert firing: kafka-broker-02 JVM heap allocation reached 98.4%. Consumer group 'payment-ingest-group' lag has exceeded 52,000 messages.",
        "raw_logs": """2026-09-28T17:44:12Z [kafka-broker-02] ERROR [KafkaServer id=2] Fatal error during KafkaServer startup: java.lang.OutOfMemoryError: Java heap space
    at org.apache.kafka.common.record.DefaultRecordBatch.readRecords(DefaultRecordBatch.java:264)
    at org.apache.kafka.common.record.FileRecords.batchesFrom(FileRecords.java:112)
    at kafka.log.LogSegment.read(LogSegment.scala:392)
2026-09-28T17:44:20Z [kafka-broker-02] WARN [GroupCoordinator 2]: Preparing to rebalance group payment-ingest-group in state PreparingRebalance
2026-09-28T17:44:35Z [ingress-api-gateway] ERROR 504 Gateway Timeout: failed to produce to topic 'payment-events.v1' after 30000ms""",
        "known_in_memory": True,
        "matched_historical_id": "INC-2024-1014"
    },
    "postgres_deadlock_payout": {
        "id": "SCN-PG-02",
        "title": "PostgreSQL Connection Pool Exhaustion & Deadlock (Recurring)",
        "service": "postgres-primary-billing",
        "severity": "P0",
        "alert_name": "PostgresActiveConnectionsExhausted",
        "timestamp": "2026-09-28T17:46:30Z",
        "summary": "Alert firing: PostgreSQL active client connections reached 798/800. PgBouncer queue latency > 14,000ms. Checkout endpoints returning 503.",
        "raw_logs": """2026-09-28T17:45:55Z [postgres-db-primary] FATAL: remaining connection slots are reserved for non-replication superuser connections
2026-09-28T17:46:02Z [postgres-db-primary] ERROR: canceling statement due to lock timeout
2026-09-28T17:46:02Z [postgres-db-primary] DETAIL: Process 19283 waits for ExclusiveLock on relation 'billing_ledger' of database 16385; blocked by process 18742.
2026-09-28T17:46:15Z [checkout-service] ERROR: 503 Service Unavailable on /api/v2/checkout: connection to database failed""",
        "known_in_memory": True,
        "matched_historical_id": "INC-2024-1102"
    },
    "k8s_payment_gw_crashloop": {
        "id": "SCN-K8S-03",
        "title": "Payment Gateway CrashLoopBackOff & Envoy 503s (Recurring)",
        "service": "payment-gw-core",
        "severity": "P0",
        "alert_name": "KubePodCrashLooping",
        "timestamp": "2026-09-28T17:48:10Z",
        "summary": "Alert firing: 16/16 replicas of payment-gw in namespace core-finance are failing startup probes and entering CrashLoopBackOff.",
        "raw_logs": """2026-09-28T17:47:05Z [kubelet] Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: expected cgroupsPath to be of format [slice]:[prefix]:[name] for systemd cgroups, got '': unknown
2026-09-28T17:47:12Z [kubelet] Error: container 'payment-gw' in pod 'payment-gw-7b98d-xr92k' failed: standard_init_linux.go:228: exec user process caused: no such file or directory
2026-09-28T17:47:20Z [envoy-ingress] [response_flags = "UF,URX"] "POST /v1/tokens HTTP/1.1" 503 - 0 19 0 - "payment-gw.core-finance" """,
        "known_in_memory": True,
        "matched_historical_id": "INC-2024-1128"
    },
    "redis_sentinel_split_brain": {
        "id": "SCN-REDIS-04",
        "title": "Redis Sentinel Read-Only Replica Desync (Recurring)",
        "service": "redis-session-sentinel",
        "severity": "P1",
        "alert_name": "RedisMasterReplicaStateDesync",
        "timestamp": "2026-09-28T17:49:00Z",
        "summary": "Alert firing: 95% of write commands to user session cache failing with READONLY replica error. Active sessions terminating.",
        "raw_logs": """2026-09-28T17:48:32Z [auth-service] ERROR: Redis::CommandError: READONLY You can't write against a read only replica on redis-node-1:6379
2026-09-28T17:48:40Z [sentinel-01] +sdown master session-cluster 10.0.4.12 6379
2026-09-28T17:48:45Z [sentinel-01] +failover-end master session-cluster 10.0.4.12 6379
2026-09-28T17:48:50Z [sentinel-01] +switch-master session-cluster 10.0.4.12 6379 10.0.4.15 6379""",
        "known_in_memory": True,
        "matched_historical_id": "INC-2024-1215"
    },
    "novel_rabbitmq_poison_pill": {
        "id": "SCN-NOVEL-05",
        "title": "RabbitMQ Dead-Letter Queue Flooding (NOVEL INCIDENT)",
        "service": "notification-dispatcher",
        "severity": "P2",
        "alert_name": "RabbitMQDLQQueueSizeSurge",
        "timestamp": "2026-09-28T17:50:00Z",
        "summary": "First-time occurrence: Dead-letter queue 'notifications.dlq' has grown to 850,000 unacknowledged messages. Consumer pods spinning at 100% CPU.",
        "raw_logs": """2026-09-28T17:49:15Z [notification-worker-04] ERROR: AmqpRejectAndRequeueException: JSON parse error: Unrecognized field 'template_locale_override' not marked as ignorable
    at com.fasterxml.jackson.databind.exc.UnrecognizedPropertyException.from(UnrecognizedPropertyException.java:61)
2026-09-28T17:49:22Z [rabbitmq-cluster] WARNING: Channel 14 on connection 10.0.12.8:58422 high consumer unack limit (10000/10000) reached.
2026-09-28T17:49:30Z [notification-worker-04] WARN: Message requeue loop detected for payload id 'msg-99214'. Shunting to DLQ at 4500 msg/sec.""",
        "known_in_memory": False,
        "matched_historical_id": None
    }
}
