<script lang="ts">
	import { onMount } from 'svelte';
	import DotGlobe from '$lib/components/DotGlobe.svelte';
	import RetroWindow from '$lib/components/RetroWindow.svelte';

	// Code tabs
	let activeTab = $state("python");

	// Retro clock window
	let now = $state(new Date());

	onMount(() => {
		const id = setInterval(() => (now = new Date()), 1000);
		return () => clearInterval(id);
	});

	const dateLabel = $derived(
		now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })
	);
	const timeLabel = $derived(now.toLocaleTimeString('en-US', { hour12: false }));
</script>

<svelte:head>
	<title>InferenceBrake - Stop Runaway AI Agents</title>
</svelte:head>

<div class="landing-brutal bg-base-100 text-base-content">
<!-- Hero -->
<section class="nb-frame relative overflow-hidden border-b-2 border-base-content">
	<div class="nb-dither nb-dither-bl" aria-hidden="true"></div>
	<div class="relative z-10 mx-auto w-full max-w-6xl px-4 pt-12 pb-12 md:px-8 md:pt-20 md:pb-16">
		<div class="grid items-center gap-10 md:gap-14 lg:grid-cols-2">
			<div>
				<p class="mb-4"><span class="nb-tag">Multi-detector loop detection</span></p>
				<h1 class="text-4xl font-extrabold tracking-tight md:text-6xl">
					Detect Reasoning Loops
					<span class="mt-3 block w-fit border-2 border-base-content bg-primary px-3 py-1">Before They Burn Your Budget</span>
				</h1>

				<p class="nb-muted mt-6 text-lg font-medium">
					Runaway AI agents rapidly consume API credits through loops and inefficient retries.
				</p>

				<p class="nb-muted mt-4 font-medium">
					Open-source detection system with 6 production detectors and 2 more in development - from embedding similarity and exact token repeats to information theory. Runs on Supabase free tier.
				</p>

<div class="mt-8 flex flex-wrap gap-4">
				<a href="#pricing" class="nb-btn nb-btn-primary nb-brutal nb-brutal-press nb-pop text-base">Get Started</a>
				<a href="#demo" class="nb-btn nb-btn-neutral nb-brutal nb-brutal-press nb-pop text-base">See Demo</a>
			</div>
			</div>

			<div class="lg:border-l-2 lg:border-base-content lg:pl-8">
				<p class="mb-4"><span class="nb-tag">Real stories from the community</span></p>

				<div class="flex flex-col gap-4">
					<a href="https://www.reddit.com/r/SaaS/comments/1qv8o6v/my_ai_agent_built_a_runaway_ai_retry_loop_that/" target="_blank" rel="noopener" class="nb-card nb-brutal nb-brutal-press bg-base-100 nb-bounce-in" style="animation-delay: 0ms;">
						<div class="nb-card-body gap-2 p-5">
							<div class="flex items-center justify-between gap-2">
								<span class="nb-muted font-mono text-xs font-bold">r/SaaS</span>
								<span class="nb-badge nb-badge-error font-mono text-xs font-bold">-$700</span>
							</div>
							<p class="text-sm font-semibold">"My AI agent built a runaway retry loop that cost me over <strong>$700</strong> in a single night"</p>
						</div>
					</a>

					<a href="https://www.reddit.com/r/AI_Agents/comments/1pqsvrs/the_30k_agent_loop_implementing_financial_circuit/" target="_blank" rel="noopener" class="nb-card nb-brutal nb-brutal-press bg-base-100 nb-bounce-in" style="animation-delay: 100ms;">
						<div class="nb-card-body gap-2 p-5">
							<div class="flex items-center justify-between gap-2">
								<span class="nb-muted font-mono text-xs font-bold">r/AI_Agents</span>
								<span class="nb-badge nb-badge-error font-mono text-xs font-bold">-$30,000</span>
							</div>
							<p class="text-sm font-semibold">"<strong>$30,000</strong> in an agent loop implementing a financial circuit breaker"</p>
						</div>
					</a>

					<a href="https://www.reddit.com/r/Python/comments/1rcqa6b/i_burned_14k_in_6_hours_because_an_ai_agent/" target="_blank" rel="noopener" class="nb-card nb-brutal nb-brutal-press bg-base-100 nb-bounce-in" style="animation-delay: 200ms;">
						<div class="nb-card-body gap-2 p-5">
							<div class="flex items-center justify-between gap-2">
								<span class="nb-muted font-mono text-xs font-bold">r/Python</span>
								<span class="nb-badge nb-badge-error font-mono text-xs font-bold">-$1,400</span>
							</div>
							<p class="text-sm font-semibold">"<strong>$1,400</strong> in 6 hours because an AI agent kept retrying"</p>
						</div>
					</a>

					<a href="https://www.reddit.com/r/cursor/comments/1puodrs/experienced_agent_runaway_burnt_all_monthly/" target="_blank" rel="noopener" class="nb-card nb-brutal nb-brutal-press bg-base-100 nb-bounce-in" style="animation-delay: 300ms;">
						<div class="nb-card-body gap-2 p-5">
							<div class="flex items-center justify-between gap-2">
								<span class="nb-muted font-mono text-xs font-bold">r/cursor</span>
							</div>
							<p class="text-sm font-semibold">"Agent runaway burnt all monthly credits in hours"</p>
						</div>
					</a>
				</div>

				<p class="nb-muted mt-8 mb-4 font-mono text-xs font-bold tracking-widest uppercase">Why built-ins don't save you:</p>
				<ul class="nb-menu nb-brutal w-full bg-base-100">
					<li><span class="text-sm font-medium">Provider flags only cover their own stack, and users find them after the bill. Common reply: didn't even know the feature existed.</span></li>
					<li><span class="text-sm font-medium">Training-time fixes don't halt a live agent burning budget tonight.</span></li>
					<li><a href="https://getunblocked.com/blog/ai-agent-doom-loop/" target="_blank" rel="noopener" class="text-sm font-medium">82% of developers hit repeated AI agent failures</a></li>
				</ul>
			</div>
		</div>
	</div>
