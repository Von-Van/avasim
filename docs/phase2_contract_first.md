# Phase 2: Contract First - Complete ✅

## Overview

Phase 2 establishes versioned API contracts for all AvaSim service communication. This enables deterministic, replayable simulations with structured event streams.

## What Was Built

### 1. Schema Package (`packages/schema/`)

**TypeScript Types** ([src/types.ts](../packages/schema/src/types.ts)):
- `RunRequest` - Input schema for starting a run
- `RunEvent` - Discriminated union of 17 event types
- `RunSummary` - Final results schema
- `CharacterBuild` - Character configuration
- `TacticalMapConfig` - Map layout
- `ValidationError` - Error responses

**JSON Schema Definitions**:
- [run-request.schema.json](../packages/schema/json-schema/run-request.schema.json)
- [run-summary.schema.json](../packages/schema/json-schema/run-summary.schema.json)

**Validation** ([src/validator.ts](../packages/schema/src/validator.ts)):
- AJV-based runtime validation
- Structured error responses
- Singleton validator instance

**Example Payloads**:
- [run-request-simple.json](../packages/schema/examples/run-request-simple.json) - Basic 1v1 duel
- [run-request-with-map.json](../packages/schema/examples/run-request-with-map.json) - Combat with tactical map
- [run-summary.json](../packages/schema/examples/run-summary.json) - Final results
- [run-events.json](../packages/schema/examples/run-events.json) - Event stream samples

### 2. Run Submission Handler (Orchestrator)

**Endpoint**: `POST /run/start`

Features:
- Schema validation using `@avasim/schema`
- Structured error responses (400 for validation failures)
- Auto-generated `run_id` (UUID v4)
- Returns `stream_url` for event streaming
- Logs validation details

**Response (202 Accepted)**:
```json
{
  "status": "accepted",
  "run_id": "abc-123",
  "message": "Run request accepted and validated",
  "schema_version": "0.1.0",
  "engine_version": "0.1.0-python",
  "validation_time_ms": 2,
  "stream_url": "/run/abc-123/events"
}
```

**Error Response (400 Bad Request)**:
```json
{
  "error": "Validation Error",
  "error_code": "INVALID_RUN_REQUEST",
  "message": "The run request payload failed schema validation",
  "validation_errors": [
    {
      "field": "/seed",
      "message": "must be integer",
      "value": "not-a-number"
    }
  ],
  "timestamp": "2026-02-16T10:30:00.000Z"
}
```

### 3. Event Streaming (Server-Sent Events)

**Endpoint**: `GET /run/:runId/events`

Features:
- Server-Sent Events (SSE) streaming
- Multiple concurrent client connections per run
- Auto-cleanup on client disconnect
- Mock event generator (Phase 2 demo)
- Broadcasts to all connected clients

**Event Stream Format**:
```
Content-Type: text/event-stream

data: {"event_id":"evt_001","type":"run_started","timestamp":"...","round":0,"message":"Mock run started","data":{...}}

data: {"event_id":"evt_002","type":"attack","timestamp":"...","round":1,"message":"MockWarrior attacks MockGoblin","data":{...}}
```

### 4. Python Event Adapter (`combat/events.py`)

**EventEmitter Class**:

Converts combat engine actions into structured `RunEvent` format.

**Methods**:
- `emit_run_started(participants)` - Run initialization
- `emit_round_started(round_num, turn_order)` - Round start
- `emit_turn_started(actor, actions_available)` - Turn start
- `emit_attack(attacker, defender, ...)` - Attack roll
- `emit_damage(source, target, ...)` - Damage dealt
- `emit_movement(actor, from_pos, to_pos, ...)` - Movement
- `emit_status_effect(target, effect, applied, ...)` - Status changes
- `emit_feat_activation(actor, feat_name, ...)` - Feat usage
- `emit_spell_cast(caster, spell_name, ...)` - Spell casting
- `emit_death(character, killer)` - Character death
- `emit_run_completed(outcome, winning_team)` - Run end

**Usage Example**:
```python
from combat import EventEmitter

emitter = EventEmitter(run_id="abc-123", seed=12345)
emitter.emit_run_started(participants=["Warrior", "Goblin"])
emitter.emit_attack(attacker="Warrior", defender="Goblin", ...)
events = emitter.get_events()  # List[Dict]
json_output = emitter.get_events_json()  # JSON string
```

**Demo Script**: [examples/event_emitter_demo.py](../examples/event_emitter_demo.py)

### 5. Contract Documentation

**Files Created**:
- [packages/schema/README.md](../packages/schema/README.md) - Complete API reference
- [packages/schema/examples/README.md](../packages/schema/examples/README.md) - Example usage guide
- [docs/phase2_contract_first.md](../docs/phase2_contract_first.md) - This document

