const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats').default;

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

// Load schemas
const runRequestSchema = require('../json-schema/run-request.schema.json');
const runSummarySchema = require('../json-schema/run-summary.schema.json');

// Compile validators
const validateRunRequest = ajv.compile(runRequestSchema);
const validateRunSummary = ajv.compile(runSummarySchema);

// Example files to validate
const examples = [
  {
    file: 'examples/run-request-simple.json',
    validator: validateRunRequest,
    type: 'RunRequest'
  },
  {
    file: 'examples/run-request-with-map.json',
    validator: validateRunRequest,
    type: 'RunRequest'
  },
  {
    file: 'examples/run-summary.json',
    validator: validateRunSummary,
    type: 'RunSummary'
  }
];

let allValid = true;

console.log('🔍 Validating example payloads...\n');

examples.forEach(({ file, validator, type }) => {
  const filePath = path.join(__dirname, '..', file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

  const valid = validator(data);

  if (valid) {
    console.log(`✅ ${file} (${type}) - VALID`);
  } else {
    console.log(`❌ ${file} (${type}) - INVALID`);
    console.log('   Errors:');
    validator.errors.forEach(err => {
      console.log(`   - ${err.instancePath || '/'}: ${err.message}`);
    });
    allValid = false;
  }
});

console.log('\n' + '='.repeat(60));
if (allValid) {
  console.log('✅ All examples are valid!');
  process.exit(0);
} else {
  console.log('❌ Some examples failed validation');
  process.exit(1);
}
