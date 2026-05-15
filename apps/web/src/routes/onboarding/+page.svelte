<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let step = $state(1);
	let apiKey = $state('');
	let apiKeyCopied = $state(false);
	let showApiKey = $state(false);
	let sdkTab = $state<'python' | 'nodejs'>('python');
	let loading = $state(true);
	let completing = $state(false);
	let error = $state('');

	onMount(async () => {
		try {
			const saved = localStorage.getItem('onboarding_step');
			if (saved) step = parseInt(saved, 10);

			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) {
				goto('/login');
				return;
			}

			const { data: userData, error: userError } = await supabase
				.from('users')
				.select('api_key, onboarding_completed')
				.eq('id', authUser.id)
				.single();

			if (userData?.onboarding_completed) {
				goto('/dashboard');
				return;
			}

			if (userData?.api_key) {
				apiKey = userData.api_key;
				localStorage.setItem('inferencebrake_api_key', userData.api_key);
			}

			// Fallback: fetch API key via edge function if direct query failed
			if (!apiKey) {
				const { data: fnData } = await supabase.functions.invoke('get-api-key');
				if (fnData?.api_key) {
					apiKey = fnData.api_key;
					localStorage.setItem('inferencebrake_api_key', fnData.api_key);
				}
			}

			loading = false;
		} catch (e) {
			console.error('Onboarding load error:', e);
			error = 'Failed to load your account. Please refresh or contact support.';
			loading = false;
		}
	});

	function saveStep(s: number) {
		step = s;
		localStorage.setItem('onboarding_step', s.toString());
	}

	async function completeOnboarding() {
		completing = true;
		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) {
				goto('/login');
				return;
			}

			const { error: updateError } = await supabase
				.from('users')
				.update({ onboarding_completed: true })
				.eq('id', authUser.id);

			if (updateError) {
				console.error('Onboarding completion error:', updateError);
				error = 'Failed to complete onboarding. Please try again.';
				completing = false;
				return;
			}

			localStorage.removeItem('onboarding_step');
			goto('/dashboard');
		} catch (e) {
			error = 'Something went wrong. Please try again.';
			completing = false;
		}
	}

	async function handleCopyKey() {
		await navigator.clipboard.writeText(apiKey);
		apiKeyCopied = true;
		saveStep(3);
	}
</script>

<svelte:head>
	<title>Get Started - InferenceBrake</title>
</svelte:head>