</section>

<!-- Detection -->
<section id="detection" class="relative overflow-hidden border-b-2 border-base-content bg-base-200">
	<div class="nb-dither nb-dither-pink nb-dither-tr" aria-hidden="true"></div>
	<div class="relative z-10 mx-auto w-full max-w-6xl px-4 py-16 md:px-8 md:py-24">
		<p class="mb-3"><span class="nb-tag">01 / Detection methods</span></p>
		<h2 class="mb-2 text-3xl font-extrabold md:text-4xl">Science Based Detection Methods</h2>
		<p class="nb-muted mb-10 font-medium md:mb-12">From embedding similarity and exact repeats to information theory</p>

		<div class="grid gap-5 md:grid-cols-2 md:gap-8 lg:grid-cols-4 stagger-children">
			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2601.11940" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-primary text-primary-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8l4 4-4 4"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Semantic Similarity</h3>
					<p class="nb-muted text-sm font-medium">Embedding-based cosine similarity. Catches paraphrased repetition and semantic attractors - circular reasoning in vector space.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">TAAR 2026</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://github.com/Liquid4All/antidoom" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-secondary text-secondary-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 2l4 4-4 4"/><path d="M3 11v-1a4 4 0 014-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v1a4 4 0 01-4 4H3"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Token Repeat</h3>
					<p class="nb-muted text-sm font-medium">Exact repeated token spans, within a response and across steps. The verbatim loop Antidoom targets at training time, caught here at runtime.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">Antidoom 2026</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2505.23059" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-accent text-accent-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 4h16v16H4z"/><path d="M9 9h6v6H9z"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Action Cycles</h3>
					<p class="nb-muted text-sm font-medium">Detects when agents call the same tools repeatedly: search→search→search. Implements state machine reasoning's Stop signal.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">SMR 2025</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2504.12608" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-success text-success-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>
					</div>
					<h3 class="text-base font-extrabold">N-gram Overlap</h3>
					<p class="nb-muted text-sm font-medium">Fast text pattern matching using DeRep's 20-pattern repetition taxonomy. Catches repeated phrases before embeddings notice.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">DeRep 2025</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/cs/0111054" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-warning text-warning-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Compression (NCD)</h3>
					<p class="nb-muted text-sm font-medium">Information-theoretic similarity via Normalized Compression Distance. Derived from Kolmogorov complexity - zero API cost.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">Li et al. 2004</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2510.21861" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-error text-error-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12h4l3-9 4 18 3-9h4"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Edit Distance Decay</h3>
					<p class="nb-muted text-sm font-medium">Directly implements the Mirror Loop paper's delta_I metric. A 55% edit distance decline signals an agent converging on a fixed point.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-success font-mono text-xs font-bold">Implemented</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">Mirror Loop 2025</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2601.05693" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-neutral text-neutral-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
					</div>
					<h3 class="text-base font-extrabold">CUSUM Drift</h3>
					<p class="nb-muted text-sm font-medium">Cumulative embedding drift detection. 89% of Long-CoT failures show prefix-dominant deadlocks - CUSUM catches the trajectory early.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-warning font-mono text-xs font-bold">Coming to API</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">Duan et al. 2026</span>
					</div>
				</div>
			</a>

			<a class="nb-card nb-brutal nb-brutal-press bg-base-100" href="https://arxiv.org/abs/2602.08520" target="_blank" rel="noopener noreferrer">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-neutral text-neutral-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Entropy Collapse</h3>
					<p class="nb-muted text-sm font-medium">Text-level vocabulary diversity monitoring. When output vocabulary collapses across steps, the loop has set in.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-warning font-mono text-xs font-bold">Coming to API</span>
						<span class="nb-badge nb-badge-outline font-mono text-xs">Sun 2026</span>
					</div>
				</div>
			</a>

			<div class="nb-card nb-brutal bg-base-100">
				<div class="nb-card-body gap-3 p-6">
					<div class="nb-brutal-sm flex size-12 items-center justify-center bg-neutral text-neutral-content">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
					</div>
					<h3 class="text-base font-extrabold">Verifier Models</h3>
					<p class="nb-muted text-sm font-medium">GPT-4 audit for critical agents. Full semantic understanding as a last-resort check for high-stakes pipelines.</p>
					<div class="mt-2 flex flex-wrap gap-2">
						<span class="nb-badge nb-badge-neutral font-mono text-xs font-bold">Future</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- Demo -->
