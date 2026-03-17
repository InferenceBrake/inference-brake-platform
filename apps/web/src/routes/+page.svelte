<script lang="ts">
// Demo state
let demoRunning = $state(false);
let currentStep = $state(0);
let steps: Array<{
	reasoning: string;
	similarity: number;
	safe: boolean;
	stepNum: number;
}> = $state([]);
let detected = $state(false);

const demoSteps = [
	{
		reasoning:
			"Analyzing user's refactoring request for authentication module. Need to identify all auth-related functions across the codebase.",
		similarity: 0,
		safe: true,
	},
	{
		reasoning:
			"Found 3 auth files: auth.py, middleware.py, utils.py. Will refactor to use modern async/await patterns.",
		similarity: 0.12,
		safe: true,
	},
	{
		reasoning:
			"Starting with auth.py - converting sync functions to async. Changed login() to async login(). Testing compatibility.",
		similarity: 0.18,
		safe: true,
	},
	{
		reasoning:
			"Middleware integration looks good. Now should refactor the authentication logic to be more modular and use async patterns throughout.",
		similarity: 0.67,
		safe: false,
	},
	{
		reasoning:
			"I need to refactor this authentication code to use better async/await patterns. Let me restructure the auth module.",
		similarity: 0.84,
		safe: false,
	},
	{
		reasoning:
			"The authentication should be refactored to async. I'll reorganize these auth functions for better async compatibility.",
		similarity: 0.91,
		safe: false,
	},
	{
		reasoning:
			"Looking at authentication refactoring again - should convert these methods to use async/await properly.",
		similarity: 0.94,
		safe: false,
	},
];

function runDemo() {
	if (demoRunning) return;
	demoRunning = true;
	currentStep = 0;
	detected = false;
	steps = [];
	processStep();
}

function processStep() {
	if (currentStep >= demoSteps.length) {
		demoRunning = false;
		return;
	}

	const step = demoSteps[currentStep];
	steps = [...steps, { ...step, stepNum: currentStep + 1 }];

	if (!step.safe && step.similarity > 0.85) {
		detected = true;
		demoRunning = false;
		return;
	}

	currentStep++;
	setTimeout(processStep, 1500);
}

// Code tabs
let activeTab = $state("python");

// Beta waitlist
let betaEmail = $state('');
let betaSubmitting = $state(false);
let betaMessage = $state('');

async function joinBeta() {
	if (!betaEmail || !betaEmail.includes('@')) {
		betaMessage = 'Please enter a valid email';
		return;
	}
	
	betaSubmitting = true;
	betaMessage = '';
	
	try {
		const { supabase } = await import('$lib/supabase');
		const { error } = await supabase
			.from('waitlist')
			.insert({ email: betaEmail });
		
		if (error) {
			if (error.code === '23505') {
				betaMessage = 'You are already on the list!';
			} else {
				betaMessage = 'Failed to join. Please try again.';
			}
		} else {
			betaMessage = 'Welcome to the beta! Check your email to get started.';
			betaEmail = '';
		}
	} catch (e) {
		betaMessage = 'Failed to join. Please try again.';
	} finally {
		betaSubmitting = false;
	}
}
</script>

<svelte:head>
	<title>InferenceBrake - Stop Runaway AI Agents</title>
</svelte:head>

