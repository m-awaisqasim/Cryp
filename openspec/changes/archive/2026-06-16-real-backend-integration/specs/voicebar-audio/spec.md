## ADDED Requirements

### Requirement: VoiceBar uses Web Audio API for waveform
The VoiceBar component SHALL render a real-time waveform using the Web Audio API AnalyserNode instead of CSS keyframe animation.

#### Scenario: Waveform renders on mount
- **WHEN** the VoiceBar mounts and the assistant is in LISTENING state
- **THEN** an `AudioContext` is created (lazy, on first user gesture if needed)
- **AND** an `OscillatorNode` → `AnalyserNode` → `destination` chain is connected
- **AND** `requestAnimationFrame` reads `getByteTimeDomainData()` to draw the SVG waveform

#### Scenario: Flat line when muted or sleeping
- **WHEN** the assistant state is SLEEPING or the mic is muted
- **THEN** the oscillator is stopped or disconnected
- **AND** the waveform displays a flat center line

#### Scenario: AudioContext created on user interaction
- **WHEN** the user first clicks the mic button or the VoiceBar area
- **THEN** the `AudioContext` is created (to satisfy browser autoplay policy)
- **AND** the oscillator starts

#### Scenario: Cleanup on unmount
- **WHEN** the VoiceBar component unmounts
- **THEN** the `AudioContext` is closed
- **AND** the animation frame is cancelled
