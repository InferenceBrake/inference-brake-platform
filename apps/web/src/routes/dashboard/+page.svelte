<script lang="ts">
	import { onMount } from 'svelte';
	import '../../app.css';
	import StatCard from '$lib/components/StatCard.svelte';

	let { data } = $props();

	let sessions = $state<Array<{
		session_id: string;
		step_count: number;
		loops_detected: number;
		created_at: string;
	}>>([]);
	let stats = $state({
		total_checks: 0,
		loops_detected: 0,
		dollars_saved: 0
	});
	let analytics = $state<{
		total_checks: number;
		loops_blocked: number;
		estimated_usd_saved: number;
		by_model: Array<{ model: string; checks: number; loops: number; saved: number }>;
		by_action: Array<{ action: string; checks: number; loops: number; saved: number }>;
		by_prompt: Array<{ prompt: string; checks: number; loops: number; saved: number }>;
		by_detector: Array<{ detector: string; loops: number }>;
		recent_loops: Array<{
			session_id: string;
			model: string | null;
			action: string | null;
			prompt: string | null;
			confidence: number;
			saved: number;
			detectors: Record<string, boolean> | null;
			created_at: string;
		}>;
	} | null>(null);
	let loading = $state(true);
	let userEmail = $state('');
	let userPlan = $state('hobby');
	let userMonthlyLimit = $state(5000);
	let checksThisMonth = $state(0);
	let checksToday = $state(0);
	let subscriptionStatus = $state('inactive');
	let upgradeProcessing = $state<string | null>(null);
	let billingMessage = $state('');
	let apiKey = $state('');
	let showApiKey = $state(false);
	let selectedSession = $state<string | null>(null);
	let sessionSteps = $state<Array<{
		step_number: number;
		reasoning: string;
		similarity: number | null;
		loop_detected: boolean;
		created_at: string;
		metadata: {
			action_repeat_count: number;
			ngram_overlap: number;
			semantic_vote: boolean;
			action_vote: boolean;
			ngram_vote: boolean;
			confidence: number;
		} | null;
	}>>([]);
	let dateFrom = $state('');
	let dateTo = $state('');

	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const fromCheckout = params.get('success') === 'true';
		if (fromCheckout) {
			billingMessage = 'Subscription activated. Syncing your plan...';
		} else if (params.get('canceled') === 'true') {
			billingMessage = 'Checkout canceled. No changes were made.';
		}

		loadData();
		// Reconcile with Stripe in the background so a delayed or missing
		// webhook cannot leave the plan stale.
		syncSubscription(fromCheckout);
		loadAnalytics();

		// Poll for usage and plan updates every 3 seconds
		const interval = setInterval(async () => {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) return;

			const { data: userData } = await supabase
				.from('users')
				.select('checks_today, checks_this_month, monthly_limit, plan, subscription_status')
				.eq('id', authUser.id)
				.single();

			if (userData) {
				checksToday = userData.checks_today || 0;
				checksThisMonth = userData.checks_this_month || 0;
				userMonthlyLimit = userData.monthly_limit || 5000;
				if (userData.plan && userData.plan !== userPlan) {
					userPlan = userData.plan;
					if (billingMessage.startsWith('Subscription activated')) {
						billingMessage = 'Subscription active.';
					}
				}
				if (userData.subscription_status) {
					subscriptionStatus = userData.subscription_status;
				}
			}
		}, 3000);

		return () => clearInterval(interval);
	});

	async function loadAnalytics() {
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) return;

			const response = await supabase.functions.invoke('analytics-summary', {
				body: { days: 30 },
				headers: { Authorization: `Bearer ${storedApiKey}` }
			});

			if (response.data && !response.error) {
				analytics = response.data;
			}
		} catch (e) {
			console.error('Failed to load analytics:', e);
		}
	}

	async function syncSubscription(notify = false) {		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) return;

			const response = await supabase.functions.invoke('stripe-sync', {
				headers: { Authorization: `Bearer ${storedApiKey}` }
			});

			if (notify) {
				if (response.data?.plan && response.data.plan !== 'hobby') {
					billingMessage = 'Subscription active.';
				} else if (response.data?.synced === false) {
					billingMessage = 'Subscription not found yet. This page will update automatically.';
				} else if (response.data?.error) {
					billingMessage = response.data.error;
				}
			}

			await loadData();
		} catch (e) {
			console.error('Subscription sync failed:', e);
		}
	}

	async function loadData() {
		try {
			const { supabase } = await import('$lib/supabase');

			// Get authenticated user
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) {
				window.location.href = '/login';
				return;
			}

			userEmail = authUser.email || '';

			// Get user's full data from our users table
			const { data: userData } = await supabase
				.from('users')
				.select('api_key, plan, monthly_limit, checks_this_month, checks_today, onboarding_completed, subscription_status')
				.eq('id', authUser.id)
				.single();

			if (userData) {
				apiKey = userData.api_key || '';
				userPlan = userData.plan || 'hobby';
				userMonthlyLimit = userData.monthly_limit || 5000;
				checksThisMonth = userData.checks_this_month || 0;
				checksToday = userData.checks_today || 0;
				subscriptionStatus = userData.subscription_status || 'inactive';

				// Store API key for SDK use
				if (userData.api_key) {
					localStorage.setItem('inferencebrake_api_key', userData.api_key);
				}

				// Redirect to onboarding if not completed
				if (!userData.onboarding_completed) {
					window.location.href = '/onboarding';
					return;
				}
			}

			// Fallback: fetch API key via edge function if direct query returned nothing
			if (!apiKey) {
				const { data: fnData } = await supabase.functions.invoke('get-api-key');
				if (fnData?.api_key) {
					apiKey = fnData.api_key;
					localStorage.setItem('inferencebrake_api_key', fnData.api_key);
				}
			}

			// Fetch user's reasoning history
			let query = supabase
				.from('reasoning_history')
				.select('session_id, created_at, loop_detected')
				.eq('user_id', authUser.id)
				.order('created_at', { ascending: false })
				.limit(50);

			if (dateFrom) {
				query = query.gte('created_at', dateFrom);
			}
			if (dateTo) {
				query = query.lte('created_at', dateTo + 'T23:59:59.999Z');
			}

			const { data: sessionsData } = await query;

			if (sessionsData) {
				const sessionMap = new Map<string, { step_count: number; loops_detected: number; created_at: string }>();

				for (const row of sessionsData) {
					const existing = sessionMap.get(row.session_id);
					if (existing) {
						existing.step_count++;
						if (row.loop_detected) existing.loops_detected++;
					} else {
						sessionMap.set(row.session_id, {
							step_count: 1,
							loops_detected: row.loop_detected ? 1 : 0,
							created_at: row.created_at
						});
					}
				}

				sessions = Array.from(sessionMap.entries()).map(([session_id, data]) => ({
					session_id,
					...data
				}));
			}

			const { data: metricsData } = await supabase
				.from('metrics')
				.select('loop_detected, estimated_cost_saved')
				.eq('user_id', authUser.id);

			if (metricsData) {
				const rows = metricsData as Array<{ loop_detected: boolean; estimated_cost_saved: number | null }>;
				const loopsDetected = rows.filter(m => m.loop_detected).length;
				const dollarsSaved = rows.reduce((sum, m) => sum + (m.estimated_cost_saved || 0), 0);
				stats = {
					total_checks: rows.length,
					loops_detected: loopsDetected,
					dollars_saved: dollarsSaved
				};
			}
		} catch (e) {
			console.error('Failed to load dashboard data:', e);
		} finally {
			loading = false;
		}
	}

	async function loadSessionSteps(sessionId: string) {
		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) return;

			const { data: steps } = await supabase
				.from('reasoning_history')
				.select('step_number, reasoning, similarity, loop_detected, created_at, metadata')
				.eq('session_id', sessionId)
				.eq('user_id', authUser.id)
				.order('step_number', { ascending: true });

			if (steps) {
				sessionSteps = steps;
			}
		} catch (e) {
			console.error('Failed to load session steps:', e);
		}
	}

	function openSessionDetail(sessionId: string) {
		selectedSession = sessionId;
		loadSessionSteps(sessionId);
	}

	function closeSessionDetail() {
		selectedSession = null;
		sessionSteps = [];
	}

	async function deleteSession() {
		if (!selectedSession) return;
		if (!confirm('Delete this session? This will remove all steps in this session.')) return;

		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) return;

			const { error } = await supabase
				.from('reasoning_history')
				.delete()
				.eq('session_id', selectedSession)
				.eq('user_id', authUser.id);

			if (!error) {
				closeSessionDetail();
				loadData();
			}
		} catch (e) {
			console.error('Failed to delete session:', e);
		}
	}

	async function copyApiKey() {
		await navigator.clipboard.writeText(apiKey);
	}

	async function regenerateApiKey() {
		if (!confirm('Are you sure? Your old API key will stop working.')) return;

		try {
			const { supabase } = await import('$lib/supabase');
			const newKey = 'ib_' + Math.random().toString(36).substring(2, 34) + Math.random().toString(36).substring(2, 34);

			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) return;

			const { error } = await supabase
				.from('users')
				.update({ api_key: newKey })
				.eq('id', authUser.id);

			if (!error) {
				apiKey = newKey;
				localStorage.setItem('inferencebrake_api_key', newKey);
			}
		} catch (e) {
			console.error('Failed to regenerate API key:', e);
		}
	}

	async function upgradePlan(plan: string) {
		upgradeProcessing = plan;
		billingMessage = '';
		try {
			const { supabase } = await import('$lib/supabase');

			// Get stored API key
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) {
				billingMessage = 'No API key found. Please refresh the page.';
				return;
			}

			const response = await supabase.functions.invoke('stripe-checkout', {
				body: { plan },
				headers: {
					Authorization: `Bearer ${storedApiKey}`
				}
			});

			if (response.data?.url) {
				window.location.href = response.data.url;
			} else if (response.data?.demo) {
				billingMessage = 'Demo mode - plan updated.';
				userPlan = plan;
				userMonthlyLimit = plan === 'pro' ? 500000 : plan === 'growth' ? 100000 : 5000;
			} else {
				billingMessage = response.data?.error || response.error?.message || 'Failed to start checkout.';
			}
		} catch (e) {
			billingMessage = 'Failed to start checkout: ' + e;
		} finally {
			upgradeProcessing = null;
		}
	}

	async function manageBilling() {
		upgradeProcessing = 'portal';
		billingMessage = '';
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) {
				billingMessage = 'No API key found. Please refresh the page.';
				return;
			}

			const response = await supabase.functions.invoke('stripe-portal', {
				headers: {
					Authorization: `Bearer ${storedApiKey}`
				}
			});

			if (response.data?.url) {
				window.location.href = response.data.url;
			} else {
				billingMessage = response.data?.error || response.error?.message || 'Failed to open billing portal.';
			}
		} catch (e) {
			billingMessage = 'Failed to open billing portal: ' + e;
		} finally {
			upgradeProcessing = null;
		}
	}

	function formatDate(dateStr: string) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function truncateId(id: string) {
		return id.length > 20 ? id.slice(0, 20) + '...' : id;
	}

	function getPlanDisplayName(plan: string) {
		if (plan === 'hobby') return 'Free';
		return plan.charAt(0).toUpperCase() + plan.slice(1);
	}

	function formatUSD(value: number) {
		return value.toLocaleString('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 2
		});
	}

	function applyDateFilter() {
		loadData();
	}

	function clearDateFilter() {
		dateFrom = '';
		dateTo = '';
		loadData();
	}

	function exportToCSV() {
		if (sessions.length === 0) return;

		const headers = ['Session ID', 'Steps', 'Loops Detected', 'Last Activity'];
		const rows = sessions.map(s => [
			s.session_id,
			s.step_count.toString(),
			s.loops_detected.toString(),
			s.created_at
		]);

		const csvContent = [
			headers.join(','),
			...rows.map(row => row.map(cell => `"${cell}"`).join(','))
		].join('\n');

		const blob = new Blob([csvContent], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `inferencebrake-sessions-${new Date().toISOString().split('T')[0]}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<svelte:head>
	<title>Dashboard - InferenceBrake</title>
</svelte:head>

<div class="dashboard-brutal bg-base-100 text-base-content">
	<!-- Header -->
	<section class="border-b-2 border-base-content">
		<div class="mx-auto w-full max-w-6xl px-4 pt-12 pb-10 md:px-8 md:pt-16">
			<p class="nb-muted mb-2 font-mono text-xs font-bold tracking-widest uppercase">Console</p>
			<h1 class="text-4xl font-extrabold tracking-tight md:text-5xl">Dashboard</h1>
			<p class="nb-muted mt-4 max-w-2xl font-medium">Monitor your AI agent sessions and loop detections</p>
		</div>
	</section>

	<div class="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-12 md:gap-8 md:px-8 md:py-16">
		<!-- Account -->
		<section class="nb-card nb-brutal bg-base-100">
			<div class="nb-card-body gap-5 p-6 md:p-8">
				<div class="flex flex-wrap items-center gap-3">
					<span class="font-bold">{userEmail}</span>
					<span class="nb-badge font-mono text-xs font-bold {userPlan === 'hobby' ? 'nb-badge-neutral' : 'nb-badge-primary'}">
						{getPlanDisplayName(userPlan)} Plan
					</span>
				</div>

				<div>
					<div class="nb-muted mb-2 flex items-center justify-between font-mono text-xs font-bold tracking-widest uppercase">
						<span>This month's usage</span>
						<span>{checksThisMonth.toLocaleString()} / {userMonthlyLimit.toLocaleString()}</span>
					</div>
					<progress class="nb-progress nb-progress-primary w-full" value={checksThisMonth} max={userMonthlyLimit}></progress>
				</div>

				<div class="border-2 border-base-content bg-base-200 p-4 md:p-5">
					<p class="font-extrabold">{getPlanDisplayName(userPlan)} plan</p>
					<p class="nb-muted text-sm font-medium">
						{userMonthlyLimit.toLocaleString()} checks/month
						{#if subscriptionStatus === 'past_due'} · Payment past due{/if}
					</p>
					{#if subscriptionStatus === 'past_due'}
						<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm mt-4">
							<span class="font-bold">Update your payment method to avoid interruption.</span>
						</div>
					{/if}
					<div class="mt-4 flex flex-col gap-3">
						{#if userPlan === 'hobby'}
							<button class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press w-full" onclick={() => upgradePlan('growth')} disabled={upgradeProcessing !== null}>
								{upgradeProcessing === 'growth' ? 'Redirecting...' : 'Upgrade to Growth - $49/mo'}
							</button>
							<button class="nb-btn nb-btn-primary nb-brutal-sm nb-brutal-press w-full" onclick={() => upgradePlan('pro')} disabled={upgradeProcessing !== null}>
								{upgradeProcessing === 'pro' ? 'Redirecting...' : 'Upgrade to Pro - $199/mo'}
							</button>
						{:else}
							<button class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press w-full" onclick={manageBilling} disabled={upgradeProcessing !== null}>
								{upgradeProcessing === 'portal' ? 'Opening...' : 'Manage billing'}
							</button>
						{/if}
					</div>
					{#if billingMessage}
						<p class="mt-3 text-sm font-bold" class:text-error={billingMessage.includes('Failed') || billingMessage.includes('past due')} class:text-success={!billingMessage.includes('Failed') && !billingMessage.includes('past due')}>
							{billingMessage}
						</p>
					{/if}
				</div>
			</div>
		</section>

		<!-- API key -->
		<section class="nb-card nb-brutal bg-base-100">
			<div class="nb-card-body gap-4 p-6 md:p-8">
				<h3 class="text-lg font-extrabold">API Key</h3>
				<div class="flex flex-wrap items-center gap-3">
					<code class="block min-w-52 flex-1 border-2 border-base-content bg-base-200 p-3 font-mono text-sm break-all">
						{showApiKey ? apiKey : apiKey.slice(0, 8) + '...' + apiKey.slice(-4)}
					</code>
					<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={() => showApiKey = !showApiKey}>
						{showApiKey ? 'Hide' : 'Show'}
					</button>
					<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={copyApiKey}>
						Copy
					</button>
					<button class="nb-btn nb-btn-error nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={regenerateApiKey}>
						Regenerate
					</button>
				</div>
				<p class="nb-muted text-sm font-medium">Keep this key secret. It grants access to your account.</p>
			</div>
		</section>

		{#if loading}
			<div class="flex flex-col items-center gap-4 py-16">
				<span class="nb-loading nb-loading-spinner nb-loading-lg"></span>
				<p class="nb-muted font-medium">Loading your data...</p>
			</div>
		{:else}
			<div class="grid gap-5 md:grid-cols-2 md:gap-8 lg:grid-cols-4 stagger-children">
				<StatCard label="Total checks" value={(analytics?.total_checks ?? stats.total_checks).toLocaleString()} desc="All time" tone="primary">
					{#snippet icon()}
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
					{/snippet}
				</StatCard>
				<StatCard label="Loops detected" value={(analytics?.loops_blocked ?? stats.loops_detected).toLocaleString()} desc="Blocked" tone="secondary">
					{#snippet icon()}
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 8-8 8 8 0 0 1 8 8"/><path d="M12 4v16"/><path d="M20 12a8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8"/></svg>
					{/snippet}
				</StatCard>
				<StatCard label="Est. $ saved" value={formatUSD(analytics?.estimated_usd_saved ?? stats.dollars_saved)} desc="Wasted tokens avoided" tone="success">
					{#snippet icon()}
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>
					{/snippet}
				</StatCard>
				<StatCard label="Checks today" value={checksToday.toLocaleString()} desc="Since midnight" tone="neutral">
					{#snippet icon()}
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
					{/snippet}
				</StatCard>
			</div>

			{#if analytics && analytics.loops_blocked > 0}
				<section>
					<div class="mb-6 flex flex-wrap items-baseline justify-between gap-2">
						<h2 class="text-2xl font-extrabold md:text-3xl">Loop Analytics</h2>
						<span class="nb-muted font-mono text-xs font-bold tracking-widest uppercase">Last 30 days</span>
					</div>

					<div class="grid gap-5 md:gap-8 lg:grid-cols-3">
						<div class="nb-card nb-brutal bg-base-100">
							<div class="nb-card-body gap-3 p-6">
								<h3 class="nb-muted text-xs font-bold tracking-widest uppercase">Loops by model</h3>
								<ul class="flex flex-col gap-2">
									{#each analytics.by_model as row}
										<li class="flex items-center justify-between gap-4 text-sm">
											<span class="truncate font-bold">{row.model}</span>
											<span class="nb-muted shrink-0 font-mono text-xs">{row.loops} / {row.checks}</span>
										</li>
									{:else}
										<li class="nb-muted text-sm">No data</li>
									{/each}
								</ul>
							</div>
						</div>

						<div class="nb-card nb-brutal bg-base-100">
							<div class="nb-card-body gap-3 p-6">
								<h3 class="nb-muted text-xs font-bold tracking-widest uppercase">Top looping tools</h3>
								<ul class="flex flex-col gap-2">
									{#each analytics.by_action as row}
										<li class="flex items-center justify-between gap-4 text-sm">
											<span class="truncate font-bold">{row.action}</span>
											<span class="nb-muted shrink-0 font-mono text-xs">{row.loops} / {row.checks}</span>
										</li>
									{:else}
										<li class="nb-muted text-sm">No data</li>
									{/each}
								</ul>
							</div>
						</div>

						<div class="nb-card nb-brutal bg-base-100">
							<div class="nb-card-body gap-3 p-6">
								<h3 class="nb-muted text-xs font-bold tracking-widest uppercase">Detectors that fired</h3>
								<ul class="flex flex-col gap-2">
									{#each analytics.by_detector as row}
										<li class="flex items-center justify-between gap-4 text-sm">
											<span class="truncate font-bold">{row.detector}</span>
											<span class="nb-muted shrink-0 font-mono text-xs">{row.loops}</span>
										</li>
									{:else}
										<li class="nb-muted text-sm">No data</li>
									{/each}
								</ul>
							</div>
						</div>
					</div>

					<div class="nb-card nb-brutal mt-5 bg-base-100 md:mt-8">
						<div class="nb-card-body gap-4 p-6 md:p-8">
							<h3 class="nb-muted text-xs font-bold tracking-widest uppercase">Recent loops</h3>
							<div class="overflow-x-auto">
								<table class="nb-table font-mono text-xs">
									<thead class="font-bold">
										<tr>
											<th>When</th>
											<th>Model</th>
											<th>Tool</th>
											<th>Detectors</th>
											<th>Conf</th>
											<th>Saved</th>
										</tr>
									</thead>
									<tbody class="nb-muted">
										{#each analytics.recent_loops as loop}
											<tr>
												<td>{formatDate(loop.created_at)}</td>
												<td>{loop.model || '-'}</td>
												<td>{loop.action || '-'}</td>
												<td>{Object.entries(loop.detectors || {}).filter(([, v]) => v).map(([k]) => k).join(', ') || '-'}</td>
												<td>{(loop.confidence * 100).toFixed(0)}%</td>
												<td>{formatUSD(loop.saved)}</td>
											</tr>
										{:else}
											<tr><td colspan="6">No loops yet</td></tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				</section>
			{/if}

			<section>
				<div class="mb-6 flex flex-wrap items-center justify-between gap-4">
					<h2 class="text-2xl font-extrabold md:text-3xl">Recent Sessions</h2>
					{#if sessions.length > 0}
						<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={exportToCSV}>
							Export CSV
						</button>
					{/if}
				</div>

				<div class="mb-6 flex flex-wrap items-end gap-4">
					<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
						From
						<input type="date" class="nb-input nb-input-bordered font-mono" bind:value={dateFrom} onchange={applyDateFilter} />
					</label>
					<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
						To
						<input type="date" class="nb-input nb-input-bordered font-mono" bind:value={dateTo} onchange={applyDateFilter} />
					</label>
					{#if dateFrom || dateTo}
						<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={clearDateFilter}>
							Clear
						</button>
					{/if}
				</div>

				<div class="nb-brutal overflow-x-auto bg-base-100">
					<table class="nb-table">
						<thead class="font-bold">
							<tr>
								<th>Session ID</th>
								<th>Steps</th>
								<th>Loops</th>
								<th>Last Activity</th>
							</tr>
						</thead>
						<tbody>
							{#each sessions as session}
								<tr onclick={() => openSessionDetail(session.session_id)} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && openSessionDetail(session.session_id)} class="cursor-pointer hover:bg-base-200">
									<td class="font-mono text-sm font-bold">{truncateId(session.session_id)}</td>
									<td class="font-mono text-sm">{session.step_count}</td>
									<td>
										{#if session.loops_detected > 0}
											<span class="nb-badge nb-badge-error font-mono text-xs font-bold">{session.loops_detected} detected</span>
										{:else}
											<span class="nb-badge nb-badge-neutral font-mono text-xs font-bold">None</span>
										{/if}
									</td>
									<td class="nb-muted text-sm">{formatDate(session.created_at)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}
	</div>

	<!-- Session detail modal -->
	{#if selectedSession}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onclick={closeSessionDetail} role="button" tabindex="0" onkeydown={(e) => e.key === 'Escape' && closeSessionDetail()}>
			<div class="nb-modal-box nb-brutal max-h-[80vh] w-full max-w-2xl overflow-y-auto bg-base-100 p-6 md:p-8" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
				<div class="mb-6 flex items-center justify-between gap-4">
					<h2 class="text-xl font-extrabold">Session Details</h2>
					<div class="flex items-center gap-3">
						<button class="nb-btn nb-btn-error nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={deleteSession}>Delete</button>
						<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={closeSessionDetail}>Close</button>
					</div>
				</div>
				<p class="mb-6 border-2 border-base-content bg-base-200 p-3 font-mono text-xs break-all">{selectedSession}</p>

				{#if sessionSteps.length === 0}
					<div class="flex flex-col items-center gap-4 py-12">
						<span class="nb-loading nb-loading-spinner nb-loading-lg"></span>
						<p class="nb-muted font-medium">Loading steps...</p>
					</div>
				{:else}
					<div class="flex flex-col gap-4">
						{#each sessionSteps as step}
							<div class="border-2 p-4 {step.loop_detected ? 'border-error bg-error/10' : 'border-base-content bg-base-100'}">
								<div class="mb-2 flex flex-wrap items-center gap-3 text-sm">
									<span class="font-extrabold">Step {step.step_number}</span>
									{#if step.loop_detected}
										<span class="nb-badge nb-badge-error font-mono text-xs font-bold">Loop Detected</span>
									{/if}
									{#if step.similarity !== null}
										<span class="nb-muted ml-auto font-mono text-xs">{(step.similarity * 100).toFixed(1)}%</span>
									{/if}
								</div>
								{#if step.metadata}
									<div class="mb-2 flex flex-wrap items-center gap-2">
										<span class="nb-badge font-mono text-xs font-bold {step.metadata.semantic_vote ? 'nb-badge-warning' : 'nb-badge-ghost'}" title="Semantic detector">
											Semantic {step.metadata.semantic_vote ? 'ON' : 'off'}
										</span>
										<span class="nb-badge font-mono text-xs font-bold {step.metadata.action_vote ? 'nb-badge-warning' : 'nb-badge-ghost'}" title="Action repeat detector">
											Action {step.metadata.action_vote ? 'ON' : 'off'}
										</span>
										<span class="nb-badge font-mono text-xs font-bold {step.metadata.ngram_vote ? 'nb-badge-warning' : 'nb-badge-ghost'}" title="N-gram detector">
											N-gram {step.metadata.ngram_vote ? 'ON' : 'off'}
										</span>
										{#if step.metadata.confidence > 0}
											<span class="nb-muted ml-auto text-xs font-medium" title="Confidence score">
												Confidence: {(step.metadata.confidence * 100).toFixed(0)}%
											</span>
										{/if}
									</div>
								{/if}
								<div class="max-h-36 overflow-y-auto text-sm whitespace-pre-wrap break-words">{step.reasoning}</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.dashboard-brutal h1,
	.dashboard-brutal h2,
	.dashboard-brutal h3 {
		color: var(--color-base-content);
	}
</style>
