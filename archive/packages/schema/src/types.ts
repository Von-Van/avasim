/**
 * AvaSim Schema v0.1.0
 *
 * Versioned contract types for AvaSim multi-service architecture.
 * These schemas enable deterministic, replayable combat simulations.
 */

// ============================================================================
// Character & Equipment Types
// ============================================================================

export interface CharacterBuild {
  name: string;
  level: number;
  /**
   * Core attributes
   */
  attributes: {
    might: number;
    finesse: number;
    guile: number;
    insight: number;
    resolve: number;
  };
  /**
   * HP configuration
   */
  hp: {
    max: number;
    current?: number; // If not specified, assumed to be max
  };
  /**
   * Anima (magical resource) configuration
   */
  anima?: {
    max: number;
    current?: number;
  };
  /**
   * Equipped items
   */
  equipment: {
    weapon_main?: string; // Weapon ID from AVALORE_WEAPONS
    weapon_offhand?: string;
    armor?: string;
    shield?: string;
  };
  /**
   * Feats (special abilities)
   */
  feats?: string[];
  /**
   * Spells known
   */
  spells?: string[];
  /**
   * Lineage/ancestry data
   */
  lineage?: {
    weapon?: string;
    weapon_alt?: string;
    elements?: string[];
  };
  /**
   * Team identifier
   */
  team: string;
  /**
   * Creature type
   */
  creature_type?: string;
}

export interface MapCell {
  x: number;
  y: number;
  terrain: 'floor' | 'wall' | 'water' | 'difficult' | 'cover';
  occupant?: string | null; // Character name if occupied
}

export interface TacticalMapConfig {
  width: number;
  height: number;
  cells: MapCell[];
}

export interface ParticipantPosition {
  character_name: string;
  position: [number, number]; // [x, y] tuple
}

// ============================================================================
// Run Request (Input Schema)
// ============================================================================

export interface RunRequest {
  /**
   * Schema version for compatibility tracking
   */
  schema_version: string; // e.g., "0.1.0"

  /**
   * Optional run identifier (generated if not provided)
   */
  run_id?: string;

  /**
   * Deterministic seed for RNG
   */
  seed: number;

  /**
   * Participant character builds
   */
  participants: CharacterBuild[];

  /**
   * Optional tactical map configuration
   */
  map?: TacticalMapConfig;

  /**
   * Optional initial positions (if map provided)
   */
  initial_positions?: ParticipantPosition[];

  /**
   * Environment configuration
   */
  environment?: {
    time_of_day?: 'day' | 'night';
    underwater?: boolean;
    party_initiated?: boolean;
    party_surprised?: boolean;
  };

  /**
   * Run configuration
   */
  config?: {
    max_rounds?: number; // Auto-end after N rounds
    capture_snapshots?: boolean; // Enable map snapshots
    log_level?: 'minimal' | 'standard' | 'verbose';
  };

  /**
   * Metadata (not used by engine, for orchestrator tracking)
   */
  metadata?: {
    scenario_name?: string;
    description?: string;
    tags?: string[];
    created_by?: string;
    [key: string]: any;
  };
}

// ============================================================================
// Run Events (Streaming Output Schema)
// ============================================================================

export type RunEventType =
  | 'run_started'
  | 'round_started'
  | 'turn_started'
  | 'action'
  | 'attack'
  | 'damage'
  | 'healing'
  | 'movement'
  | 'status_effect'
  | 'feat_activation'
  | 'spell_cast'
  | 'death'
  | 'map_snapshot'
  | 'round_ended'
  | 'turn_ended'
  | 'run_completed';

export interface BaseRunEvent {
  /**
   * Unique event ID
   */
  event_id: string;

  /**
   * Event type discriminator
   */
  type: RunEventType;

  /**
   * Timestamp (ISO 8601)
   */
  timestamp: string;

  /**
   * Combat round (0-indexed)
   */
  round: number;

  /**
   * Turn index within round
   */
  turn_index?: number;

  /**
   * Human-readable log message
   */
  message: string;
}

export interface RunStartedEvent extends BaseRunEvent {
  type: 'run_started';
  data: {
    run_id: string;
    seed: number;
    engine_version: string;
    participants: string[]; // Character names
  };
}

export interface RoundStartedEvent extends BaseRunEvent {
  type: 'round_started';
  data: {
    round: number;
    turn_order: string[]; // Character names in initiative order
  };
}

export interface TurnStartedEvent extends BaseRunEvent {
  type: 'turn_started';
  data: {
    actor: string; // Character name
    actions_available: number;
  };
}

export interface ActionEvent extends BaseRunEvent {
  type: 'action';
  data: {
    actor: string;
    action_type: string; // e.g., "attack", "move", "evade"
    action_cost: number;
    target?: string;
    details?: any;
  };
}

export interface AttackEvent extends BaseRunEvent {
  type: 'attack';
  data: {
    attacker: string;
    defender: string;
    weapon?: string;
    attack_roll: number;
    dice_values: [number, number];
    defense_value: number;
    hit: boolean;
    critical?: boolean;
    modifiers?: {
      name: string;
      value: number;
    }[];
  };
}

