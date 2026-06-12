# @avasim/schema

**Version:** 0.1.0

Versioned contract definitions for AvaSim's multi-service architecture. This package provides TypeScript types, JSON Schema validation, and example payloads for all inter-service communication.

## Overview

AvaSim uses a contract-first approach where all service boundaries are defined by versioned schemas. This enables:

- **Deterministic behavior**: Same inputs + same seed = same outputs
- **Replayability**: All events are structured and can be replayed
- **Multi-language support**: Contracts work across TypeScript, Python, and Rust services
- **Version compatibility**: Breaking changes are tracked via semantic versioning

## Installation

### TypeScript/Node.js

```bash
npm install @avasim/schema
```

### Python

```python
# Event emitter is in combat package
from combat import EventEmitter
```

## Core Contracts

### 1. RunRequest

Input schema for starting a simulation run.

**Required fields:**
- `schema_version` (string) - Schema version (e.g., "0.1.0")
- `seed` (number) - Deterministic RNG seed
- `participants` (array) - Character builds

**Example:**

```typescript
import { RunRequest } from '@avasim/schema';

const request: RunRequest = {
  schema_version: "0.1.0",
  seed: 12345,
  participants: [
    {
      name: "Warrior",
      level: 3,
      attributes: { might: 4, finesse: 2, guile: 1, insight: 2, resolve: 3 },
      hp: { max: 35 },
      equipment: {
        weapon_main: "longsword",
        armor: "chainmail"
      },
      team: "party"
    }
  ]
};
```

[Full schema →](./json-schema/run-request.schema.json)
[Example →](./examples/run-request-simple.json)

### 2. RunEvent

Streaming events during simulation execution.

**Event types:**
- `run_started` - Run initialization
- `round_started` - New combat round
- `turn_started` - Character's turn begins
- `attack` - Attack roll with results
- `damage` - Damage dealt to target
- `movement` - Character movement
- `status_effect` - Status applied/removed
- `feat_activation` - Special ability used
- `spell_cast` - Spell casting
- `death` - Character death
- `run_completed` - Run finished

**All events include:**
- `event_id` (string) - Unique event identifier
- `type` (string) - Event type discriminator
- `timestamp` (string) - ISO 8601 timestamp
- `round` (number) - Combat round number
- `message` (string) - Human-readable description
- `data` (object) - Event-specific payload

**Example:**

```typescript
import { AttackEvent } from '@avasim/schema';

const event: AttackEvent = {
  event_id: "evt_001",
  type: "attack",
  timestamp: "2026-02-16T10:30:00.000Z",
  round: 1,
  turn_index: 0,
  message: "Warrior attacks Goblin with longsword (roll: 15 vs 12) - HIT!",
  data: {
    attacker: "Warrior",
    defender: "Goblin",
    weapon: "longsword",
    attack_roll: 15,
    dice_values: [7, 8],
    defense_value: 12,
    hit: true
  }
};
```

[Example stream →](./examples/run-events.json)

### 3. RunSummary

Final results after simulation completion.

**Required fields:**
- `run_id` (string) - Unique run identifier
- `engine_version` (string) - Engine version used
- `seed` (number) - RNG seed
- `outcome` (string) - "victory" | "defeat" | "draw" | "timeout"
- `participants` (array) - Final state of all characters
- `statistics` (object) - Aggregate stats
- `execution` (object) - Timing and metadata

**Example:**

```typescript
import { RunSummary } from '@avasim/schema';

const summary: RunSummary = {
  schema_version: "0.1.0",
  run_id: "abc-123",
  engine_version: "0.1.0-python",
  seed: 12345,
  outcome: "victory",
  winning_team: "party",
  participants: [
    {
      name: "Warrior",
      team: "party",
      final_hp: 18,
      max_hp: 35,
      is_alive: true,
      damage_dealt: 15,
      damage_taken: 17,
      kills: 1,
      turns_taken: 4,
      status_effects: []
    }
  ],
  statistics: {
    total_rounds: 4,
    total_attacks: 6,
    hit_rate: 0.667
    // ... more stats
  },
  execution: {
    started_at: "2026-02-16T10:30:00.000Z",
    completed_at: "2026-02-16T10:30:01.234Z",
    duration_ms: 1234,
    event_count: 42
  }
};
```

