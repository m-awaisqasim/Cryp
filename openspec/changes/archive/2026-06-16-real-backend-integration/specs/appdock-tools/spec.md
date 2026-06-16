## ADDED Requirements

### Requirement: AppDock launches real tools via WebSocket
The AppDock component SHALL send WebSocket commands when an app icon is clicked, instead of showing stub notifications.

#### Scenario: App icon click sends command
- **WHEN** the user clicks an AppDock icon
- **THEN** `sendCommand(toolName)` is called via `useCrypWS`
- **AND** a WebSocket message `{"command": toolName}` is sent to the server

#### Scenario: Loading state shown during execution
- **WHEN** a command is sent but no transcript response has been received yet
- **THEN** the clicked icon shows a brief loading indicator (spinner or pulse)

#### Scenario: Each icon maps to a known tool name
- **WHEN** the AppDock renders
- **THEN** each icon has an associated tool command string (e.g., `"terminal"` → `"open terminal"`, `"files"` → `"show files"`, `"search"` → `"search the web"`)
