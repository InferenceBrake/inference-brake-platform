/**
 * JS SDK guarded wrapper. Runs without an LLM provider.
 *
 *   npm install inferencebrake
 *   INFERENCEBRAKE_API_KEY=ib_your_key node node_example.js
 */

const { guarded, LoopDetectedError } = require('inferencebrake');

const apiKey = process.env.INFERENCEBRAKE_API_KEY;
if (!apiKey) {
  console.error('Set INFERENCEBRAKE_API_KEY');
  process.exit(1);
}

const callModel = guarded(
  async (prompt) => {
    // Replace with your real model call.
    return {
      choices: [
        { message: { content: 'The service is unavailable, so I will retry the same call.' } },
      ],
    };
  },
  {
    apiKey,
    sessionId: 'node-demo',
    model: 'gpt-4o-mini',
    prompt: 'fetch user balance',
    action: () => 'get_balance',
  }
);

(async () => {
  for (let step = 1; step <= 8; step++) {
    try {
      await callModel('fetch the user balance');
    } catch (e) {
      if (e instanceof LoopDetectedError) {
        console.log(`step ${step}: halted by InferenceBrake -> ${e.message}`);
        process.exit(0);
      }
      throw e;
    }
    console.log(`step ${step}: ok`);
  }
  console.log('No loop detected');
  process.exit(1);
})();