[Full schema →](./json-schema/run-summary.schema.json)
[Example →](./examples/run-summary.json)

## Usage

### TypeScript (Orchestrator)

```typescript
import { validator, RunRequest, SCHEMA_VERSION } from '@avasim/schema';

// Validate incoming request
const result = validator.validateRunRequest(requestBody);

if (!result.valid) {
  return res.status(400).json({
    error: 'Validation failed',
    errors: result.errors
  });
}

// Type-safe access
const request = requestBody as RunRequest;
console.log(`Starting run with seed ${request.seed}`);
```

### Python (Combat Engine)

```python
from combat import EventEmitter

# Create emitter for a run
emitter = EventEmitter(run_id="abc-123", seed=12345)

# Emit events during combat
emitter.emit_run_started(participants=["Warrior", "Goblin"])
emitter.emit_attack(
    attacker="Warrior",
    defender="Goblin",
    weapon="longsword",
    attack_roll=15,
    dice_values=(7, 8),
    defense_value=12,
    hit=True
)
emitter.emit_run_completed(outcome="victory", winning_team="party")

# Get structured events
events = emitter.get_events()  # List[Dict]
json_output = emitter.get_events_json()  # JSON string
```

## API Endpoints

### POST /run/start

Submit a new run request.

**Request:**
```json
{
  "schema_version": "0.1.0",
  "seed": 12345,
  "participants": [...]
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "run_id": "abc-123",
  "stream_url": "/run/abc-123/events"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Validation Error",
  "error_code": "INVALID_RUN_REQUEST",
  "validation_errors": [
    {
      "field": "/seed",
      "message": "must be integer"
    }
  ]
}
```

### GET /run/:runId/events

Stream run events via Server-Sent Events (SSE).

**Response:**
```
Content-Type: text/event-stream

data: {"event_id":"evt_001","type":"run_started",...}

data: {"event_id":"evt_002","type":"attack",...}

data: {"event_id":"evt_003","type":"damage",...}
```

## Schema Versioning

The schema follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (incompatible with previous versions)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Current Version: 0.1.0

Initial release with core contracts for run orchestration.

### Compatibility Rules

1. **Forward compatibility**: Newer services can process older schema versions
2. **Version checking**: All payloads include `schema_version` field
3. **Graceful degradation**: Unknown fields are ignored
4. **Validation**: Strict validation prevents invalid data propagation

## Validation

### Validate Examples

```bash
cd packages/schema
npm install
npm run validate
```

### Custom Validation

```typescript
import Ajv from 'ajv';
import runRequestSchema from '@avasim/schema/json-schema/run-request.schema.json';

const ajv = new Ajv();
const validate = ajv.compile(runRequestSchema);

const valid = validate(myData);
if (!valid) {
  console.error(validate.errors);
}
```

## Development

### Building

```bash
npm install
npm run build
```

### Testing Examples

```bash
npm run validate
```

## File Structure

```
packages/schema/
├── src/
│   ├── types.ts          # TypeScript type definitions
│   ├── validator.ts      # Runtime validation with AJV
│   └── index.ts          # Package exports
├── json-schema/
│   ├── run-request.schema.json
│   └── run-summary.schema.json
├── examples/
│   ├── run-request-simple.json
│   ├── run-request-with-map.json
│   ├── run-summary.json
│   └── run-events.json
└── scripts/
    └── validate-examples.js
```

## Integration Examples

### Client (Fetch API)

```typescript
const response = await fetch('http://localhost:3000/run/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(runRequest)
});

const { run_id, stream_url } = await response.json();

// Connect to event stream
const eventSource = new EventSource(`http://localhost:3000${stream_url}`);

eventSource.onmessage = (event) => {
  const runEvent = JSON.parse(event.data);
  console.log(`[${runEvent.type}] ${runEvent.message}`);
};
```

### Python Client

```python
import requests
import json

# Submit run
response = requests.post('http://localhost:3000/run/start', json=run_request)
data = response.json()
run_id = data['run_id']
stream_url = data['stream_url']

# Stream events
import sseclient
response = requests.get(f'http://localhost:3000{stream_url}', stream=True)
client = sseclient.SSEClient(response)

for event in client.events():
    run_event = json.loads(event.data)
    print(f"[{run_event['type']}] {run_event['message']}")
```

## License

MIT

## Maintainers

AvaSim Team
