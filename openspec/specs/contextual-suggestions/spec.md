# contextual-suggestions Specification

## Requirements

### Requirement: Suggestion rule engine
The system SHALL maintain a set of if-then rules that generate proactive suggestions based on current context. Rules SHALL be stored in `config/proactive_rules.json` and loaded at engine startup.

#### Scenario: Rules loaded from config
- **WHEN** the engine starts
- **THEN** it reads `config/proactive_rules.json`
- **AND** each rule's conditions are compiled into a match table

#### Scenario: Config file missing
- **WHEN** `config/proactive_rules.json` does not exist
- **THEN** the engine uses built-in default rules (terminal → updates, git conflict → VS Code, empty clipboard at 9am → daily planner)

### Requirement: Context evaluation
The system SHALL evaluate suggestion rules against current live context (active window title, clipboard content, time of day, day of week, recent patterns) at each natural pause opportunity.

#### Scenario: Terminal rule matches
- **WHEN** the active window title contains "Terminal" or "bash" or "zsh"
- **AND** it is between 8:00 and 10:00 on a weekday
- **AND** the suggestion cooldown has elapsed
- **THEN** the engine enqueues: "Sir, would you like me to run system updates while you work?"

#### Scenario: Git conflict rule matches
- **WHEN** clipboard content contains "CONFLICT" or "<<<<<<<"
- **AND** the suggestion cooldown has elapsed
- **THEN** the engine enqueues: "Sir, I noticed a merge conflict in your clipboard. Shall I open VS Code to resolve it?"

#### Scenario: No rule matches
- **WHEN** no rule conditions are met
- **THEN** no suggestion is generated

### Requirement: Suggestion cooldown
The system SHALL enforce a configurable cooldown between suggestions to prevent annoyance (default: 30 minutes).

#### Scenario: Cooldown respected
- **WHEN** a suggestion was spoken at T=0
- **AND** the next pause occurs at T=600 (< 1800s cooldown)
- **THEN** no suggestion is spoken even if conditions match

#### Scenario: Cooldown expired
- **WHEN** a suggestion was spoken at T=0
- **AND** the next pause occurs at T=1900 (> 1800s cooldown)
- **THEN** a new suggestion is spoken if conditions match

### Requirement: Suggestion style
Suggestions SHALL be phrased as questions or offers, not commands. They SHALL include "Sir" as the greeting.

#### Scenario: Suggestion phrasing
- **WHEN** a suggestion is generated
- **THEN** it starts with "Sir, ..."
- **AND** it is phrased as a question or offer: "Would you like...", "Shall I...", "Do you need..."