**Documentation Includes**:
- Schema definitions for all three contracts
- TypeScript and Python usage examples
- API endpoint specifications
- Validation instructions
- Integration examples (fetch, SSE client, Python client)
- Versioning strategy

## Updated Services

### Orchestrator Changes

**[apps/orchestrator/package.json](../apps/orchestrator/package.json)**:
- Added `@avasim/schema` dependency (local package)
- Added `uuid` for run ID generation

**[apps/orchestrator/src/index.ts](../apps/orchestrator/src/index.ts)**:
- Imports `validator`, `RunRequest`, `RunEvent`, `SCHEMA_VERSION`
- Validates `POST /run/start` requests
- Returns structured errors on validation failure
- Implements `GET /run/:runId/events` SSE endpoint
- Mock event generator for Phase 2 demonstration
- Connection tracking and broadcast helper

**[infra/docker/orchestrator.Dockerfile](../infra/docker/orchestrator.Dockerfile)**:
- Updated to build schema package first
- Copies and builds `packages/schema/` before orchestrator
- Workspace structure preserved in Docker build

### Combat Package Changes

**[combat/events.py](../combat/events.py)** (NEW):
- Full `EventEmitter` implementation
- 17 event emission methods
- JSON serialization
- Compatible with `@avasim/schema` RunEvent types

**[combat/__init__.py](../combat/__init__.py)**:
- Exports `EventEmitter` for public use

## Usage

### Start the Stack

```bash
make docker-up
```

### Test Run Submission

```bash
# Submit a valid run request
curl -X POST http://localhost:3000/run/start \
  -H "Content-Type: application/json" \
  -d @packages/schema/examples/run-request-simple.json

# Expected: 202 Accepted with run_id and stream_url
```

### Test Invalid Request

```bash
# Submit request with invalid seed
curl -X POST http://localhost:3000/run/start \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"0.1.0","seed":"not-a-number","participants":[]}'

# Expected: 400 Bad Request with validation_errors
```

### Stream Events

```bash
# Connect to event stream (replace <run_id> with actual ID)
curl -N http://localhost:3000/run/<run_id>/events

# Expected: SSE stream with mock events
```

### Test Python EventEmitter

```bash
python examples/event_emitter_demo.py

# Expected: Structured JSON output matching RunEvent schema
```

### Validate Schema Examples

```bash
cd packages/schema
npm install
npm run validate

# Expected: All examples pass validation
```

## Phase 2 Success Criteria ✅

- ✅ Schema validates sample payloads (run-request, run-summary, run-events)
- ✅ Invalid payloads rejected with structured errors
- ✅ Client receives mocked timeline events via SSE
- ✅ Python simulation emits contract-compliant events
- ✅ Documentation enables usage without reverse engineering

## Testing

### Schema Validation

```bash
cd packages/schema
npm run validate
```

**Result**: All 3 examples pass JSON Schema validation

### Orchestrator Endpoints

```bash
# Health check
curl http://localhost:3000/health

# Version info
curl http://localhost:3000/version

# Submit valid run
curl -X POST http://localhost:3000/run/start \
  -H "Content-Type: application/json" \
  -d @packages/schema/examples/run-request-simple.json

# Stream events
curl -N http://localhost:3000/run/<run_id>/events
```

### Event Emitter Demo

```bash
python examples/event_emitter_demo.py
```

**Output**: 10 structured events in RunEvent format

## Architecture Notes

### Contract Versioning

All payloads include `schema_version` field:
- Current version: `0.1.0`
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Breaking changes increment MAJOR
- Services validate version compatibility

### Event Stream Design

- **Server-Sent Events (SSE)**: One-way server-to-client push
- **Multiple clients**: Each run supports multiple concurrent connections
- **Auto-cleanup**: Connections removed on client disconnect
- **Broadcast**: Events sent to all connected clients for a run

### Phase 2 Limitations

- **Mock events only**: Real event generation happens in Phase 4
- **No persistence**: Events not stored, only streamed
- **No run execution**: Validation only, no actual simulation
- **Single orchestrator**: No load balancing or scaling

## Next Steps

**Phase 3: Rust Rules Engine Bootstrap**
- Initialize Rust service with `/health`, `/simulate` stub
- Port core dice/action primitives (seeded RNG + action economy)
- Port minimal duel loop (movement + attack + damage)
- Implement snapshot event emission from Rust
- Add engine-version stamping to every run
- Add cross-language parity test harness

The contract-first foundation is complete! All services can now communicate using versioned, validated schemas.
