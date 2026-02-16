import express, { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { validator, RunRequest, RunEvent, SCHEMA_VERSION } from '@avasim/schema';

const app = express();
const PORT = process.env.PORT || 3000;
const VERSION = '0.1.0';
const ENGINE_VERSION = '0.1.0-python';

app.use(express.json());

// Store active event streams (run_id -> Response[])
const activeStreams = new Map<string, Response[]>();

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'avasim-orchestrator',
    timestamp: new Date().toISOString(),
  });
});

// Version endpoint
app.get('/version', (req: Request, res: Response) => {
  res.json({
    service: 'avasim-orchestrator',
    version: VERSION,
    node: process.version,
    env: process.env.NODE_ENV || 'development',
  });
});

// Run submission endpoint with schema validation
app.post('/run/start', (req: Request, res: Response) => {
  const startTime = Date.now();

  // Validate the request payload against RunRequest schema
  const validation = validator.validateRunRequest(req.body);

  if (!validation.valid) {
    const errorResponse = validator.createErrorResponse(
      'Validation Error',
      'INVALID_RUN_REQUEST',
      'The run request payload failed schema validation',
      validation.errors
    );
    console.error('❌ Run request validation failed:', validation.errors);
    return res.status(400).json(errorResponse);
  }

  const runRequest = req.body as RunRequest;

  // Generate run_id if not provided
  const runId = runRequest.run_id || uuidv4();

  console.log(`✅ Run request validated: ${runId}`);
  console.log(`   - Seed: ${runRequest.seed}`);
  console.log(`   - Participants: ${runRequest.participants.length}`);
  console.log(`   - Schema version: ${runRequest.schema_version}`);

  // Phase 2: Just validate and accept
  // Phase 4: Will forward to rules engine and return real results
  res.status(202).json({
    status: 'accepted',
    run_id: runId,
    message: 'Run request accepted and validated (execution in Phase 4)',
    schema_version: SCHEMA_VERSION,
    engine_version: ENGINE_VERSION,
    validation_time_ms: Date.now() - startTime,
    stream_url: `/run/${runId}/events`,
  });
});

// Event stream endpoint (Server-Sent Events)
app.get('/run/:runId/events', (req: Request, res: Response) => {
  const { runId } = req.params;

  console.log(`📡 Client connected to event stream: ${runId}`);

  // Set up SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

  // Register this connection
  if (!activeStreams.has(runId)) {
    activeStreams.set(runId, []);
  }
  activeStreams.get(runId)!.push(res);

  // Send initial connection event
  const connectionEvent = {
    type: 'connection',
    run_id: runId,
    message: 'Connected to event stream',
    timestamp: new Date().toISOString(),
  };
  res.write(`data: ${JSON.stringify(connectionEvent)}\n\n`);

  // Phase 2: Send mock events to demonstrate the stream
  // Phase 4: Will receive real events from rules engine
  sendMockEvents(runId, res);

  // Handle client disconnect
  req.on('close', () => {
    console.log(`📡 Client disconnected from event stream: ${runId}`);
    const streams = activeStreams.get(runId);
    if (streams) {
      const index = streams.indexOf(res);
      if (index > -1) {
        streams.splice(index, 1);
      }
      if (streams.length === 0) {
        activeStreams.delete(runId);
      }
    }
  });
});

// Helper function to broadcast an event to all connected clients for a run
function broadcastEvent(runId: string, event: RunEvent | any): void {
  const streams = activeStreams.get(runId);
  if (!streams || streams.length === 0) {
    return;
  }

  const eventData = `data: ${JSON.stringify(event)}\n\n`;
  streams.forEach(res => {
    try {
      res.write(eventData);
    } catch (err) {
      console.error(`Failed to send event to client:`, err);
    }
  });
}

// Mock event generator (Phase 2 demonstration)
async function sendMockEvents(runId: string, res: Response): Promise<void> {
  // Wait a bit before starting
  await sleep(500);

  const mockEvents: Partial<RunEvent>[] = [
    {
      event_id: uuidv4(),
      type: 'run_started',
      timestamp: new Date().toISOString(),
      round: 0,
      message: 'Mock run started',
      data: {
        run_id: runId,
        seed: 12345,
        engine_version: ENGINE_VERSION,
        participants: ['MockWarrior', 'MockGoblin'],
      },
    },
    {
      event_id: uuidv4(),
      type: 'round_started',
      timestamp: new Date().toISOString(),
      round: 1,
      message: 'Mock round 1 begins',
      data: {
        round: 1,
        turn_order: ['MockWarrior', 'MockGoblin'],
      },
    },
    {
      event_id: uuidv4(),
      type: 'attack',
      timestamp: new Date().toISOString(),
      round: 1,
      turn_index: 0,
      message: 'MockWarrior attacks MockGoblin',
      data: {
        attacker: 'MockWarrior',
        defender: 'MockGoblin',
        weapon: 'longsword',
        attack_roll: 15,
        dice_values: [7, 8] as [number, number],
        defense_value: 12,
        hit: true,
      },
    },
    {
      event_id: uuidv4(),
      type: 'damage',
      timestamp: new Date().toISOString(),
      round: 1,
      turn_index: 0,
      message: 'MockGoblin takes 8 damage',
      data: {
        source: 'MockWarrior',
        target: 'MockGoblin',
        damage_type: 'slashing',
        damage_amount: 8,
        damage_mitigated: 2,
        hp_before: 12,
        hp_after: 4,
      },
    },
    {
      event_id: uuidv4(),
      type: 'run_completed',
      timestamp: new Date().toISOString(),
      round: 1,
      message: 'Mock run completed',
      data: {
        run_id: runId,
        outcome: 'victory' as const,
        winning_team: 'party',
        total_rounds: 1,
      },
    },
  ];

  for (const event of mockEvents) {
    await sleep(800); // Simulate event timing
    broadcastEvent(runId, event);
  }

  console.log(`✅ Mock event stream completed for ${runId}`);
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

app.listen(PORT, () => {
  console.log(`✅ AvaSim Orchestrator listening on port ${PORT}`);
  console.log(`   Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`   Version: ${VERSION}`);
});