<section class="hero">
	<div class="container">
		<div class="hero-split">
			<div class="hero-solution">
				<h1 class="hero-title">
					Detect Reasoning Loops<br/>
					<span class="text-gradient">Before They Burn Your Budget</span>
				</h1>
				
				<p class="hero-problem-text">
					Runaway AI agents rapidly consume API credits through loops and inefficient retries.
				</p>
				
			<p class="hero-desc">
				Open-source detection system with 5 production detectors and 2 more in development - from embedding similarity to information theory. Runs on Supabase free tier.
			</p>
				
				<div class="hero-cta">
					<a href="#pricing" class="btn btn-primary">Get Started</a>
					<a href="#demo" class="btn btn-secondary">See Demo</a>
				</div>
			</div>
			
			<div class="hero-problem">
				<p class="problem-intro">Real stories from the community:</p>
				
				<div class="reddit-quotes">
					<a href="https://www.reddit.com/r/SaaS/comments/1qv8o6v/my_ai_agent_built_a_runaway_ai_retry_loop_that/" target="_blank" rel="noopener" class="reddit-card worst">
						<div class="reddit-header">
							<span class="reddit-source">r/SaaS</span>
						</div>
						<p class="reddit-text">"My AI agent built a runaway retry loop that cost me over <strong>$700</strong> in a single night"</p>
					</a>
					
					<a href="https://www.reddit.com/r/AI_Agents/comments/1pqsvrs/the_30k_agent_loop_implementing_financial_circuit/" target="_blank" rel="noopener" class="reddit-card">
						<div class="reddit-header">
							<span class="reddit-source">r/AI_Agents</span>
						</div>
						<p class="reddit-text">"<strong>$30,000</strong> in an agent loop implementing a financial circuit breaker"</p>
					</a>
					
					<a href="https://www.reddit.com/r/Python/comments/1rcqa6b/i_burned_14k_in_6_hours_because_an_ai_agent/" target="_blank" rel="noopener" class="reddit-card">
						<div class="reddit-header">
							<span class="reddit-source">r/Python</span>
						</div>
						<p class="reddit-text">"<strong>$1,400</strong> in 6 hours because an AI agent kept retrying"</p>
					</a>

					<a href="https://www.reddit.com/r/cursor/comments/1puodrs/experienced_agent_runaway_burnt_all_monthly/" target="_blank" rel="noopener" class="reddit-card">
						<div class="reddit-header">
							<span class="reddit-source">r/cursor</span>
						</div>
						<p class="reddit-text">"Agent runaway burnt all monthly credits in hours"</p>
					</a>
				</div>
			</div>
		</div>
	</div>
</section>

<section id="detection" class="detection-section">
	<div class="container">
		<div class="section-header">
			<h2>Science Based Detection Methods</h2>
			<p>From information theory to embedding drift</p>
		</div>
		
		<div class="detectors-grid">
			<a class="detector-card" href="https://arxiv.org/abs/2601.11940" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8l4 4-4 4"/></svg>
				<h3>Semantic Similarity</h3>
				<p>Embedding-based cosine similarity. Catches paraphrased repetition and semantic attractors - circular reasoning in vector space.</p>
				<div class="card-footer">
					<span class="detector-badge free">Implemented</span>
					<span class="paper-tag">TAAR 2026</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/2505.23059" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z"/><path d="M9 9h6v6H9z"/></svg>
				<h3>Action Cycles</h3>
				<p>Detects when agents call the same tools repeatedly: search→search→search. Implements state machine reasoning's Stop signal.</p>
				<div class="card-footer">
					<span class="detector-badge free">Implemented</span>
					<span class="paper-tag">SMR 2025</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/2504.12608" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>
				<h3>N-gram Overlap</h3>
				<p>Fast text pattern matching using DeRep's 20-pattern repetition taxonomy. Catches repeated phrases before embeddings notice.</p>
				<div class="card-footer">
					<span class="detector-badge free">Implemented</span>
					<span class="paper-tag">DeRep 2025</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/cs/0111054" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/></svg>
				<h3>Compression (NCD)</h3>
				<p>Information-theoretic similarity via Normalized Compression Distance. Derived from Kolmogorov complexity - zero API cost.</p>
				<div class="card-footer">
					<span class="detector-badge free">Implemented</span>
					<span class="paper-tag">Li et al. 2004</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/2510.21861" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h4l3-9 4 18 3-9h4"/></svg>
				<h3>Edit Distance Decay</h3>
				<p>Directly implements the Mirror Loop paper's delta_I metric. A 55% edit distance decline signals an agent converging on a fixed point.</p>
				<div class="card-footer">
					<span class="detector-badge free">Implemented</span>
					<span class="paper-tag">Mirror Loop 2025</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/2601.05693" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
				<h3>CUSUM Drift</h3>
				<p>Cumulative embedding drift detection. 89% of Long-CoT failures show prefix-dominant deadlocks - CUSUM catches the trajectory early.</p>
				<div class="card-footer">
					<span class="detector-badge coming">Coming to API</span>
					<span class="paper-tag">Duan et al. 2026</span>
				</div>
			</a>

			<a class="detector-card" href="https://arxiv.org/abs/2602.08520" target="_blank" rel="noopener noreferrer">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
				<h3>Entropy Collapse</h3>
				<p>Text-level vocabulary diversity monitoring. When output vocabulary collapses across steps, the loop has set in.</p>
				<div class="card-footer">
					<span class="detector-badge coming">Coming to API</span>
					<span class="paper-tag">Sun 2026</span>
				</div>
			</a>

			<div class="detector-card detector-card--future">
				<svg class="detector-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
				<h3>Verifier Models</h3>
				<p>GPT-4 audit for critical agents. Full semantic understanding as a last-resort check for high-stakes pipelines.</p>
				<div class="card-footer">
					<span class="detector-badge future">Future</span>
				</div>
			</div>
		</div>
	</div>
