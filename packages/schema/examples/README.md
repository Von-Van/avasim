# AvaSim Schema Examples

This directory contains example payloads demonstrating the AvaSim service contracts.

## Files

### Run Requests

- **[run-request-simple.json](./run-request-simple.json)** - Basic 1v1 duel without a tactical map
- **[run-request-with-map.json](./run-request-with-map.json)** - Combat scenario with tactical positioning

### Run Summary

- **[run-summary.json](./run-summary.json)** - Example final summary from a completed run

### Run Events

- **[run-events.json](./run-events.json)** - Sample event stream showing various event types during combat

## Validating Examples

Run the validation script to verify all examples pass schema validation:

```bash
cd packages/schema
npm install
npm run validate
```

## Using Examples in Tests

```typescript
import { validator } from '@avasim/schema';
import runRequestExample from './examples/run-request-simple.json';

// Validate the example
const result = validator.validateRunRequest(runRequestExample);
console.log(result.valid); // true

// Use in HTTP request
const response = await fetch('http://localhost:3000/run/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(runRequestExample)
});
```

## Schema Versioning

All examples include a `schema_version` field (currently `"0.1.0"`). When the contract evolves:

1. Update the schema version using semantic versioning
2. Maintain backward compatibility where possible
3. Document breaking changes in migration guides
4. Keep old examples for regression testing