<section id="demo" class="nb-frame relative overflow-hidden border-b-2 border-base-content">
	<div class="nb-dither nb-dither-tr" aria-hidden="true"></div>
	<div class="relative z-10 mx-auto w-full max-w-6xl px-4 py-16 md:px-8 md:py-24">
		<p class="mb-3"><span class="nb-tag">02 / Live demo</span></p>
		<h2 class="mb-2 text-3xl font-extrabold md:text-4xl">See It In Action</h2>
		<p class="nb-muted mb-10 font-medium md:mb-12">A real agent loop detected and halted in the terminal</p>

		<div class="relative">
			<div class="pointer-events-none absolute -top-6 right-0 z-20 hidden w-52 rotate-[1.5deg] md:block">
				<RetroWindow title="Clock Tool 1.1" bodyClass="bg-base-100 p-3 font-pixel text-xs leading-relaxed">
					<p class="text-base-content/70">{dateLabel}</p>
					<p class="mt-1 text-lg">{timeLabel}</p>
				</RetroWindow>
			</div>

			<div class="pointer-events-none absolute -bottom-12 -left-12 z-20 hidden opacity-80 md:block">
				<DotGlobe size={190} color="var(--color-accent)" />
			</div>

			<div class="nb-window relative z-10 mx-auto w-full max-w-4xl overflow-hidden">
				<div class="nb-window-bar">
					<span>demo — loop halted</span>
					<span class="nb-window-bar-dots" aria-hidden="true"><i></i><i></i><i></i></span>
				</div>
				<img
					src="/demo.gif"
					alt="InferenceBrake detecting and halting a real agent reasoning loop in a terminal"
					loading="lazy"
					class="block w-full"
				/>
			</div>
		</div>
	</div>
</section>

