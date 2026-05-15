<script lang="ts">
	import '../../app.css';

	let activeSection = $state('quickstart');
	let copyFeedback = $state<string | null>(null);

	const sections = [
		{ id: 'quickstart', label: 'Quick Start' },
		{ id: 'python', label: 'Python SDK' },
		{ id: 'javascript', label: 'JavaScript SDK' },
		{ id: 'rest', label: 'REST API' },
		{ id: 'reference', label: 'API Reference' },
		{ id: 'integrations', label: 'Integrations' },
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

	const codes = {
		pip: 'pip install inferencebrake',
		npm: 'npm install inferencebrake',
		pythonBasic: `from inferencebrake import InferenceBrake

guard = InferenceBrake(
    api_key="ib_your_key",
    supabase_url="https://yourproject.supabase.co"
)

for step in agent.run():
    status = guard.check(
        reasoning=step.reasoning,
        session_id="agent-session-1"
    )

    if status.should_stop:
        print(f"Loop detected! Similarity: {status.similarity}")
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
    supabase_url="https://yourproject.supabase.co",
    timeout=10,
    auto_stop=False
)`,
		jsBasic: `const { InferenceBrake } = require('inferencebrake');

const guard = new InferenceBrake({
    apiKey: 'ib_your_key',
    supabaseUrl: 'https://yourproject.supabase.co'
});

const status = await guard.check(
    'reasoning text',
    'session-1'
);

if (status.shouldStop) {
    console.log('Loop detected!', status.message);
}`,
		jsConfig: `const guard = new InferenceBrake({
    apiKey: 'ib_your_key',
    supabaseUrl: 'https://yourproject.supabase.co',
    timeout: 10000,
    maxRetries: 3,
    retryDelay: 1000,
    retryBackoff: 2,
    circuitBreakerThreshold: 5,
    circuitBreakerTimeout: 30000,
});`,
		jsMonitor: `const { inferencebrakeMonitor } = require('inferencebrake');

const monitor = inferencebrakeMonitor({
    apiKey: 'ib_your_key',
    supabaseUrl: 'https://yourproject.supabase.co'
});

const status = await monitor.check(reasoning);

monitor.reset('new-session-id');`,
		curlHealth: `curl https://yourproject.supabase.co/functions/v1/health`,
		curlCheck: `curl -X POST https://yourproject.supabase.co/functions/v1/check \\
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
  "action_repeat_count": 0,
  "ngram_overlap": 0.1,
  "detectors": {
    "semantic": false,
    "action": false,
    "ngram": false,
    "editdist": false,
    "compression": false
  },
  "confidence": 0.18,
  "status": "safe",
  "message": "Reasoning sound",
  "usage": {
    "today": 42,
    "limit": 10000,
    "remaining": 9958
  }
}`,
		langchain: `from inferencebrake import InferenceBrakeCallback

callback = InferenceBrakeCallback(
    api_key="ib_your_key",
    supabase_url="https://yourproject.supabase.co"
)

agent = initialize_agent(tools, llm, callbacks=[callback])`,
		crewai: `from inferencebrake import InferenceBrakeCallback

callback = InferenceBrakeCallback(
    api_key="ib_your_key",
    supabase_url="https://yourproject.supabase.co"
)

agent.callbacks = [callback]`,
		decorator: `from inferencebrake import inferencebrake_monitor

@inferencebrake_monitor(
    api_key="ib_your_key",
    supabase_url="https://yourproject.supabase.co"
)
def agent_step(reasoning: str):
    return result`,
		jsMonitorFull: `const { inferencebrakeMonitor } = require('inferencebrake');

const monitor = inferencebrakeMonitor({
    apiKey: 'ib_your_key',
    supabaseUrl: 'https://yourproject.supabase.co',
    sessionId: 'my-agent'
});

const status = await monitor.check(reasoningText);
if (status.shouldStop) {
    // Handle loop
}`,
	};
</script>

<svelte:head>
	<title>Integration Docs - InferenceBrake</title>
	<meta name="description" content="Integrate InferenceBrake loop detection with Python, JavaScript, or REST API." />
</svelte:head>

<div class="docs-layout">
	<aside class="sidebar">
		<nav class="sidebar-nav">
			<h3>Documentation</h3>
			{#each sections as section}
				<button
					class="sidebar-link"
					class:active={activeSection === section.id}
					onclick={() => scrollTo(section.id)}
				>
					{section.label}
				</button>
			{/each}
		</nav>
	</aside>

	<main class="docs-content">
		<section id="quickstart">
			<h1 class="text-gradient">Integration Documentation</h1>
			<p class="lead">Connect InferenceBrake to your AI agents in minutes. All plans include 10,000 checks/day during beta.</p>

			<div class="card highlight-card">
				<h4>Before You Start</h4>
				<ol class="steps-list">
					<li><strong>Sign up</strong> at <a href="https://inferencebrake.dev">inferencebrake.dev</a></li>
					<li><strong>Get your API key</strong> from the Dashboard</li>
					<li><strong>Deploy the edge function</strong> to your Supabase project</li>
				</ol>
			</div>
		</section>

		<section id="python">
			<h2>Python SDK</h2>
			<p>Install the <code>inferencebrake</code> package and start monitoring your agents.</p>

			<div class="code-block">
				<div class="code-header">
					<span>Install</span>
					<button class="copy-btn" onclick={() => copyCode(codes.pip, 'pip install')}>
						{copyFeedback === 'pip install' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.pip}</code></pre>
			</div>

			<h3>Basic Usage</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.pythonBasic, 'basic usage')}>
						{copyFeedback === 'basic usage' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.pythonBasic}</code></pre>
			</div>

			<h3>Batch Check</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.pythonBatch, 'batch')}>
						{copyFeedback === 'batch' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.pythonBatch}</code></pre>
			</div>

			<h3>Session History</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.pythonHistory, 'history')}>
						{copyFeedback === 'history' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.pythonHistory}</code></pre>
			</div>

			<h3>Configuration</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.pythonConfig, 'config')}>
						{copyFeedback === 'config' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.pythonConfig}</code></pre>
			</div>
		</section>

		<section id="javascript">
			<h2>JavaScript / Node.js SDK</h2>
			<p>Built-in resilience: retry logic, circuit breaker, and offline queue.</p>

			<div class="code-block">
				<div class="code-header">
					<span>Install</span>
					<button class="copy-btn" onclick={() => copyCode(codes.npm, 'npm')}>
						{copyFeedback === 'npm' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.npm}</code></pre>
			</div>

			<h3>Basic Usage</h3>
			<div class="code-block">
				<div class="code-header">
					<span>JavaScript</span>
					<button class="copy-btn" onclick={() => copyCode(codes.jsBasic, 'js basic')}>
						{copyFeedback === 'js basic' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.jsBasic}</code></pre>
			</div>

			<h3>Resilience Configuration</h3>
			<div class="code-block">
				<div class="code-header">
					<span>JavaScript</span>
					<button class="copy-btn" onclick={() => copyCode(codes.jsConfig, 'js config')}>
						{copyFeedback === 'js config' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.jsConfig}</code></pre>
			</div>

			<h3>Monitor Helper</h3>
			<div class="code-block">
				<div class="code-header">
					<span>JavaScript</span>
					<button class="copy-btn" onclick={() => copyCode(codes.jsMonitor, 'js monitor')}>
						{copyFeedback === 'js monitor' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.jsMonitor}</code></pre>
			</div>
		</section>

		<section id="rest">
			<h2>REST API</h2>
			<p>Use directly from any language or framework via HTTP.</p>

			<h3>Health Check</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Shell</span>
					<button class="copy-btn" onclick={() => copyCode(codes.curlHealth, 'health')}>
						{copyFeedback === 'health' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.curlHealth}</code></pre>
			</div>

			<h3>Check Reasoning</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Shell</span>
					<button class="copy-btn" onclick={() => copyCode(codes.curlCheck, 'curl')}>
						{copyFeedback === 'curl' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.curlCheck}</code></pre>
			</div>

			<h3>Response</h3>
			<div class="code-block">
				<div class="code-header">
					<span>JSON</span>
					<button class="copy-btn" onclick={() => copyCode(codes.responseJson, 'response')}>
						{copyFeedback === 'response' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.responseJson}</code></pre>
			</div>
		</section>

		<section id="reference">
			<h2>API Reference</h2>

			<h3>CheckStatus Fields</h3>
			<div class="table-wrap">
				<table>
					<thead>
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

			<h3>Detector Fields</h3>
			<div class="table-wrap">
				<table>
					<thead>
						<tr>
							<th>Detector</th>
							<th>Method</th>
							<th>Best For</th>
						</tr>
					</thead>
					<tbody>
						<tr><td><code>semantic</code></td><td>Embedding cosine similarity</td><td>Paraphrased repetition</td></tr>
						<tr><td><code>action</code></td><td>Tool call patterns</td><td>Repeated tool invocations</td></tr>
						<tr><td><code>ngram</code></td><td>Text overlap</td><td>Phrase-level repetition</td></tr>
						<tr><td><code>editdist</code></td><td>Normalized Levenshtein</td><td>Near-identical mirror loops</td></tr>
						<tr><td><code>compression</code></td><td>Normalized Compression Distance</td><td>Structural / information theory</td></tr>
					</tbody>
				</table>
			</div>

			<h3>Rate Limits</h3>
			<div class="card info-card">
				<p><strong>Beta tier:</strong> 10,000 checks per day per account. Resets at midnight UTC.</p>
				<p>Rate limit headers are returned with every response:</p>
				<ul class="header-list">
					<li><code>X-RateLimit-Limit</code> - Daily limit</li>
					<li><code>X-RateLimit-Remaining</code> - Checks remaining today</li>
					<li><code>X-RateLimit-Reset</code> - Unix timestamp when limit resets</li>
				</ul>
			</div>

			<h3>Error Codes</h3>
			<div class="table-wrap">
				<table>
					<thead>
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

		<section id="integrations">
			<h2>Framework Integrations</h2>

			<h3>LangChain (Python)</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.langchain, 'langchain')}>
						{copyFeedback === 'langchain' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.langchain}</code></pre>
			</div>

			<h3>CrewAI (Python)</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.crewai, 'crewai')}>
						{copyFeedback === 'crewai' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.crewai}</code></pre>
			</div>

			<h3>Python Decorator</h3>
			<div class="code-block">
				<div class="code-header">
					<span>Python</span>
					<button class="copy-btn" onclick={() => copyCode(codes.decorator, 'decorator')}>
						{copyFeedback === 'decorator' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.decorator}</code></pre>
			</div>

			<h3>JavaScript Monitor</h3>
			<div class="code-block">
				<div class="code-header">
					<span>JavaScript</span>
					<button class="copy-btn" onclick={() => copyCode(codes.jsMonitorFull, 'js monitor full')}>
						{copyFeedback === 'js monitor full' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<pre><code>{codes.jsMonitorFull}</code></pre>
			</div>
		</section>
	</main>
</div>

<style>
	.docs-layout {
		display: grid;
		grid-template-columns: 240px 1fr;
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		gap: 2rem;
		min-height: calc(100vh - 72px);
	}

	.sidebar {
		position: sticky;
		top: 88px;
		height: fit-content;
		max-height: calc(100vh - 104px);
		overflow-y: auto;
		padding-right: 1rem;
	}

	.sidebar-nav h3 {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-tertiary);
		margin-bottom: 1rem;
	}

	.sidebar-link {
		display: block;
		width: 100%;
		text-align: left;
		padding: 0.5rem 0.75rem;
		margin-bottom: 0.25rem;
		background: none;
		border: none;
		color: var(--text-secondary);
		font-family: var(--font-display);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: all 0.15s;
	}

	.sidebar-link:hover {
		color: var(--text-primary);
		background: var(--bg-tertiary);
	}

	.sidebar-link.active {
		color: var(--accent);
		background: var(--accent-muted);
	}

	.docs-content {
		min-width: 0;
	}

	.docs-content section {
		margin-bottom: 4rem;
		scroll-margin-top: 88px;
	}

	.lead {
		font-size: 1.1rem;
		color: var(--text-secondary);
		margin: 0.5rem 0 2rem;
		max-width: 640px;
	}

	.highlight-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: 1.5rem 2rem;
		margin-bottom: 2rem;
	}

	.highlight-card h4 {
		margin-bottom: 1rem;
	}

	.steps-list {
		margin: 0;
		padding: 0 0 0 1.25rem;
	}

	.steps-list li {
		margin-bottom: 0.5rem;
		color: var(--text-secondary);
		line-height: 1.5;
	}

	.steps-list li strong {
		color: var(--text-primary);
	}

	h2 {
		margin-bottom: 1rem;
	}

	h3 {
		font-size: 1.1rem;
		margin: 1.5rem 0 0.75rem;
		color: var(--text-primary);
	}

	.docs-content p {
		color: var(--text-secondary);
		margin-bottom: 1rem;
		line-height: 1.6;
	}

	.code-block {
		background: #0d0d0d;
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		margin-bottom: 1.5rem;
		overflow: hidden;
	}

	.code-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 1rem;
		background: var(--bg-tertiary);
		border-bottom: 1px solid var(--border);
	}

	.code-header span {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.copy-btn {
		background: none;
		border: 1px solid var(--border);
		color: var(--text-tertiary);
		font-family: var(--font-display);
		font-size: 0.75rem;
		padding: 0.2rem 0.6rem;
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: all 0.15s;
	}

	.copy-btn:hover {
		color: var(--text-primary);
		border-color: var(--border-hover);
		background: var(--bg-elevated);
	}

	.code-block pre {
		padding: 1rem;
		margin: 0;
		overflow-x: auto;
	}

	.code-block code {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		line-height: 1.5;
		color: #e4e4e7;
		white-space: pre;
	}

	code:not(.code-block code) {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		background: var(--bg-tertiary);
		padding: 0.1em 0.3em;
		border-radius: var(--radius-sm);
		color: var(--accent);
	}

	.table-wrap {
		overflow-x: auto;
		margin-bottom: 1.5rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.9rem;
	}

	thead {
		background: var(--bg-tertiary);
	}

	th {
		text-align: left;
		padding: 0.75rem 1rem;
		font-weight: 600;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-tertiary);
		border-bottom: 1px solid var(--border);
	}

	td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
		color: var(--text-secondary);
	}

	td:first-child {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--accent);
		white-space: nowrap;
	}

	.info-card {
		background: rgba(249, 115, 22, 0.05);
		border: 1px solid rgba(249, 115, 22, 0.2);
		border-radius: var(--radius-md);
		padding: 1.25rem 1.5rem;
		margin-bottom: 1.5rem;
	}

	.info-card p {
		margin-bottom: 0.5rem;
	}

	.header-list {
		margin: 0.75rem 0 0;
		padding: 0 0 0 1.25rem;
	}

	.header-list li {
		margin-bottom: 0.25rem;
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	@media (max-width: 768px) {
		.docs-layout {
			grid-template-columns: 1fr;
			padding: 1.5rem;
		}

		.sidebar {
			display: none;
		}
	}
</style>
