/**
 * InferenceBrake SDK test — follows the docs examples.
 *
 * Usage:
 *   export INFERENCEBRAKE_API_KEY=ib_your_key_here
 *   bun run test_docs.mjs
 */

import { InferenceBrake } from 'inferencebrake';

const API_KEY = process.env.INFERENCEBRAKE_API_KEY || 'ib_your_key';

async function testBasic() {
  console.log('\n=== Basic Usage ===');
  const guard = new InferenceBrake({ apiKey: API_KEY });

  const steps = [
    'I need to search for weather in NYC',
    'Let me call the weather API for NYC',
    'I should check the weather in New York City',
  ];

  for (let i = 0; i < steps.length; i++) {
    const status = await guard.check(steps[i], 'test-basic');
    console.log(`  Step ${i + 1}: action=${status.action}, similarity=${(status.similarity * 100).toFixed(2)}%, status=${status.status}`);

    if (status.shouldStop) {
      console.log(`  Loop detected: ${status.message}`);
      break;
    }
  }

  return guard;
}

async function testBatch(guard) {
  console.log('\n=== Batch Check ===');
  const statuses = await guard.checkBatch(
    ['first step', 'second step', 'third step'],
    'test-batch',
  );
  statuses.forEach((s, i) => console.log(`  Step ${i + 1}: ${s.action}`));
}

async function testHistory(guard) {
  console.log('\n=== Session History ===');
  try {
    const history = await guard.getSessionHistory('test-basic', 10);
    const steps = history.steps || [];
    console.log(`  Found ${steps.length} steps`);
    for (const step of steps) {
      console.log(`  Step ${step.step_number}: ${(step.reasoning || '').slice(0, 60)}`);
    }
  } catch (e) {
    console.log(`  History: ${e.message}`);
  }
}

async function testConfig() {
  console.log('\n=== Configuration ===');
  const guard = new InferenceBrake({
    apiKey: API_KEY,
    timeout: 10000,
    maxRetries: 3,
    retryDelay: 1000,
    retryBackoff: 2,
    circuitBreakerThreshold: 5,
    circuitBreakerTimeout: 30000,
  });
  const status = await guard.check('config test', 'test-config');
  console.log(`  Status: ${status.status}`);
}

async function main() {
  const guard = await testBasic();
  await testBatch(guard);
  await testHistory(guard);
  await testConfig();
  console.log('\nDone.');
}

main().catch(console.error);
