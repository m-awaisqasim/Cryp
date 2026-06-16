## ADDED Requirements

### Requirement: Replace NEXUS branding with Cryp
The system SHALL replace all occurrences of "NEXUS" or "NEXUS AI" text labels in the dashboard UI with "Cryp".

#### Scenario: TopBar title updated
- **WHEN** the dashboard loads
- **THEN** the TopBar displays "Cryp" instead of "NEXUS" or "NEXUS AI"

#### Scenario: Welcome message updated
- **WHEN** the initial conversation message is shown
- **THEN** the assistant identifies itself as "Cryp" not "NEXUS AI"

#### Scenario: Panel headers updated
- **WHEN** any panel header contains "NEXUS"
- **THEN** it displays "Cryp" instead

#### Scenario: No remaining NEXUS references
- **WHEN** all UI source files are scanned
- **THEN** no file contains the string "NEXUS" (case-insensitive) outside of comments or filenames
