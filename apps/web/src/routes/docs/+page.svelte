<script lang="ts">
	import '../../app.css';
	import hljs from 'highlight.js';
	import 'highlight.js/styles/github-dark-dimmed.css';

	let activeSection = $state('quickstart');
	let copyFeedback = $state<string | null>(null);

	const sections = [
		{ id: 'quickstart', label: 'Quick Start' },
		{ id: 'python', label: 'Python SDK' },
		{ id: 'javascript', label: 'JavaScript SDK' },
		{ id: 'rest', label: 'REST API' },
		{ id: 'reference', label: 'API Reference' },
		{ id: 'integrations', label: 'Integrations' },
		{ id: 'escalation', label: 'Escalation' },
		{ id: 'analytics', label: 'Analytics' },
	];

	function scrollTo(id: string) {
		activeSection = id;
		const el = document.getElementById(id);
		if (el) el.scrollIntoView({ behavior: 'smooth' });
	}

	function copyCode(text: string, label: string) {
		navigator.clipboard.writeText(text);
		copyFeedback = label;
		setTimeout(() => copyFeedback = null, 2000);
	}

	$effect(() => {
		hljs.highlightAll();
	});

	const codes = {
		pip: 'pip install inferencebrake',
		npm: 'npm install inferencebrake',
		pythonBasic: `from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="ib_your_key")

for step in agent.run():
    status = guard.check(
        reasoning=step.reasoning,
        session_id="agent-session-1",
        action=step.tool,       # optional, enables action repetition
        model="gpt-4o-mini",    # optional, recorded for attribution
        prompt="weather task",  # optional, recorded for attribution
    )

    if status.should_stop:
        print(f"Loop detected! {status.detector_triggered}")
        break`,
		pythonBatch: `statuses = guard.check_batch(
    reasoning_list=["step1", "step2", "step3"],
    session_id="agent-session-1"
)`,
		pythonHistory: `history = guard.get_session_history(
    session_id="agent-session-1",
    limit=50
)`,
		pythonConfig: `guard = InferenceBrake(
    api_key="ib_your_key",
    timeout=10,
    auto_stop=False
)`,
		jsBasic: `const { InferenceBrake } = require('inferencebrake');

const guard = new InferenceBrake({ apiKey: 'ib_your_key' });

const status = await guard.check(
    'reasoning text',
    'session-1'
);

if (status.shouldStop) {
    console.log('Loop detected!', status.message);
}`,
		jsConfig: `const guard = new InferenceBrake({
    apiKey: 'ib_your_key',
    timeout: 10000,
    maxRetries: 3,
    retryDelay: 1000,
    retryBackoff: 2,
    circuitBreakerThreshold: 5,
    circuitBreakerTimeout: 30000,
});`,
		jsMonitor: `const { inferencebrakeMonitor } = require('inferencebrake');

const monitor = inferencebrakeMonitor({ apiKey: 'ib_your_key' });

const status = await monitor.check(reasoning);

monitor.reset('new-session-id');`,
		curlHealth: `curl https://ocnjiyiqeifllbyqohks.supabase.co/functions/v1/health`,
		curlCheck: `curl -X POST https://ocnjiyiqeifllbyqohks.supabase.co/functions/v1/check \\
  -H "Authorization: Bearer ib_your_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "agent-123",
    "reasoning": "I should check the weather in NYC"
  }'`,
		responseJson: `{
  "action": "PROCEED",
  "loop_detected": false,
  "similarity": 0.42,
  "confidence": 0.18,
  "detectors": {
    "semantic": false,
    "token_repeat": false,
    "action": false,
    "ngram": false,
    "editdist": false,
    "compression": false
  },
  "estimated_cost_saved": 0,
  "status": "safe",
  "message": "Reasoning sound",
  "usage": {
    "today": 42,
    "month": 42,
    "limit": 5000,
    "remaining": 4958
  }
}`,
		langchain: `from inferencebrake import InferenceBrakeCallbackHandler

handler = InferenceBrakeCallbackHandler(api_key="ib_your_key")

agent = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])`,
		crewai: `from inferencebrake import create_crewai_callback

callback = create_crewai_callback(api_key="ib_your_key")

agent.callbacks = [callback]`,
		decorator: `from inferencebrake import guard_agent_loop

@guard_agent_loop(
    api_key="ib_your_key",
    session_id="agent-1",
    action=lambda r: r["tool"],
)
def call_model(prompt):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )`,
		jsMonitorFull: `const { InferenceBrakeCallbackHandler } = require('inferencebrake');

const handler = new InferenceBrakeCallbackHandler({
    apiKey: 'ib_your_key',
    sessionId: 'my-agent'
});

const result = await chain.invoke(input, { callbacks: [handler] });`,
		escalation: `from inferencebrake import guard_agent_loop

@guard_agent_loop(
    api_key="ib_your_key",
    session_id="agent-1",
    escalate=lambda status, attempt: switch_model("claude-opus"),
    max_escalations=2,
)
def call_model(prompt):
    ...  # on a loop the agent retries on the stronger model,
         # then stops if it still loops`,
		analyticsCurl: `curl -H "Authorization: Bearer ib_your_key" \\
  "https://ocnjiyiqeifllbyqohks.supabase.co/functions/v1/analytics-summary?days=30"`,
		analyticsJson: `{
  "total_checks": 78,
  "loops_blocked": 9,
  "estimated_usd_saved": 0.0146,
  "by_model": [
    { "model": "gpt-4o-mini", "checks": 30, "loops": 4, "saved": 0.006 }
  ],
  "by_action": [
    { "action": "get_balance", "checks": 12, "loops": 3, "saved": 0.004 }
  ],
  "by_detector": [
    { "detector": "semantic", "loops": 6 },
    { "detector": "token_repeat", "loops": 3 }
  ],
  "recent_loops": [
    {
      "session_id": "agent-1",
      "model": "gpt-4o-mini",
      "action": "get_balance",
      "confidence": 0.85,
      "saved": 0.0019,
      "created_at": "2026-09-20T03:24:44Z"
    }
  ]
}`,
	};