</section>

<section id="demo" class="demo-section">
	<div class="container">
		<div class="section-header">
			<h2>See It In Action</h2>
			<p>Watch InferenceBrake detect a semantic loop in real-time</p>
		</div>
		
		<div class="demo-container">
			<div class="demo-header">
				<div class="demo-title">
					<span class="demo-dot"></span>
					Agent Monitor
				</div>
				<div class="demo-status">
					{#if detected}
						<span class="status-badge danger">Loop Detected</span>
					{:else if demoRunning}
						<span class="status-badge running">Monitoring...</span>
					{:else}
						<span class="status-badge ready">Ready</span>
					{/if}
				</div>
			</div>
			
			<div class="demo-body">
				<div class="terminal">
					{#each steps as step}
						<div class="terminal-line" class:danger={step.similarity > 0.85} class:warning={step.similarity > 0.5 && step.similarity <= 0.85}>
							<span class="step-num">[{step.stepNum}]</span>
							<span class="step-text">{step.reasoning.slice(0, 80)}...</span>
							<span class="step-sim">({Math.round(step.similarity * 100)}%)</span>
						</div>
					{/each}
					{#if steps.length === 0}
						<div class="terminal-line info">Waiting for agent execution...</div>
					{/if}
					{#if detected}
						<div class="terminal-line danger kill">⚠ CIRCUIT BREAKER TRIGGERED - Agent stopped</div>
					{/if}
				</div>
				
				<div class="demo-metrics">
					<div class="metric">
						<span class="metric-label">Steps</span>
						<span class="metric-value">{steps.length}</span>
					</div>
					<div class="metric">
						<span class="metric-label">Similarity</span>
						<span class="metric-value">{steps.length > 0 ? Math.round(steps[steps.length - 1].similarity * 100) : 0}%</span>
					</div>
					<div class="metric">
						<span class="metric-label">Status</span>
						<span class="metric-value" class:danger={detected}>{detected ? 'LOOP' : 'SAFE'}</span>
					</div>
				</div>
			</div>
			
			<div class="demo-footer">
				<button class="btn btn-primary" onclick={runDemo} disabled={demoRunning}>
					{demoRunning ? 'Running...' : 'Run Demo →'}
				</button>
			</div>
		</div>
	</div>
</section>

<section class="code-section">
	<div class="container">
		<div class="section-header">
			<h2>Integrate in Minutes</h2>
			<p>Add loop detection to any agent in 3 lines of code</p>
		</div>
		
		<div class="code-tabs">
			<button class="code-tab" class:active={activeTab === 'python'} onclick={() => activeTab = 'python'}>Python</button>
			<button class="code-tab" class:active={activeTab === 'node'} onclick={() => activeTab = 'node'}>Node.js</button>
			<button class="code-tab" class:active={activeTab === 'curl'} onclick={() => activeTab = 'curl'}>cURL</button>
		</div>
		
		<div class="code-block">
			{#if activeTab === 'python'}
				<pre class="code python"><code><span class="k">from</span> inferencebrake <span class="k">import</span> InferenceBrake

guard = InferenceBrake(api_key=<span class="s">"ib_key"</span>)

<span class="k">for</span> step <span class="k">in</span> agent.run():
    status = guard.check(step.reasoning, session_id=<span class="s">"agent-1"</span>)
    
    <span class="k">if</span> status.should_stop:
        print(<span class="s">"Loop detected!"</span>)
        <span class="k">break</span></code></pre>
			{:else if activeTab === 'node'}
				<pre class="code node"><code><span class="k">const</span> InferenceBrake = require(<span class="s">'inferencebrake'</span>)

<span class="k">const</span> guard = <span class="k">new</span> InferenceBrake(<span class="s">'ib_key'</span>)

<span class="k">for</span> (step of agent.steps) &#123;
    status = <span class="k">await</span> guard.check(step.reasoning, <span class="s">'agent-1'</span>)
    
    <span class="k">if</span> (status.should_stop) &#123;
        console.log(<span class="s">'Loop detected!'</span>)
        <span class="k">break</span>
    &#125;
&#125;</code></pre>
			{:else}
				<pre class="code curl"><code>curl -X POST https://your-project.supabase.co/functions/v1/check 
  -H "Authorization: Bearer ib_key" 
  -d '&#123;
    "session_id": "agent-1",
    "reasoning": "I should check..."
  &#125;'

<span class="c">// Response</span>
&#123;
  "action": "PROCEED",
  "loop_detected": false,
  "confidence": 0.42
&#125;</code></pre>
			{/if}
		</div>
	</div>
</section>

<section id="pricing" class="pricing-section">
	<div class="container">
		<div class="section-header">
			<h2>Free During Beta</h2>
			<p>All features, no credit card required.</p>
		</div>
		
		<div class="beta-card">
			<div class="beta-badge">Open Beta</div>
			<h3>10,000 checks/day</h3>
			<p class="beta-desc">Full access to all 5 detectors during our public beta. No limits, no credit card, no catch.</p>
			
			<ul class="beta-features">
				<li><span class="check">✓</span> All 5 production detectors</li>
				<li><span class="check">✓</span> Adjustable voting thresholds</li>
				<li><span class="check">✓</span> 90-day history</li>
				<li><span class="check">✓</span> Email support</li>
			</ul>
			
			<div class="beta-signup">
				<input 
					type="email" 
					bind:value={betaEmail} 
					placeholder="Enter your email"
					disabled={betaSubmitting}
				/>
				<button class="btn btn-primary" onclick={joinBeta} disabled={betaSubmitting}>
					{betaSubmitting ? 'Joining...' : 'Get Started Free'}
				</button>
			</div>
			
			{#if betaMessage}
				<div class="beta-message" class:error={!betaMessage.includes('Welcome')}>
					{betaMessage}
				</div>
			{/if}
		</div>
		
		<div class="pro-notice">
			<span>Pro plan coming later with higher limits and early access to new detectors.</span>
			<a href="#pricing" onclick={() => document.getElementById('beta-signup')?.scrollIntoView({behavior: 'smooth'})}>
				Get notified →
			</a>
		</div>
	</div>
</section>

<style>
	/* Hero */
	.hero {
		padding: 6rem 0;
		background: radial-gradient(ellipse at top, rgba(249, 115, 22, 0.08) 0%, transparent 60%);
	}
	
	.hero-split {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 4rem;
		align-items: center;
	}
	
	.hero-solution {
		text-align: left;
	}
	
	.hero-title {
		font-size: 2.5rem;
		line-height: 1.15;
		margin-bottom: 1rem;
	}
	
	.hero-title .text-gradient {
		display: block;
		padding-bottom: 1rem;
	}
	
	.hero-problem-text {
		font-size: 1.1rem;
		color: var(--text-secondary);
		margin-bottom: 1.5rem;
		line-height: 1.5;
	}
	
	.hero-desc {
		font-size: 1.15rem;
		color: var(--text-secondary);
		margin-bottom: 2rem;
		line-height: 1.6;
	}
	
	.hero-cta {
		display: flex;
		gap: 1rem;
	}
	
	.hero-problem {
		padding-left: 2rem;
	}
	
	.problem-intro {
		font-size: 0.9rem;
		color: var(--text-tertiary);
		margin-bottom: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.reddit-quotes {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.reddit-card {
		display: block;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: 1rem;
		transition: transform 0.2s, border-color 0.2s;
		text-decoration: none;
	}
	
	.reddit-card:hover {
		transform: translateY(-2px);
		border-color: var(--accent);
	}
	
	.reddit-card.worst {
		border-color: rgba(239, 68, 68, 0.5);
		background: rgba(239, 68, 68, 0.05);
	}
	
	.reddit-header {
		margin-bottom: 0.5rem;
	}
	
	.reddit-source {
		font-size: 0.75rem;
		color: var(--text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.reddit-text {
		font-size: 0.95rem;
		color: var(--text-primary);
		line-height: 1.4;
	}
	
	@media (max-width: 768px) {
		.hero-split {
			grid-template-columns: 1fr;
			gap: 3rem;
		}
		
		.hero-problem {
			padding-left: 0;
			order: 2;
		}
		
		.hero-solution {
			order: 1;
		}
		
		.hero-title {
			font-size: 2.25rem;
		}
	}
	
	.stat-value {
		display: block;
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-primary);
	}
	
	.stat-label {
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}
	
	/* Section Headers */
	.section-header {
		text-align: center;
		margin-bottom: 4rem;
	}
	
	.section-header h2 {
		margin-bottom: 1rem;
	}
	
	.section-header p {
		font-size: 1.1rem;
	}

	.reddit-link {
		margin-top: 1rem;
	}

	.reddit-link a {
		color: var(--accent);
		text-decoration: underline;
	}

	.reddit-link a:hover {
		opacity: 0.8;
	}
	
	/* Detection Section */
	.detection-section {
		padding: 6rem 0;
		background: var(--bg-secondary);
	}
	
	.detectors-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.detector-card {
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
	}
	
	.detector-card:hover {
		border-color: var(--accent);
		transform: translateY(-4px);
	}
	
	.detector-icon {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-md);
		margin-bottom: 1rem;
		background: var(--bg-tertiary);
	}
	
	.detector-card h3 {
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}
	
	.detector-card p {
		font-size: 0.85rem;
		color: var(--text-tertiary);
		line-height: 1.5;
		margin-bottom: 1rem;
	}
	
	.detector-badge {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		font-size: 0.7rem;
		font-weight: 600;
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.detector-badge.free {
		background: rgba(34, 197, 94, 0.15);
		color: #22c55e;
	}
	
	.detector-badge.pro {
		background: rgba(249, 115, 22, 0.15);
		color: #f97316;
	}
	
	.detector-badge.future {
		background: rgba(115, 115, 115, 0.15);
		color: #737373;
	}

	.detector-badge.coming {
		background: rgba(96, 165, 250, 0.15);
		color: #60a5fa;
	}
	
	.card-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: auto;
	}
	
	/* Demo Section */
	.demo-section {
		padding: 6rem 0;
	}
	
	.demo-container {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-xl);
		overflow: hidden;
		max-width: 900px;
		margin: 0 auto;
	}
	
	.demo-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: var(--bg-tertiary);
		border-bottom: 1px solid var(--border);
	}
	
	.demo-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
	}
	
	.demo-dot {
		width: 8px;
		height: 8px;
		background: var(--accent);
		border-radius: 50%;
		animation: pulse 2s infinite;
	}
	
	.status-badge {
		padding: 0.35rem 0.75rem;
		font-size: 0.8rem;
		font-weight: 600;
		border-radius: var(--radius-full);
	}
	
	.status-badge.ready { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
	.status-badge.running { background: rgba(234, 179, 8, 0.15); color: #eab308; }
	.status-badge.danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
	
	.demo-body {
		display: grid;
		grid-template-columns: 2fr 1fr;
	}
	
	.terminal {
		background: #000;
		padding: 1.5rem;
		font-family: var(--font-mono);
		font-size: 0.8rem;
		min-height: 350px;
		max-height: 350px;
		overflow-y: auto;
	}
	
	.terminal-line {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
		animation: fadeIn 0.3s ease;
	}
	
	.terminal-line.info { color: var(--text-tertiary); }
	.terminal-line.warning { color: #eab308; }
	.terminal-line.danger { color: #ef4444; }
	.terminal-line.kill { 
		margin-top: 1rem; 
		padding-top: 1rem; 
		border-top: 1px solid rgba(239, 68, 68, 0.3);
		font-weight: 600;
	}
	
	.step-num { color: var(--text-tertiary); }
	.step-sim { color: var(--text-tertiary); margin-left: auto; }
	
	.demo-metrics {
		display: flex;
		flex-direction: column;
		gap: 1px;
		background: var(--border);
	}
	
	.metric {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: var(--bg-secondary);
	}
	
	.metric-label {
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}
	
	.metric-value {
		font-family: var(--font-mono);
		font-size: 1.25rem;
		font-weight: 600;
	}
	
	.metric-value.danger { color: #ef4444; }
	
	.demo-footer {
		padding: 1.5rem;
		border-top: 1px solid var(--border);
		text-align: center;
	}
	
	/* Code Section */
	.code-section {
		padding: 6rem 0;
		background: var(--bg-secondary);
	}
	
	.code-tabs {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0;
	}
	
	.code-tab {
		padding: 0.75rem 1.5rem;
		background: transparent;
		border: 1px solid var(--border);
		border-bottom: none;
		border-radius: var(--radius-md) var(--radius-md) 0 0;
		color: var(--text-secondary);
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.code-tab.active {
		background: var(--bg-primary);
		color: var(--text-primary);
	}
	
	.code-block {
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: 0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
		padding: 2rem;
		overflow-x: auto;
	}
	
	.code-block pre {
		margin: 0;
	}
	
	.code-block code {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		line-height: 1.8;
	}
	
	.k { color: #f97316; }
	.s { color: #22c55e; }
	.f { color: #60a5fa; }
	.c { color: var(--text-tertiary); }
	.n { color: #a78bfa; }
	
	/* Pricing Section */
	.pricing-section {
		padding: 6rem 0;
	}
	
	.pricing-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 2rem;
		align-items: stretch;
	}
	
	.pricing-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-xl);
		padding: 2rem;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
	}
	
	.pricing-card .btn {
		margin-top: auto;
	}
	
	.pricing-card:hover {
		border-color: var(--border-hover);
	}
	
	.pricing-card.featured {
		background: linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(249, 115, 22, 0.02) 100%);
		border-color: var(--accent);
		position: relative;
	}
	
	.featured-badge {
		position: absolute;
		top: -12px;
		left: 50%;
		transform: translateX(-50%);
		background: var(--gradient-accent);
		color: white;
		padding: 0.35rem 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: var(--radius-full);
		text-transform: uppercase;
	}
	
	.plan-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.plan-header.coming {
		color: #737373;
	}
	
	.plan-header h3 {
		font-size: 1.25rem;
		margin-bottom: 0.5rem;
	}
	
	.plan-price {
		font-size: 3rem;
		font-weight: 800;
		line-height: 1;
		min-height: 3.5rem;
	}
	
	.plan-price.coming {
		font-size: 2.5rem;
	}
	
	.plan-price span {
		font-size: 1rem;
		color: var(--text-tertiary);
		font-weight: 400;
	}
	
	.plan-header p {
		font-size: 0.9rem;
		color: var(--text-tertiary);
	}
	
	.plan-features {
		list-style: none;
		margin-bottom: 2rem;
	}
	
	.plan-features li {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 0;
		border-bottom: 1px solid var(--border);
		font-size: 0.9rem;
		color: var(--text-secondary);
	}
	
	.plan-features li:last-child {
		border-bottom: none;
	}
	
	.check {
		color: var(--accent);
		font-weight: 600;
	}

	.check.coming {
		color: #737373;
	}
	
	.feature-highlight {
		color: var(--accent);
		font-weight: 600;
	}
	
	/* Beta Card */
	.beta-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-xl);
		padding: 3rem 2rem;
		max-width: 500px;
		margin: 0 auto;
		text-align: center;
	}
	
	.beta-badge {
		display: inline-block;
		background: var(--gradient-accent);
		color: white;
		padding: 0.35rem 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: var(--radius-full);
		text-transform: uppercase;
		margin-bottom: 1.5rem;
	}
	
	.beta-card h3 {
		font-size: 2.5rem;
		font-weight: 800;
		margin-bottom: 0.5rem;
	}
	
	.beta-desc {
		font-size: 1.1rem;
		color: var(--text-secondary);
		margin-bottom: 2rem;
	}
	
	.beta-features {
		list-style: none;
		margin-bottom: 2rem;
		text-align: left;
		display: inline-block;
	}
	
	.beta-features li {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0;
		font-size: 0.95rem;
		color: var(--text-secondary);
	}
	
	.beta-signup {
		display: flex;
		gap: 0.5rem;
		max-width: 400px;
		margin: 0 auto 1rem;
	}
	
	.beta-signup input {
		flex: 1;
		padding: 0.75rem 1rem;
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		color: var(--text-primary);
		font-size: 0.95rem;
	}
	
	.beta-signup input:focus {
		outline: none;
		border-color: var(--accent);
	}
	
	.beta-message {
		font-size: 0.9rem;
		color: var(--success);
	}
	
	.beta-message.error {
		color: var(--danger);
	}
	
	.pro-notice {
		text-align: center;
		margin-top: 2rem;
		font-size: 0.9rem;
		color: var(--text-tertiary);
	}
	
	.pro-notice a {
		color: var(--accent);
		text-decoration: none;
		margin-left: 0.5rem;
	}
	
	@media (max-width: 1024px) {
		.detectors-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.pricing-grid {
			grid-template-columns: 1fr;
			max-width: 400px;
			margin: 0 auto;
		}
	}
	
	@media (max-width: 768px) {
		.hero-split {
			grid-template-columns: 1fr;
			gap: 3rem;
		}
		
		.hero-title {
			font-size: 2rem;
		}
		
		.hero-problem {
			padding-right: 0;
		}
		
		.demo-body {
			grid-template-columns: 1fr;
		}
		
		.detectors-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
