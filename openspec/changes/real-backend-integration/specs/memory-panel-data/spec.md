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

### Requirement: MemoryPanel displays real memory data
The MemoryPanel component SHALL fetch and display the assistant's memory from the backend.

#### Scenario: MemoryPanel loads on mount
- **WHEN** the MemoryPanel mounts
- **THEN** it fetches `GET /api/memory`
- **AND** displays each key-value pair as a labeled row

#### Scenario: MemoryPanel updates on WebSocket push
- **WHEN** the WebSocket receives a `{"type": "memory", "data": {...}}` message
- **THEN** the MemoryPanel re-renders with the updated memory dict
