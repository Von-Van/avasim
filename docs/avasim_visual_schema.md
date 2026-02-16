# AvaSim Visual Schema

This companion document provides visual schematics for the next-gen offline AvaSim design.

## 1. Offline System Topology

```mermaid
flowchart LR
    subgraph Desktop["Desktop Runtime"]
        UI["UI Shell (Tauri + React/TS)"]
        ORCH["Local Orchestrator (TypeScript)"]
        UI --> ORCH
    end

    subgraph Services["Local Container Services"]
        RULES["Rules Engine (Rust)"]
        WORKER["Batch Worker (Python)"]
        DB["Postgres or SQLite (Local)"]
        CACHE["Redis (Local Queue/Cache)"]
        ART["Artifact Store (MinIO or FS)"]
    end

    ORCH --> RULES
    ORCH --> WORKER
    ORCH --> DB
    ORCH --> CACHE
    ORCH --> ART
    WORKER --> RULES
    WORKER --> ART
```

## 2. Mode Selection and User Flow

```mermaid
flowchart TD
    START["Launch AvaSim"] --> HOME["Home: Mode Select"]
    HOME --> M1["Scenario Analysis Mode"]
    HOME --> M2["Batch Optimization Mode"]
    HOME --> M3["Endless Arena Mode"]

    M1 --> M1A["Build/Load Scenario"]
    M1A --> M1B["Run Deterministic Simulation"]
    M1B --> M1C["Inspect Timeline + Explainability"]

    M2 --> M2A["Choose Build Space + Seeds"]
    M2A --> M2B["Queue Batch Runs"]
    M2B --> M2C["View Aggregates + Recommendations"]

    M3 --> M3A["Pick Player Build"]
    M3A --> M3B["Manual Actions in Live Combat"]
    M3B --> M3C["Auto-Generate Next Opponent"]
    M3C --> M3B
```

## 3. Endless Arena Encounter Generation

```mermaid
flowchart LR
    INIT["Start Arena Run (seed, player build)"] --> GEN["Generate Opponent Build"]
    GEN --> VALID["Validate Against Avalore Ruleset"]
    VALID --> SCALE["Apply Difficulty Scaling"]
    SCALE --> FIGHT["Play Encounter (manual player input)"]
    FIGHT --> RESULT{"Victory?"}
    RESULT -->|Yes| REWARD["Apply Progression/Modifiers"]
    REWARD --> NEXT["Increment Tier + Reseed"]
    NEXT --> GEN
    RESULT -->|No| END["Run Summary + Export Replay"]
```

## 4. UI Surface Blueprint (Production Layout)

```mermaid
flowchart TB
    APP["AvaSim Main Window"] --> TOP["Top Bar: Profile, Build, Settings, Theme"]
    APP --> BODY["Main Body"]
    APP --> FOOT["Bottom Bar: Timeline, Playback, Export"]

    BODY --> LEFT["Left Rail: Mode Controls, Scenario/Batch Inputs"]
    BODY --> CENTER["Center: Tactical Battlefield (Primary Focus)"]
    BODY --> RIGHT["Right Rail: Character Sheets, Rules Explainability"]
    BODY --> DRAWER["Collapsible Drawer: Combat Feed + Event Filters"]
```

## 5. Deterministic Replay Data Flow

```mermaid
sequenceDiagram
    participant UI as "Desktop UI"
    participant ORCH as "Local Orchestrator"
    participant ENG as "Rules Engine"
    participant DB as "Local Storage"

    UI->>ORCH: "StartRun(run_request, seed)"
    ORCH->>ENG: "ExecuteRun(request)"
    loop "Each simulation step"
      ENG-->>ORCH: "RunEvent(snapshot_delta, action_meta)"
      ORCH-->>UI: "StreamEvent(run_event)"
    end
    ENG-->>ORCH: "RunComplete(summary)"
    ORCH->>DB: "Persist run, snapshots, summary"
    UI->>ORCH: "OpenReplay(run_id)"
    ORCH-->>UI: "ReplayStream(snapshot_sequence)"
```

## 6. Design Intent Notes

- The simulation remains fully offline and deterministic.
- The same event schema feeds all three modes.
- Endless Arena is a first-class mode, not an add-on.
- UI hierarchy keeps battlefield and explainability visible at all times.
