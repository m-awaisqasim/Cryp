## ADDED Requirements

### Requirement: Drag-and-drop file upload
The React SPA SHALL support drag-and-drop file upload replicating the PyQt6 `FileDropZone` behaviour.

#### Scenario: File dragged over drop zone
- **WHEN** a file is dragged over the upload area
- **THEN** the drop zone border glows cyan
- **AND** a "Release to load" indicator appears

#### Scenario: File dropped for upload
- **WHEN** a file is dropped onto the upload area
- **THEN** the file is read as base64
- **AND** a `{"type": "file_upload", "name": "...", "data": "...", "mime": "..."}` message is sent via WebSocket
- **AND** a loading indicator is shown until `file_ack` response

#### Scenario: File upload acknowledged
- **WHEN** a `{"type": "file_ack", "name": "...", "path": "...", "status": "loaded"}` response is received
- **THEN** the UI shows the file name, type, and size
- **AND** a "Tell JARVIS what to do with it" hint is displayed

#### Scenario: File clear button
- **WHEN** the user clicks the "✕" button on the uploaded file
- **THEN** a `{"type": "file_clear"}` message is sent via WebSocket
- **AND** the drop zone resets to idle state

### Requirement: Click to browse file
The drop zone SHALL also support click-to-browse as an alternative to drag-and-drop.

#### Scenario: Click opens file picker
- **WHEN** the user clicks the drop zone
- **THEN** the native OS file picker dialog opens
- **AND** after selection, the file is uploaded via the same WebSocket protocol as drag-and-drop

### Requirement: File type icon display
The uploaded file display SHALL show a type-appropriate icon and metadata.

#### Scenario: File info displayed
- **WHEN** a file is loaded
- **THEN** the UI displays: file type icon, filename (truncated if >34 chars), extension + file size, and parent directory path
- **AND** icons match the PyQt6 mapping (image→cyan, video→orange, audio→purple, etc.)