</script>

<svelte:head>
	<title>Integration Docs - InferenceBrake</title>
	<meta name="description" content="Integrate InferenceBrake loop detection with Python, JavaScript, or REST API." />
</svelte:head>

{#snippet codeblock(label: string, copyLabel: string, lang: string, code: string)}
	<div class="nb-brutal overflow-x-auto bg-neutral p-4 text-neutral-content md:p-5">
		<div class="mb-3 flex items-center justify-between gap-4">
			<span class="font-mono text-xs font-bold tracking-widest uppercase opacity-70">{label}</span>
			<button class="nb-btn nb-btn-secondary nb-btn-xs" onclick={() => copyCode(code, copyLabel)}>
				{copyFeedback === copyLabel ? 'Copied' : 'Copy'}
			</button>
		</div>
		<pre class="overflow-x-auto font-mono text-sm"><code class="language-{lang}">{code}</code></pre>
	</div>
{/snippet}

<div class="docs-brutal bg-base-100 text-base-content">
	<section class="border-b-2 border-black">
		<div class="mx-auto w-full max-w-6xl px-4 pt-12 pb-10 md:px-8 md:pt-16">
			<p class="nb-muted mb-2 font-mono text-xs font-bold tracking-widest uppercase">Documentation</p>
			<h1 class="text-4xl font-extrabold tracking-tight md:text-5xl">Integration Documentation</h1>
			<p class="nb-muted mt-4 max-w-3xl text-lg font-medium">Connect InferenceBrake to your AI agents in minutes. The Free plan includes 5,000 checks/month; paid plans scale to 100k and 500k per month.</p>
			<p class="mt-2 font-medium">Runnable examples: <a href="https://github.com/InferenceBrake/inferencebrake-examples" target="_blank" rel="noopener">InferenceBrake/inferencebrake-examples</a>.</p>
		</div>
	</section>

	<div class="mx-auto grid w-full max-w-6xl gap-8 px-4 py-12 md:px-8 md:py-16 lg:grid-cols-[240px_minmax(0,1fr)]">
		<aside class="h-fit lg:sticky lg:top-24">
			<div class="nb-card nb-brutal bg-base-100">
				<div class="nb-card-body gap-2 p-4">
					<p class="nb-muted px-2 font-mono text-xs font-bold tracking-widest uppercase">Contents</p>
					<ul class="nb-menu w-full">
						{#each sections as section}
							<li>
								<button
									class="font-medium"
									class:nb-menu-active={activeSection === section.id}
									onclick={() => scrollTo(section.id)}
								>
									{section.label}
								</button>
							</li>
						{/each}
					</ul>
				</div>
			</div>
		</aside>

		<main class="docs-content flex min-w-0 flex-col gap-12">
			<section id="quickstart" class="flex scroll-mt-24 flex-col gap-5">
				<div class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-3 p-6">
						<h2 class="text-xl font-extrabold">Before You Start</h2>
						<ol class="flex list-decimal flex-col gap-2 pl-6 font-medium">
							<li><strong>Sign up</strong> at <a href="https://inferencebrake.dev">inferencebrake.dev</a></li>
							<li><strong>Get your API key</strong> from the Dashboard</li>
						</ol>
					</div>
				</div>
			</section>

			<section id="python" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">Python SDK</h2>
				<p class="nb-muted font-medium">Install the <code>inferencebrake</code> package and start monitoring your agents.</p>

				{@render codeblock('Install', 'pip install', 'bash', codes.pip)}

				<h3 class="text-lg font-extrabold">Basic Usage</h3>
				{@render codeblock('Python', 'basic usage', 'python', codes.pythonBasic)}

				<h3 class="text-lg font-extrabold">Batch Check</h3>
				{@render codeblock('Python', 'batch', 'python', codes.pythonBatch)}

				<h3 class="text-lg font-extrabold">Session History</h3>
				{@render codeblock('Python', 'history', 'python', codes.pythonHistory)}

				<h3 class="text-lg font-extrabold">Configuration</h3>
				{@render codeblock('Python', 'config', 'python', codes.pythonConfig)}
			</section>

			<section id="javascript" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">JavaScript / Node.js SDK</h2>
				<p class="nb-muted font-medium">Built-in resilience: retry logic, circuit breaker, and offline queue.</p>

				{@render codeblock('Install', 'npm', 'bash', codes.npm)}

				<h3 class="text-lg font-extrabold">Basic Usage</h3>
				{@render codeblock('JavaScript', 'js basic', 'javascript', codes.jsBasic)}

				<h3 class="text-lg font-extrabold">Resilience Configuration</h3>
				{@render codeblock('JavaScript', 'js config', 'javascript', codes.jsConfig)}

				<h3 class="text-lg font-extrabold">Monitor Helper</h3>
				{@render codeblock('JavaScript', 'js monitor', 'javascript', codes.jsMonitor)}
			</section>

			<section id="rest" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">REST API</h2>
				<p class="nb-muted font-medium">Use directly from any language or framework via HTTP.</p>

				<h3 class="text-lg font-extrabold">Health Check</h3>
				{@render codeblock('Shell', 'health', 'bash', codes.curlHealth)}

				<h3 class="text-lg font-extrabold">Check Reasoning</h3>
				{@render codeblock('Shell', 'curl', 'bash', codes.curlCheck)}

				<h3 class="text-lg font-extrabold">Response</h3>
				{@render codeblock('JSON', 'response', 'json', codes.responseJson)}
			</section>

			<section id="reference" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">API Reference</h2>

				<h3 class="text-lg font-extrabold">CheckStatus Fields</h3>
				<div class="nb-brutal overflow-x-auto bg-base-100">
					<table class="nb-table text-sm">
						<thead class="font-bold">
							<tr>
								<th>Field</th>
								<th>Type</th>
								<th>Description</th>
							</tr>
						</thead>
						<tbody>
							<tr><td><code>action</code></td><td>string</td><td><code>"KILL"</code> if loop detected, <code>"PROCEED"</code> otherwise</td></tr>
							<tr><td><code>loop_detected</code></td><td>boolean</td><td>Whether a reasoning loop was detected</td></tr>
							<tr><td><code>similarity</code></td><td>float</td><td>Max cosine similarity against recent steps (0.0 - 1.0)</td></tr>
							<tr><td><code>action_repeat_count</code></td><td>int</td><td>Number of consecutive identical actions</td></tr>
							<tr><td><code>ngram_overlap</code></td><td>float</td><td>N-gram overlap ratio with recent steps</td></tr>
							<tr><td><code>confidence</code></td><td>float</td><td>Weighted voting confidence (0.0 - 1.0)</td></tr>
							<tr><td><code>status</code></td><td>string</td><td><code>"safe"</code>, <code>"warning"</code>, or <code>"danger"</code></td></tr>
							<tr><td><code>message</code></td><td>string</td><td>Human-readable status message</td></tr>
							<tr><td><code>test_mode</code></td><td>boolean</td><td>Whether request used test mode API key</td></tr>
						</tbody>
					</table>
				</div>

				<h3 class="text-lg font-extrabold">Detector Fields</h3>
				<div class="nb-brutal overflow-x-auto bg-base-100">
					<table class="nb-table text-sm">
						<thead class="font-bold">
							<tr>
								<th>Detector</th>
								<th>Method</th>
								<th>Best For</th>
							</tr>
						</thead>
						<tbody>
							<tr><td><code>semantic</code></td><td>Embedding cosine similarity</td><td>Paraphrased repetition</td></tr>
							<tr><td><code>token_repeat</code></td><td>Exact repeated token spans</td><td>Verbatim loops (Antidoom / OpenRouter failure mode)</td></tr>
							<tr><td><code>action</code></td><td>Tool call patterns</td><td>Repeated tool invocations</td></tr>
							<tr><td><code>ngram</code></td><td>Text overlap</td><td>Phrase-level repetition</td></tr>
							<tr><td><code>editdist</code></td><td>Normalized Levenshtein</td><td>Near-identical mirror loops</td></tr>
							<tr><td><code>compression</code></td><td>Normalized Compression Distance</td><td>Structural / information theory</td></tr>
						</tbody>
					</table>
				</div>

				<h3 class="text-lg font-extrabold">Rate Limits</h3>
				<div role="note" class="nb-alert nb-alert-info nb-brutal-sm flex-col items-start gap-3">
					<p class="text-sm font-bold">Free plan: 5,000 checks per month per account. Paid plans raise the limit. Counters reset on the 1st.</p>
					<p class="text-sm font-medium">Rate limit headers are returned with every response:</p>
					<ul class="flex list-disc flex-col gap-1 pl-6 text-sm font-medium">
						<li><code>X-RateLimit-Limit</code> - Monthly limit</li>
						<li><code>X-RateLimit-Remaining</code> - Checks remaining this month</li>
						<li><code>X-RateLimit-Period</code> - <code>month</code></li>
						<li><code>X-RateLimit-Reset</code> - Unix timestamp when the quota resets</li>
					</ul>
				</div>

				<h3 class="text-lg font-extrabold">Error Codes</h3>
				<div class="nb-brutal overflow-x-auto bg-base-100">
					<table class="nb-table text-sm">
						<thead class="font-bold">
							<tr>
								<th>Status</th>
								<th>Error</th>
								<th>Cause</th>
							</tr>
						</thead>
						<tbody>
							<tr><td>401</td><td><code>Invalid API Key</code></td><td>Missing or invalid <code>Authorization</code> header</td></tr>
							<tr><td>402</td><td><code>Subscription past due</code></td><td>Payment required</td></tr>
							<tr><td>429</td><td><code>Rate limit exceeded</code></td><td>Daily check limit reached</td></tr>
							<tr><td>500</td><td><code>Internal error</code></td><td>Server-side failure, retry with backoff</td></tr>
						</tbody>
					</table>
				</div>
			</section>

			<section id="integrations" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">Framework Integrations</h2>

				<h3 class="text-lg font-extrabold">LangChain (Python)</h3>
				{@render codeblock('Python', 'langchain', 'python', codes.langchain)}

				<h3 class="text-lg font-extrabold">CrewAI (Python)</h3>
				{@render codeblock('Python', 'crewai', 'python', codes.crewai)}

				<h3 class="text-lg font-extrabold">Python Decorator</h3>
				{@render codeblock('Python', 'decorator', 'python', codes.decorator)}

				<h3 class="text-lg font-extrabold">JavaScript Monitor</h3>
				{@render codeblock('JavaScript', 'js monitor full', 'javascript', codes.jsMonitorFull)}
			</section>

			<section id="escalation" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">Escalation</h2>
				<p class="nb-muted font-medium">Instead of stopping on the first loop, give the agent a chance to recover on a stronger model, then stop if it still loops. The SDK does not pick models; you provide the hook.</p>

				{@render codeblock('Python', 'escalation', 'python', codes.escalation)}

				<div role="note" class="nb-alert nb-alert-info nb-brutal-sm flex-col items-start gap-3">
					<p class="text-sm font-bold">Order of precedence on detection:</p>
					<ol class="flex list-decimal flex-col gap-1 pl-6 text-sm font-medium">
						<li><code>escalate(status, attempt)</code> while under <code>max_escalations</code></li>
						<li><code>on_loop(status)</code></li>
						<li>raise <code>LoopDetectedError</code> when <code>auto_stop</code> is set</li>
					</ol>
					<p class="text-sm font-medium">Use <code>steering_message(status)</code> for a ready-to-inject nudge, and <code>LoopPolicy</code> to apply the same behavior outside a decorator.</p>
				</div>
			</section>

			<section id="analytics" class="flex scroll-mt-24 flex-col gap-5">
				<h2 class="text-2xl font-extrabold md:text-3xl">Analytics</h2>
				<p class="nb-muted font-medium">Attribute loops to the model, tool, and prompt that produced them, not just a total count.</p>

				{@render codeblock('cURL', 'analytics curl', 'bash', codes.analyticsCurl)}
				{@render codeblock('Response', 'analytics json', 'json', codes.analyticsJson)}

				<div role="note" class="nb-alert nb-alert-info nb-brutal-sm">
					<p class="text-sm font-medium">Attribution comes from the <code>model</code>, <code>action</code>, and <code>prompt</code> you pass to <code>check()</code>. Totals reflect retained metrics, so the window is bounded by your plan's retention.</p>
				</div>
			</section>
		</main>
	</div>
</div>

<style>
	.docs-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.docs-brutal h1,
	.docs-brutal h2,
	.docs-brutal h3 {
		color: #171310;
	}

	.docs-brutal .docs-content a {
		font-weight: 700;
		text-decoration: underline;
		text-underline-offset: 3px;
	}

	.docs-brutal .docs-content :not(pre) > code {
		border: 1px solid #171310;
		background: #f6ecd4;
		padding: 0.1rem 0.35rem;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.85em;
		white-space: nowrap;
	}

	.docs-brutal pre code.hljs {
		background: transparent;
	}
</style>