<!-- Wild -->
<section class="relative overflow-hidden border-b-2 border-base-content bg-base-200">
	<div class="nb-dither nb-dither-bl" aria-hidden="true"></div>
	<div class="relative z-10 mx-auto w-full max-w-6xl px-4 py-16 md:px-8 md:py-24">
		<p class="mb-3"><span class="nb-tag">03 / In the wild</span></p>
		<h2 class="mb-2 text-3xl font-extrabold md:text-4xl">Doom Loops Happen in Your Editor</h2>
		<p class="nb-muted mb-10 font-medium md:mb-12">A coding agent stuck repeating the same constraint. Every step re-billed, no progress.</p>

		<div class="grid gap-8 md:grid-cols-2">
			<!-- OpenCode Loop -->
			<div class="nb-window overflow-hidden">
				<div class="nb-window-bar">
					<span>opencode — doom loop</span>
					<span class="nb-window-bar-dots" aria-hidden="true"><i></i><i></i><i></i></span>
				</div>
				<video
					autoplay
					loop
					muted
					playsinline
					preload="metadata"
					poster="/opencode-doomloop-poster.jpg"
					aria-label="OpenCode getting stuck in a doom loop"
					class="block w-full"
				>
					<source src="/opencode-doomloop.webm" type="video/webm" />
					<source src="/opencode-doomloop.mp4" type="video/mp4" />
				</video>
				<p class="nb-muted p-4 text-center text-sm font-medium">OpenCode AI assistant in a doom loop</p>
			</div>

			<!-- VSCode Loop -->
			<div class="nb-window overflow-hidden">
				<div class="nb-window-bar">
					<span>vs code — doom loop</span>
					<span class="nb-window-bar-dots" aria-hidden="true"><i></i><i></i><i></i></span>
				</div>
				<video
					autoplay
					loop
					muted
					playsinline
					preload="metadata"
					poster="/vscode-doomloop-poster.jpg"
					aria-label="A coding agent repeating the same sentence in a loop"
					class="block w-full"
				>
					<source src="/vscode-doomloop.webm" type="video/webm" />
					<source src="/vscode-doomloop.mp4" type="video/mp4" />
				</video>
				<p class="nb-muted p-4 text-center text-sm font-medium">Recorded from a real agent session. InferenceBrake halts this at the first repeat, not the hundredth.</p>
			</div>
		</div>
	</div>
</section>