<div class="onboarding-page">
	<div class="onboarding-card">
		<div class="onboarding-progress">
			<div class="progress-dots">
				{#each [1, 2, 3, 4] as s}
					<button
						class="progress-dot"
						class:active={s === step}
						class:done={s < step}
						disabled
					>
						{#if s < step}
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
						{:else}
							{s}
						{/if}
					</button>
				{/each}
			</div>
			<div class="progress-labels">
				<span class:active={step === 1} class:done={step > 1}>Welcome</span>
				<span class:active={step === 2} class:done={step > 2}>API Key</span>
				<span class:active={step === 3} class:done={step > 3}>SDK</span>
				<span class:active={step === 4} class:done={step > 4}>Integrate</span>
			</div>
		</div>

		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>Loading...</p>
			</div>
		{:else if step === 1}
			<div class="step-content animate-in">
				<div class="step-icon welcome-icon">
					<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
				</div>
				<h1>Welcome to InferenceBrake</h1>
				<p class="step-desc">
					InferenceBrake detects when your AI agent gets stuck in reasoning loops and stops it before it burns through your budget. Set up in under 2 minutes.
				</p>
				<div class="feature-list">
					<div class="feature-item">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
						<span>3 detection methods working together</span>
					</div>
					<div class="feature-item">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
						<span>Works with any LLM provider</span>
					</div>
					<div class="feature-item">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
						<span>Free tier: 10,000 checks per day</span>
					</div>
				</div>
				<button class="btn btn-primary btn-lg" onclick={() => saveStep(2)}>
					Get Started
				</button>
			</div>

		{:else if step === 2}
			<div class="step-content animate-in">
				<div class="step-icon key-icon">
					<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
				</div>
				<h2>Your API Key</h2>
				<p class="step-desc">This key authenticates your requests. Copy it now — you will need it in the next step.</p>

				<div class="key-display">
					<code class="key-value">{showApiKey ? apiKey : apiKey.slice(0, 8) + '...' + apiKey.slice(-4)}</code>
				</div>

				<div class="key-actions">
					<button class="btn btn-primary" onclick={handleCopyKey}>
						{apiKeyCopied ? 'Copied!' : 'Copy Key'}
					</button>
					<button class="btn btn-secondary" onclick={() => showApiKey = !showApiKey}>
						{showApiKey ? 'Hide' : 'Show'}
					</button>
				</div>

				<p class="key-hint">This key is shown only once during onboarding. Store it securely.</p>

				<button class="btn btn-secondary" onclick={() => saveStep(3)} disabled={!apiKeyCopied}>
					Next Step
				</button>
			</div>

		{:else if step === 3}
			<div class="step-content animate-in">
				<div class="step-icon sdk-icon">
					<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
				</div>
				<h2>Install the SDK</h2>
				<p class="step-desc">Add InferenceBrake to your project with one command.</p>

				<div class="sdk-tabs">
					<button
						class="sdk-tab"
						class:active={sdkTab === 'python'}
						onclick={() => sdkTab = 'python'}
					>Python</button>
					<button
						class="sdk-tab"
						class:active={sdkTab === 'nodejs'}
						onclick={() => sdkTab = 'nodejs'}
					>Node.js</button>
				</div>

				<pre class="code-block"><code>{sdkTab === 'python' ? 'pip install inferencebrake' : 'npm install inferencebrake'}</code></pre>

				<p class="step-desc secondary">Then import it in your code:</p>

				<pre class="code-block"><code>{sdkTab === 'python'
	? 'from inferencebrake import InferenceBrake\n\nguard = InferenceBrake(api_key="YOUR_API_KEY")'
	: 'const { InferenceBrake } = require("inferencebrake");\n\nconst guard = new InferenceBrake({ apiKey: "YOUR_API_KEY" });'
}</code></pre>

				<button class="btn btn-primary" onclick={() => saveStep(4)}>
					Next Step
				</button>
			</div>

		{:else if step === 4}
			<div class="step-content animate-in">
				<div class="step-icon integrate-icon">
					<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
				</div>
				<h2>Add to Your Agent</h2>
				<p class="step-desc">Wrap your agent loop with loop detection.</p>

				<pre class="code-block code-block-lg"><code>from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="{apiKey.slice(0, 8)}...")

for step in agent.run():
    result = guard.check(
        reasoning=step["reasoning"],
        agent_id="my-agent"
    )
    if result.should_stop:
        print("Loop detected!")
        break</code></pre>

				<div class="step-info">
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
					<span>Use your API key as the <code>api_key</code> parameter.</span>
				</div>

				{#if error}
					<div class="error-msg">{error}</div>
				{/if}

				<div class="final-actions">
					<button class="btn btn-primary btn-lg" onclick={completeOnboarding} disabled={completing}>
						{completing ? 'Completing...' : 'Go to Dashboard'}
					</button>
					<a href="/docs" class="btn btn-secondary">Read Docs</a>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.onboarding-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		background: radial-gradient(ellipse at top, rgba(249, 115, 22, 0.06) 0%, transparent 60%);
	}

	.onboarding-card {
		width: 100%;
		max-width: 560px;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-xl);
		padding: 2.5rem;
	}

	.onboarding-progress {
		margin-bottom: 2.5rem;
	}

	.progress-dots {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.progress-dot {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 2px solid var(--border);
		background: transparent;
		color: var(--text-tertiary);
		font-size: 0.85rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: default;
		transition: all 0.3s ease;
	}

	.progress-dot.active {
		border-color: var(--accent);
		background: var(--accent);
		color: white;
	}

	.progress-dot.done {
		border-color: var(--success);
		background: var(--success);
		color: white;
	}

	.progress-labels {
		display: flex;
		justify-content: space-between;
		padding: 0 0.25rem;
	}

	.progress-labels span {
		font-size: 0.75rem;
		color: var(--text-tertiary);
		transition: color 0.3s ease;
	}

	.progress-labels span.active {
		color: var(--accent);
		font-weight: 600;
	}

	.progress-labels span.done {
		color: var(--success);
	}

	.step-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: 1rem;
	}

	.animate-in {
		animation: fadeIn 0.4s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(12px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.step-icon {
		width: 80px;
		height: 80px;
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 0.5rem;
	}

	.welcome-icon {
		background: rgba(249, 115, 22, 0.12);
		color: var(--accent);
	}

	.key-icon {
		background: rgba(99, 102, 241, 0.12);
		color: #818cf8;
	}

	.sdk-icon {
		background: rgba(34, 197, 94, 0.12);
		color: var(--success);
	}

	.integrate-icon {
		background: rgba(249, 115, 22, 0.12);
		color: var(--accent);
	}

	h1 {
		font-size: 1.75rem;
	}

	h2 {
		font-size: 1.5rem;
	}

	.step-desc {
		color: var(--text-secondary);
		font-size: 0.95rem;
		max-width: 420px;
		line-height: 1.6;
	}

	.step-desc.secondary {
		margin-top: 0.5rem;
		font-size: 0.85rem;
	}

	.feature-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		text-align: left;
		width: 100%;
		max-width: 360px;
		margin: 0.5rem 0;
	}

	.feature-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.feature-item svg {
		color: var(--success);
		flex-shrink: 0;
	}

	.key-display {
		width: 100%;
		padding: 1rem;
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		margin: 0.5rem 0;
	}

	.key-value {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		word-break: break-all;
		color: var(--text-primary);
	}

	.key-actions {
		display: flex;
		gap: 0.75rem;
	}

	.key-hint {
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.sdk-tabs {
		display: flex;
		gap: 0.25rem;
		background: var(--bg-primary);
		padding: 0.25rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--border);
	}

	.sdk-tab {
		padding: 0.5rem 1.25rem;
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--text-tertiary);
		font-family: var(--font-display);
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.sdk-tab.active {
		background: var(--bg-elevated);
		color: var(--text-primary);
	}

	.code-block {
		width: 100%;
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: 1rem 1.25rem;
		text-align: left;
		overflow-x: auto;
	}

	.code-block code {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		color: var(--text-primary);
		line-height: 1.6;
		white-space: pre;
	}

	.code-block-lg code {
		font-size: 0.8rem;
	}

	.step-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: rgba(249, 115, 22, 0.08);
		border: 1px solid rgba(249, 115, 22, 0.2);
		border-radius: var(--radius-md);
		color: var(--text-secondary);
		font-size: 0.85rem;
		text-align: left;
		width: 100%;
	}

	.step-info code {
		font-family: var(--font-mono);
		color: var(--accent);
		font-size: 0.8rem;
	}

	.step-info svg {
		color: var(--accent);
		flex-shrink: 0;
	}

	.error-msg {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #ef4444;
		padding: 0.75rem 1rem;
		border-radius: var(--radius-md);
		width: 100%;
		font-size: 0.9rem;
	}

	.final-actions {
		display: flex;
		gap: 0.75rem;
		margin-top: 0.5rem;
	}

	.btn-lg {
		padding: 0.875rem 2rem;
		font-size: 1rem;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 3rem 0;
		gap: 1rem;
		color: var(--text-secondary);
	}

	.spinner {
		width: 36px;
		height: 36px;
		border: 3px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@media (max-width: 480px) {
		.onboarding-card {
			padding: 1.5rem;
		}

		.progress-labels span:nth-child(2),
		.progress-labels span:nth-child(3) {
			display: none;
		}
	}
</style>
