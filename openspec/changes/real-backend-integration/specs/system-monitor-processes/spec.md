## ADDED Requirements

### Requirement: REST API for process list
The server SHALL expose a `/api/processes` REST endpoint that returns a snapshot of running processes via psutil.

#### Scenario: GET returns process list
- **WHEN** a client sends `GET /api/processes`
- **THEN** the server returns `{"success": true, "data": [{"pid": 1234, "name": "python3", "cpu": 2.5, "memory": 1.2, "status": "running"}, ...]}`
- **AND** the list is sorted by CPU usage descending
- **AND** each entry includes `pid` (int), `name` (str), `cpu` (float), `memory` (float, percent of RAM), `status` (str)

#### Scenario: psutil errors handled gracefully
- **WHEN** psutil raises an exception during process iteration
- **THEN** the endpoint returns `{"success": false, "error": "..."}` with status 500

### Requirement: SystemMonitor shows real process list
The SystemMonitor component SHALL fetch and display the real process list.

#### Scenario: Processes tab shows real data
- **WHEN** the SystemMonitor processes tab is visible
- **THEN** it fetches `GET /api/processes` every 5 seconds
- **AND** displays the process table with PID, name, CPU%, and memory%

#### Scenario: Process list polling stops on unmount
- **WHEN** the SystemMonitor component unmounts
- **THEN** the polling interval is cleared