<!-- Code -->
<section class="border-b-2 border-base-content">
	<div class="mx-auto w-full max-w-6xl px-4 py-16 md:px-8 md:py-24">
		<p class="mb-3"><span class="nb-tag">04 / Integration</span></p>
		<h2 class="mb-2 text-3xl font-extrabold md:text-4xl">Integrate in Minutes</h2>
		<p class="nb-muted mb-10 font-medium md:mb-12">Add loop detection to any agent in 3 lines of code</p>

		<div role="tablist" class="nb-tabs nb-tabs-box mb-6 w-fit border-2 border-base-content">
			<button role="tab" class="nb-tab font-mono text-sm font-bold" class:nb-tab-active={activeTab === 'python'} onclick={() => activeTab = 'python'}>Python</button>
			<button role="tab" class="nb-tab font-mono text-sm font-bold" class:nb-tab-active={activeTab === 'node'} onclick={() => activeTab = 'node'}>Node.js</button>
			<button role="tab" class="nb-tab font-mono text-sm font-bold" class:nb-tab-active={activeTab === 'curl'} onclick={() => activeTab = 'curl'}>cURL</button>
		</div>

		<div class="nb-window overflow-hidden">
			<div class="nb-window-bar">
				<span>integration — {activeTab}</span>
				<span class="nb-window-bar-dots" aria-hidden="true"><i></i><i></i><i></i></span>
			</div>
			<div class="nb-terminal overflow-x-auto p-6 md:p-8">
			{#if activeTab === 'python'}
				<pre class="font-mono text-sm leading-relaxed"><code><span class="k">from</span> inferencebrake <span class="k">import</span> InferenceBrake

guard = InferenceBrake(api_key=<span class="s">"ib_key"</span>)

<span class="k">for</span> step <span class="k">in</span> agent.run():
    status = guard.check(step.reasoning, session_id=<span class="s">"agent-1"</span>)
    
    <span class="k">if</span> status.should_stop:
        print(<span class="s">"Loop detected!"</span>)
        <span class="k">break</span></code></pre>
			{:else if activeTab === 'node'}
				<pre class="font-mono text-sm leading-relaxed"><code><span class="k">const</span> InferenceBrake = require(<span class="s">'inferencebrake'</span>)

<span class="k">const</span> guard = <span class="k">new</span> InferenceBrake(<span class="s">'ib_key'</span>)

<span class="k">for</span> (step of agent.steps) &#123;
    status = <span class="k">await</span> guard.check(step.reasoning, <span class="s">'agent-1'</span>)
    
    <span class="k">if</span> (status.should_stop) &#123;
        console.log(<span class="s">'Loop detected!'</span>)
        <span class="k">break</span>
    &#125;
&#125;</code></pre>
			{:else}
				<pre class="font-mono text-sm leading-relaxed"><code>curl -X POST https://your-project.supabase.co/functions/v1/check 
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
	</div>
</section>

<!-- Pricing -->
<section id="pricing" class="relative overflow-hidden border-b-2 border-base-content bg-base-200">
	<div class="nb-dither nb-dither-pink nb-dither-tr" aria-hidden="true"></div>
	<div class="relative z-10 mx-auto w-full max-w-6xl px-4 py-16 md:px-8 md:py-24">
		<p class="mb-3"><span class="nb-tag">05 / Pricing</span></p>
		<h2 class="mb-2 text-3xl font-extrabold md:text-4xl">Simple, usage-based pricing</h2>
		<p class="nb-muted mb-10 font-medium md:mb-12">Scale with the number of agent steps you monitor. Cancel anytime.</p>

		<div class="grid items-stretch gap-5 md:gap-8 lg:grid-cols-3">
			<div class="nb-card nb-brutal bg-base-100">
				<div class="nb-card-body gap-4 p-6 md:p-8">
					<h3 class="text-xl font-extrabold">Free</h3>
					<p class="font-mono text-5xl font-extrabold">$0<span class="price-meta text-base font-bold">/mo</span></p>
					<p class="price-meta text-sm font-medium">5,000 checks/month. No credit card required.</p>
					<ul class="flex flex-1 flex-col gap-2">
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> All 6 production detectors</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> 7-day log retention</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> Email support</li>
					</ul>
					<a href="/register" class="nb-btn nb-btn-neutral nb-brutal-press mt-auto w-full">Get started free</a>
				</div>
			</div>

			<div class="nb-card nb-brutal bg-primary text-primary-content">
				<div class="nb-card-body gap-4 p-6 md:p-8">
					<h3 class="text-xl font-extrabold">Growth</h3>
					<p class="font-mono text-5xl font-extrabold">$49<span class="text-base font-bold">/mo</span></p>
					<p class="text-sm font-medium">100,000 checks/month for production agents.</p>
					<ul class="flex flex-1 flex-col gap-2">
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold">✓</span> All 6 production detectors</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold">✓</span> Slack + webhook alerts</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold">✓</span> Est. dollars-saved dashboard</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold">✓</span> 30-day log retention</li>
					</ul>
					<a href="/register" class="nb-btn nb-btn-neutral nb-brutal-press mt-auto w-full">Start with Growth</a>
				</div>
			</div>

			<div class="nb-card nb-brutal bg-base-100">
				<div class="nb-card-body gap-4 p-6 md:p-8">
					<h3 class="text-xl font-extrabold">Pro</h3>
					<p class="font-mono text-5xl font-extrabold">$199<span class="price-meta text-base font-bold">/mo</span></p>
					<p class="price-meta text-sm font-medium">500,000 checks/month and priority latency.</p>
					<ul class="flex flex-1 flex-col gap-2">
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> All 6 production detectors</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> Custom voting thresholds</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> Priority API latency</li>
						<li class="flex items-center gap-3 text-sm font-medium"><span class="font-bold text-success">✓</span> 90-day log retention</li>
					</ul>
					<a href="/register" class="nb-btn nb-btn-neutral nb-brutal-press mt-auto w-full">Start with Pro</a>
				</div>
			</div>
		</div>

		<p class="nb-muted mt-8 text-center text-sm font-medium">Paid plans require a free account. Upgrade from the dashboard after signing up.</p>
	</div>
</section>
</div>

<style>
	.landing-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.landing-brutal h1,
	.landing-brutal h2,
	.landing-brutal h3 {
		color: var(--color-base-content);
	}

	.landing-brutal .k { color: #f97316; }
	.landing-brutal .s { color: #34d399; }
	.landing-brutal .c { color: #8a8474; }

	/* Pricing meta text: readable small print */
	.landing-brutal .price-meta { color: var(--nb-muted); }
</style>
