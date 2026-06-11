## ADDED Requirements

### Requirement: Rotating 3D orb animation
The HUD SHALL render a central rotating 3D orb using Three.js with layered concentric rings, pulsing halo glow, and animated scan arcs.

#### Scenario: Orb renders on page load
- **WHEN** the SPA loads in a browser
- **THEN** a 3D orb is rendered at the center of the HUD with animated rotation
- **AND** concentric arc rings rotate at varying speeds around the orb

#### Scenario: Orb responds to speaking state
- **WHEN** `state` is `SPEAKING`
- **THEN** the orb pulse rate increases
- **AND** particle burst frequency increases around the orb
- **AND** the halo expands to 1.5x default radius

#### Scenario: Orb responds to muted state
- **WHEN** `state` is `MUTED`
- **THEN** orb colors shift from cyan to muted magenta
- **AND** animations slow to idle rate

#### Scenario: Orb responds to sleeping state
- **WHEN** `state` is `SLEEPING`
- **THEN** orb dims to 40% opacity
- **AND** rotation slows to a near-stop

### Requirement: State indicator with animated text
The HUD SHALL display the current assistant state as animated text beneath the orb with pulsing symbols.

#### Scenario: State text updates via WebSocket
- **WHEN** a `{"type": "state", "state": "THINKING"}` message arrives
- **THEN** the state text below the orb updates to "THINKING" with a blinking diamond symbol

#### Scenario: State colors match PyQt6 scheme
- **WHEN** state is `LISTENING`
- **THEN** text is green
- **WHEN** state is `SPEAKING`
- **THEN** text is orange (`#ff6b00`)
- **WHEN** state is `THINKING`
- **THEN** text is amber (`#ffcc00`)
- **WHEN** state is `MUTED`
- **THEN** text is muted magenta (`#ff3366`)

### Requirement: Ambient particle system
The HUD SHALL render a continuous particle effect with floating hex data bits and sparkles.

#### Scenario: Data bits float outward
- **WHEN** the HUD is active
- **THEN** hex snippets ("0x", "A1", "7F", "E4", etc.) float outward from the orb and fade
- **WHEN** state is `SPEAKING`
- **THEN** data bit spawn rate increases 3x

#### Scenario: Sparkle particles animate
- **WHEN** the HUD is active
- **THEN** small sparkle particles drift across the screen with varying sizes and fade out

### Requirement: Circular waveform bars
The HUD SHALL render radial audio-reactive waveform bars around the orb.

#### Scenario: Bars animate in idle mode
- **WHEN** no audio is being captured
- **THEN** bars show subtle ambient animation (sinusoidal variation)

#### Scenario: Bars respond to speaking volume
- **WHEN** state is `SPEAKING`
- **THEN** bar heights reflect the audio volume level from the analyzer

### Requirement: Animated background with grid dots
The HUD background SHALL display a subtle moving grid dot pattern with pulsing alpha.

#### Scenario: Grid dots animate
- **WHEN** the HUD is rendered
- **THEN** a grid of small dots is visible in the background
- **AND** dots slowly scroll in the grid pattern
- **AND** dots are excluded from the center area around the orb

### Requirement: Tick marks around orb
The HUD SHALL render animated tick marks (degree markers) around the orb perimeter.

#### Scenario: Tick marks render at intervals
- **WHEN** the HUD is rendered
- **THEN** tick marks appear at 5-degree intervals around the orb
- **AND** major ticks (30-degree) are thicker and brighter than minor ticks
