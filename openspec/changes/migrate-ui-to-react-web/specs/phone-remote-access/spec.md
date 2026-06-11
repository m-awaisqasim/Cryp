## ADDED Requirements

### Requirement: LAN access from mobile device
The dashboard SHALL be accessible from any device on the same local network without additional configuration.

#### Scenario: Access via LAN IP
- **WHEN** the Cryp host IP is `192.168.1.100` and port is `7070`
- **THEN** any device on the same LAN can access the UI at `http://192.168.1.100:7070`
- **AND** the UI is fully functional including WebSocket real-time updates

### Requirement: Optional tunnel for remote access
The system SHALL support an optional `--tunnel` flag or `TUNNEL_ENABLED=true` env var to create a public URL via cloudflared or ngrok.

#### Scenario: Tunnel starts with cloudflared
- **WHEN** `TUNNEL_ENABLED=true` and `TUNNEL_PROVIDER=cloudflared`
- **THEN** a `cloudflared tunnel --url http://localhost:7070` process is spawned
- **AND** the public URL is logged to the console
- **AND** a `{"type": "tunnel_url", "url": "https://xxx.trycloudflare.com"}` message is broadcast

#### Scenario: Tunnel starts with ngrok
- **WHEN** `TUNNEL_ENABLED=true` and `TUNNEL_PROVIDER=ngrok`
- **THEN** `pyngrok` creates a tunnel to `localhost:7070`
- **AND** the public ngrok URL is logged to the console

### Requirement: Mobile-responsive layout
The React SPA SHALL adapt its layout for mobile screen sizes (320px-768px width).

#### Scenario: Mobile layout activates
- **WHEN** the viewport width is less than 768px
- **THEN** the multi-panel grid collapses to a single column
- **AND** the HUD orb scales to fit the viewport
- **AND** touch targets are at least 44px for interactive elements

#### Scenario: Landscape mobile layout
- **WHEN** the viewport is between 568px and 768px wide in landscape orientation
- **THEN** the panels display in a 2-column grid
- **AND** the HUD orb takes the left column

### Requirement: Tunnel access without CORS issues
The FastAPI server SHALL be configured to allow cross-origin requests from tunnel domains.

#### Scenario: CORS headers present
- **WHEN** a request arrives from `https://xxx.trycloudflare.com`
- **THEN** the FastAPI server responds with permissive CORS headers
- **AND** WebSocket connections from the tunnel domain succeed