export interface DamageEvent extends BaseRunEvent {
  type: 'damage';
  data: {
    source: string; // Attacker or effect source
    target: string;
    damage_type: string;
    damage_amount: number;
    damage_mitigated: number;
    hp_before: number;
    hp_after: number;
    temp_hp_absorbed?: number;
  };
}

export interface HealingEvent extends BaseRunEvent {
  type: 'healing';
  data: {
    source: string;
    target: string;
    healing_amount: number;
    hp_before: number;
    hp_after: number;
  };
}

export interface MovementEvent extends BaseRunEvent {
  type: 'movement';
  data: {
    actor: string;
    from: [number, number];
    to: [number, number];
    distance: number;
    opportunity_attacks?: string[]; // Characters who got OA
  };
}

export interface StatusEffectEvent extends BaseRunEvent {
  type: 'status_effect';
  data: {
    target: string;
    effect: string; // e.g., "prone", "stunned", "bleeding"
    applied: boolean; // true = applied, false = removed
    duration?: number; // rounds remaining
    source?: string; // Who/what caused it
  };
}

export interface FeatActivationEvent extends BaseRunEvent {
  type: 'feat_activation';
  data: {
    actor: string;
    feat_name: string;
    target?: string;
    effect_description: string;
  };
}

export interface SpellCastEvent extends BaseRunEvent {
  type: 'spell_cast';
  data: {
    caster: string;
    spell_name: string;
    anima_cost: number;
    targets?: string[];
    result: string; // Description of effect
  };
}

export interface DeathEvent extends BaseRunEvent {
  type: 'death';
  data: {
    character: string;
    killer?: string;
    death_save_failures?: number;
  };
}

export interface MapSnapshotEvent extends BaseRunEvent {
  type: 'map_snapshot';
  data: {
    label: string;
    width: number;
    height: number;
    cells: MapCell[];
    actor?: {
      name: string;
      position: [number, number];
    };
    target?: {
      name: string;
      position: [number, number];
    };
  };
}

export interface RoundEndedEvent extends BaseRunEvent {
  type: 'round_ended';
  data: {
    round: number;
    survivors: string[];
  };
}

export interface TurnEndedEvent extends BaseRunEvent {
  type: 'turn_ended';
  data: {
    actor: string;
    actions_used: number;
  };
}

export interface RunCompletedEvent extends BaseRunEvent {
  type: 'run_completed';
  data: {
    run_id: string;
    outcome: 'victory' | 'defeat' | 'draw' | 'timeout';
    winning_team?: string;
    total_rounds: number;
  };
}

/**
 * Discriminated union of all event types
 */
export type RunEvent =
  | RunStartedEvent
  | RoundStartedEvent
  | TurnStartedEvent
  | ActionEvent
  | AttackEvent
  | DamageEvent
  | HealingEvent
  | MovementEvent
  | StatusEffectEvent
  | FeatActivationEvent
  | SpellCastEvent
  | DeathEvent
  | MapSnapshotEvent
  | RoundEndedEvent
  | TurnEndedEvent
  | RunCompletedEvent;

// ============================================================================
// Run Summary (Final Output Schema)
// ============================================================================

export interface ParticipantFinalState {
  name: string;
  team: string;
  final_hp: number;
  max_hp: number;
  is_alive: boolean;
  final_position?: [number, number];
  damage_dealt: number;
  damage_taken: number;
  kills: number;
  turns_taken: number;
  status_effects: string[];
}

export interface RunStatistics {
  total_rounds: number;
  total_turns: number;
  total_damage: number;
  total_attacks: number;
  total_hits: number;
  total_criticals: number;
  total_deaths: number;
  average_damage_per_hit: number;
  hit_rate: number;
}

export interface RunSummary {
  /**
   * Schema version
   */
  schema_version: string;

  /**
   * Run identifier
   */
  run_id: string;

  /**
   * Engine version that executed this run
   */
  engine_version: string;

  /**
   * Deterministic seed used
   */
  seed: number;

  /**
   * Run outcome
   */
  outcome: 'victory' | 'defeat' | 'draw' | 'timeout';

  /**
   * Winning team (if applicable)
   */
  winning_team?: string;

  /**
   * Final state of all participants
   */
  participants: ParticipantFinalState[];

  /**
   * Aggregate statistics
   */
  statistics: RunStatistics;

  /**
   * Execution metadata
   */
  execution: {
    started_at: string; // ISO 8601
    completed_at: string; // ISO 8601
    duration_ms: number;
    event_count: number;
  };

  /**
   * Optional metadata from request
   */
  metadata?: {
    [key: string]: any;
  };
}

// ============================================================================
// Error Schema
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

export interface RunErrorResponse {
  error: string;
  error_code: string;
  message: string;
  validation_errors?: ValidationError[];
  timestamp: string;
}
