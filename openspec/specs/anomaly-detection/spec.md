# anomaly-detection Specification

## Requirements

### Requirement: System metric baseline tracking
The system SHALL maintain a rolling baseline of system metrics (CPU, RAM, active application) per hour of day. The baseline SHALL use data from the last 7 days.

#### Scenario: Baseline built from patterns
- **WHEN** a pattern scan detects `patterns/top_apps` and system health data
- **THEN** the engine computes per-hour averages: `cpu_mean`, `cpu_std`, `ram_mean`, `ram_std`, `typical_app`
- **AND** stores the baseline as procedural memory: `patterns/baseline/<hour>: { cpu_mean, cpu_std, ram_mean, ram_std, typical_app }`

#### Scenario: No baseline data yet
- **WHEN** fewer than 3 data points exist for a given hour
- **THEN** anomaly detection is skipped for that hour (insufficient data)

### Requirement: Real-time anomaly check
The system SHALL check current system metrics against the baseline after each pattern scan and when triggered by significant metric changes.

#### Scenario: CPU anomaly detected
- **WHEN** current CPU percent exceeds `cpu_mean + 2 * cpu_std` for the current hour
- **AND** the debounce cooldown for CPU alerts has elapsed
- **THEN** the engine enqueues a proactive message: "Sir, CPU is unusually high at X% compared to the usual Y% at this time."

#### Scenario: RAM anomaly detected
- **WHEN** current RAM percent exceeds `ram_mean + 2 * ram_std` for the current hour
- **AND** the debounce cooldown for RAM alerts has elapsed
- **THEN** the engine enqueues a proactive message about unusual memory usage

#### Scenario: Application anomaly detected
- **WHEN** the current active application differs from `typical_app` for this hour
- **AND** this deviation has occurred for 3+ consecutive hourly checks
- **AND** no anomaly for this was spoken in the last 24 hours
- **THEN** the engine enqueues: "Sir, I notice you're using X instead of your usual Y at this time."

#### Scenario: All metrics normal
- **WHEN** all current metrics are within 2σ of the baseline
- **THEN** no anomaly message is generated

### Requirement: Anomaly alert debouncing
The system SHALL prevent repeated anomaly alerts for the same metric within a configurable cooldown period.

#### Scenario: Repeated anomaly suppressed
- **WHEN** a CPU anomaly alert was spoken at T=0
- **AND** CPU remains anomalous at T=300
- **AND** `PROACTIVE_ANOMALY_COOLDOWN` (default 1800s) has not elapsed
- **THEN** no new alert is spoken

#### Scenario: Cooldown expires
- **WHEN** a CPU anomaly alert was spoken at T=0
- **AND** CPU remains anomalous at T=1800
- **THEN** a new anomaly alert is spoken
