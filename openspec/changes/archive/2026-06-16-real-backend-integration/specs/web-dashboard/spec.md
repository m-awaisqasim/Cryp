## ADDED Requirements

### Requirement: REST API for memory data
The server SHALL expose a `/api/memory` REST endpoint for reading and writing the assistant's long-term memory.

#### Scenario: GET returns full memory dict
- **WHEN** a client sends `GET /api/memory`
- **THEN** the server returns `{"success": true, "data": {"key1": "value1", ...}}` with all key-value pairs from `memory_manager.load_memory()`
- **AND** the response has `Content-Type: application/json`

#### Scenario: POST writes a new key-value pair
- **WHEN** a client sends `POST /api/memory` with body `{"key": "user_name", "value": "Alice"}`
- **THEN** the server calls `memory_manager.update_memory("user_name", "Alice")`
- **AND** returns `{"success": true, "data": {"user_name": "Alice", ...}}` with the full updated memory dict

#### Scenario: POST returns 400 for invalid body
- **WHEN** a client sends `POST /api/memory` with missing `key` or `value` fields
- **THEN** the server returns `{"success": false, "error": "..."}` with status 400

### Requirement: REST API for process list
The server SHALL expose a `/api/processes` REST endpoint that returns a snapshot of running processes via psutil.

#### Scenario: GET returns process list
- **WHEN** a client sends `GET /api/processes`
- **THEN** the server returns `{"success": true, "data": [{"pid": 1234, "name": "python3", "cpu": 2.5, "memory": 1.2, "status": "running"}, ...]}`
- **AND** the list is sorted by CPU usage descending
- **AND** each entry includes `pid` (int), `name` (str), `cpu` (float), `memory` (float), `status` (str)

#### Scenario: psutil errors handled gracefully
- **WHEN** psutil raises an exception during process iteration
- **THEN** the endpoint returns `{"success": false, "error": "..."}` with status 500
