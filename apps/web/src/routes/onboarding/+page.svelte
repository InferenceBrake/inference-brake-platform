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

	const stepLabels = ['Welcome', 'API Key', 'SDK', 'Integrate'];
	const stepTones = ['bg-primary text-primary-content', 'bg-secondary text-secondary-content', 'bg-accent text-accent-content', 'bg-success text-success-content'];

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

<div class="onboarding-brutal bg-base-100 text-base-content">
	<div class="mx-auto flex min-h-[85vh] w-full max-w-xl items-center justify-center px-4 py-12">
		<div class="nb-card nb-brutal w-full bg-base-100">
			<div class="nb-card-body gap-6 p-6 md:p-8">
				<ul class="nb-steps w-full">
					{#each stepLabels as label, i}
						<li class="nb-step text-xs font-bold" class:nb-step-primary={i + 1 <= step} data-content={i + 1 < step ? '✓' : i + 1}>
							{label}
						</li>
					{/each}
				</ul>

				{#if loading}
					<div class="flex flex-col items-center gap-4 py-12">
						<span class="nb-loading nb-loading-spinner nb-loading-lg"></span>
						<p class="nb-muted font-medium">Loading...</p>
					</div>
				{:else if step === 1}
					<div class="animate-fade-in flex flex-col items-center gap-4 text-center">
						<div class="nb-brutal-sm flex size-16 items-center justify-center {stepTones[0]}">
							<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
						</div>
						<h1 class="text-3xl font-extrabold">Welcome to InferenceBrake</h1>
						<p class="nb-muted font-medium">
							InferenceBrake detects when your AI agent gets stuck in reasoning loops and stops it before it burns through your budget. Set up in under 2 minutes.
						</p>
						<ul class="flex w-full flex-col gap-2 text-left">
							<li class="flex items-center gap-3 text-sm font-bold">
								<span class="nb-brutal-sm flex size-6 shrink-0 items-center justify-center bg-success text-success-content">
									<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
								</span>
								6 detectors working together
							</li>
							<li class="flex items-center gap-3 text-sm font-bold">
								<span class="nb-brutal-sm flex size-6 shrink-0 items-center justify-center bg-success text-success-content">
									<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
								</span>
								Works with any LLM provider
							</li>
							<li class="flex items-center gap-3 text-sm font-bold">
								<span class="nb-brutal-sm flex size-6 shrink-0 items-center justify-center bg-success text-success-content">
									<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
								</span>
								Free tier: 5,000 checks per month
							</li>
						</ul>
						<button class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" onclick={() => saveStep(2)}>
							Get Started
						</button>
					</div>

				{:else if step === 2}
					<div class="animate-fade-in flex flex-col items-center gap-4 text-center">
						<div class="nb-brutal-sm flex size-16 items-center justify-center {stepTones[1]}">
							<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
						</div>
						<h2 class="text-2xl font-extrabold">Your API Key</h2>
						<p class="nb-muted font-medium">This key authenticates your requests. Copy it now — you will need it in the next step.</p>

						<code class="block w-full border-2 border-base-content bg-base-200 p-4 font-mono text-sm break-all">{showApiKey ? apiKey : apiKey.slice(0, 8) + '...' + apiKey.slice(-4)}</code>

						<div class="flex w-full flex-wrap gap-3">
							<button class="nb-btn nb-btn-primary nb-brutal-sm nb-brutal-press flex-1" onclick={handleCopyKey}>
								{apiKeyCopied ? 'Copied!' : 'Copy Key'}
							</button>
							<button class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press flex-1" onclick={() => showApiKey = !showApiKey}>
								{showApiKey ? 'Hide' : 'Show'}
							</button>
						</div>

						<p class="nb-muted text-sm font-medium">This key is shown only once during onboarding. Store it securely.</p>

						<button class="nb-btn nb-btn-secondary nb-brutal nb-brutal-press w-full" onclick={() => saveStep(3)} disabled={!apiKeyCopied}>
							Next Step
						</button>
					</div>

				{:else if step === 3}
					<div class="animate-fade-in flex flex-col items-center gap-4 text-center">
						<div class="nb-brutal-sm flex size-16 items-center justify-center {stepTones[2]}">
							<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
						</div>
						<h2 class="text-2xl font-extrabold">Install the SDK</h2>
						<p class="nb-muted font-medium">Add InferenceBrake to your project with one command.</p>

						<div role="tablist" class="nb-tabs nb-tabs-box border-2 border-base-content">
							<button
								role="tab"
								class="nb-tab font-mono text-sm font-bold"
								class:nb-tab-active={sdkTab === 'python'}
								onclick={() => sdkTab = 'python'}
							>Python</button>
							<button
								role="tab"
								class="nb-tab font-mono text-sm font-bold"
								class:nb-tab-active={sdkTab === 'nodejs'}
								onclick={() => sdkTab = 'nodejs'}
							>Node.js</button>
						</div>

						<pre class="nb-brutal-sm w-full overflow-x-auto bg-neutral p-4 text-left font-mono text-sm text-neutral-content"><code>{sdkTab === 'python' ? 'pip install inferencebrake' : 'npm install inferencebrake'}</code></pre>

						<p class="nb-muted font-medium">Then import it in your code:</p>

						<pre class="nb-brutal-sm w-full overflow-x-auto bg-neutral p-4 text-left font-mono text-sm text-neutral-content"><code>{sdkTab === 'python'
	? 'from inferencebrake import InferenceBrake\n\nguard = InferenceBrake(api_key="YOUR_API_KEY")'
	: 'const { InferenceBrake } = require("inferencebrake");\n\nconst guard = new InferenceBrake({ apiKey: "YOUR_API_KEY" });'
}</code></pre>

						<button class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full" onclick={() => saveStep(4)}>
							Next Step
						</button>
					</div>

				{:else if step === 4}
					<div class="animate-fade-in flex flex-col items-center gap-4 text-center">
						<div class="nb-brutal-sm flex size-16 items-center justify-center {stepTones[3]}">
							<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
						</div>
						<h2 class="text-2xl font-extrabold">Add to Your Agent</h2>
						<p class="nb-muted font-medium">Wrap your agent loop with loop detection.</p>

						<pre class="nb-brutal-sm w-full overflow-x-auto bg-neutral p-4 text-left font-mono text-xs text-neutral-content md:text-sm"><code>from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="{apiKey.slice(0, 8)}...")

for step in agent.run():
    result = guard.check(
        reasoning=step["reasoning"],
        agent_id="my-agent"
    )
    if result.should_stop:
        print("Loop detected!")
        break</code></pre>

						<div role="note" class="nb-alert nb-alert-info nb-brutal-sm text-left">
							<span class="text-sm font-bold">Use your API key as the <code class="font-mono">api_key</code> parameter.</span>
						</div>

						{#if error}
							<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm text-sm font-bold">{error}</div>
						{/if}

						<div class="flex w-full flex-col gap-3">
							<button class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" onclick={completeOnboarding} disabled={completing}>
								{completing ? 'Completing...' : 'Go to Dashboard'}
							</button>
							<a href="/docs" class="nb-btn nb-btn-secondary nb-brutal nb-brutal-press w-full">Read Docs</a>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.onboarding-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.onboarding-brutal h1,
	.onboarding-brutal h2 {
		color: var(--color-base-content);
	}
</style>
