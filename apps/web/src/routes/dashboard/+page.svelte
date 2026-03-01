<script lang="ts">
	import { onMount } from 'svelte';
	import '../../app.css';

	let { data } = $props();
	
	let sessions = $state<Array<{
		session_id: string;
		step_count: number;
		loops_detected: number;
		created_at: string;
	}>>([]);
	let stats = $state({
		total_checks: 0,
		loops_detected: 0
	});
	let loading = $state(true);
	let userEmail = $state('');
	let userPlan = $state('hobby');
	let userDailyLimit = $state(1000);
	let checksToday = $state(0);
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
		loadData();
		
		// Poll for usage updates every 3 seconds
		const interval = setInterval(async () => {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) return;
			
			const { data: userData } = await supabase
				.from('users')
				.select('checks_today, daily_limit')
				.eq('id', authUser.id)
				.single();
			
			if (userData) {
				checksToday = userData.checks_today || 0;
				userDailyLimit = userData.daily_limit || 1000;
			}
		}, 3000);
		
		return () => clearInterval(interval);
	});
	
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
				.select('api_key, plan, daily_limit, checks_today')
				.eq('id', authUser.id)
				.single();
			
			if (userData) {
				apiKey = userData.api_key || '';
				userPlan = userData.plan || 'hobby';
				userDailyLimit = userData.daily_limit || 1000;
				checksToday = userData.checks_today || 0;
				
				// Store API key for SDK use
				if (userData.api_key) {
					localStorage.setItem('inferencebrake_api_key', userData.api_key);
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
				.select('loop_detected')
				.eq('user_id', authUser.id);
			
			if (metricsData) {
				const loopsDetected = (metricsData as Array<{ loop_detected: boolean }>).filter(m => m.loop_detected).length;
				stats = {
					total_checks: metricsData.length,
					loops_detected: loopsDetected
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
		try {
			const { supabase } = await import('$lib/supabase');
			
			// Get stored API key
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) {
				alert('No API key found. Please refresh the page.');
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
				alert('Demo mode - plan updated!');
				userPlan = plan;
				userDailyLimit = plan === 'pro' ? 10000 : 1000;
			} else if (response.error) {
				alert('Error: ' + response.error);
			}
		} catch (e) {
			console.error('Failed to upgrade:', e);
			alert('Failed to upgrade: ' + e);
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
		return plan.charAt(0).toUpperCase() + plan.slice(1);
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

<div class="dashboard">
	<div class="container">
		<header class="dashboard-header">
			<h1>Dashboard</h1>
			<p class="subtitle">Monitor your AI agent sessions and loop detections</p>
		</header>

		<!-- User Info & Plan Section -->
		<section class="user-section">
			<div class="user-info">
				<div class="user-email">{userEmail}</div>
				<div class="plan-badge" class:pro={userPlan === 'pro'}>
					{getPlanDisplayName(userPlan)} Plan
				</div>
			</div>
			
			<!-- Usage Meter -->
			<div class="usage-meter">
				<div class="usage-header">
					<span>Today's Usage</span>
					<span>{checksToday} / {userDailyLimit}</span>
				</div>
				<div class="usage-bar">
					<div class="usage-fill" style="width: {Math.min(100, (checksToday / userDailyLimit) * 100)}%"></div>
				</div>
			</div>
			
			{#if userPlan !== 'pro'}
				{#if checksToday >= userDailyLimit}
					<div class="limit-alert">
						<span class="alert-icon">!</span>
						<div class="limit-alert-content">
							<span>You've reached your daily limit of {userDailyLimit} checks.</span>
							<span>Upgrade to Pro for unlimited access.</span>
						</div>
						<button class="btn btn-primary upgrade-btn" onclick={() => upgradePlan('pro')}>
							Upgrade to Pro ($9/mo)
						</button>
					</div>
				{:else if checksToday >= userDailyLimit * 0.8}
					<div class="upgrade-prompt">
						<span>Running low on checks? Upgrade to Pro for 10,000 checks/day.</span>
						<button class="btn btn-secondary upgrade-btn" onclick={() => upgradePlan('pro')}>
							Upgrade to Pro
						</button>
					</div>
				{/if}
			{/if}
		</section>
		
		<!-- API Key Section -->
		<section class="api-key-section">
			<h3>API Key</h3>
			<div class="api-key-row">
				<code class="api-key-display">
					{showApiKey ? apiKey : apiKey.slice(0, 8) + '...' + apiKey.slice(-4)}
				</code>
				<button class="btn btn-secondary" onclick={() => showApiKey = !showApiKey}>
					{showApiKey ? 'Hide' : 'Show'}
				</button>
				<button class="btn btn-secondary" onclick={copyApiKey}>
					Copy
				</button>
				<button class="btn btn-secondary danger" onclick={regenerateApiKey}>
					Regenerate
				</button>
			</div>
			<p class="api-key-hint">Keep this key secret. It grants access to your account.</p>
		</section>

		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Loading your data...</p>
			</div>
		{:else}
			<div class="stats-grid stagger-children">
				<div class="stat-card">
					<div class="stat-icon total">
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Total Checks</span>
						<span class="stat-value">{stats.total_checks.toLocaleString()}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon loops">
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 8-8 8 8 0 0 1 8 8"/><path d="M12 4v16"/><path d="M20 12a8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8"/></svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Loops Detected</span>
						<span class="stat-value">{stats.loops_detected.toLocaleString()}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon saved">
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Loops Stopped</span>
						<span class="stat-value">{stats.loops_detected.toLocaleString()}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon">
						<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Total Checks</span>
						<span class="stat-value">{stats.total_checks.toLocaleString()}</span>
					</div>
				</div>
			</div>

			<section class="sessions-section">
				<div class="sessions-header">
					<h2>Recent Sessions</h2>
					{#if sessions.length > 0}
						<button class="btn btn-secondary" onclick={exportToCSV}>
							Export CSV
						</button>
					{/if}
				</div>

				<div class="date-filters">
					<label>
						From:
						<input type="date" bind:value={dateFrom} onchange={applyDateFilter} />
					</label>
					<label>
						To:
						<input type="date" bind:value={dateTo} onchange={applyDateFilter} />
					</label>
					{#if dateFrom || dateTo}
						<button class="btn btn-secondary btn-sm" onclick={clearDateFilter}>
							Clear
						</button>
					{/if}
				</div>
				
				{#if sessions.length === 0}
					<div class="empty-state">
						<div class="empty-icon">
							<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
						</div>
						<h3>No sessions yet</h3>
						<p>Start sending reasoning traces to see your agent activity here.</p>
						<a href="/docs" class="btn btn-primary">View Integration Docs</a>
					</div>
				{:else}
					<div class="sessions-table">
						<div class="table-header">
							<span>Session ID</span>
							<span>Steps</span>
							<span>Loops</span>
							<span>Last Activity</span>
						</div>
						
						{#each sessions as session}
							<div class="table-row" onclick={() => openSessionDetail(session.session_id)} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && openSessionDetail(session.session_id)}>
								<span class="session-id mono">{truncateId(session.session_id)}</span>
								<span class="step-count">{session.step_count}</span>
								<span class="loop-badge" class:detected={session.loops_detected > 0}>
									{session.loops_detected > 0 ? `${session.loops_detected} detected` : 'None'}
								</span>
								<span class="timestamp">{formatDate(session.created_at)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</section>
		{/if}

		<!-- Session Detail Modal -->
		{#if selectedSession}
			<div class="modal-overlay" onclick={closeSessionDetail} role="button" tabindex="0" onkeydown={(e) => e.key === 'Escape' && closeSessionDetail()}>
				<div class="modal-content" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
					<div class="modal-header">
						<h2>Session Details</h2>
						<div class="modal-actions">
							<button class="btn btn-danger btn-sm" onclick={deleteSession}>Delete</button>
							<button class="modal-close" onclick={closeSessionDetail}>&times;</button>
						</div>
					</div>
					<div class="modal-body">
						<div class="session-meta">
							<span class="mono">{selectedSession}</span>
						</div>
						
						{#if sessionSteps.length === 0}
							<div class="loading-steps">
								<div class="spinner"></div>
								<p>Loading steps...</p>
							</div>
						{:else}
							<div class="steps-timeline">
								{#each sessionSteps as step}
									<div class="step-item" class:loop-detected={step.loop_detected}>
										<div class="step-header">
											<span class="step-number">Step {step.step_number}</span>
											{#if step.loop_detected}
												<span class="loop-flag">Loop Detected</span>
											{/if}
											{#if step.similarity !== null}
												<span class="similarity">{(step.similarity * 100).toFixed(1)}%</span>
											{/if}
										</div>
										{#if step.metadata}
											<div class="detector-badges">
												<span class="detector" class:fired={step.metadata.semantic_vote} title="Semantic detector">
													Semantic {step.metadata.semantic_vote ? 'ON' : 'off'}
												</span>
												<span class="detector" class:fired={step.metadata.action_vote} title="Action repeat detector">
													Action {step.metadata.action_vote ? 'ON' : 'off'}
												</span>
												<span class="detector" class:fired={step.metadata.ngram_vote} title="N-gram detector">
													N-gram {step.metadata.ngram_vote ? 'ON' : 'off'}
												</span>
												{#if step.metadata.confidence > 0}
													<span class="confidence" title="Confidence score">
														Confidence: {(step.metadata.confidence * 100).toFixed(0)}%
													</span>
												{/if}
											</div>
										{/if}
										<div class="step-reasoning">{step.reasoning}</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard {
		min-height: 100vh;
		padding: var(--space-2xl) 0;
		background: var(--gradient-dark);
	}

	.dashboard-header {
		margin-bottom: var(--space-2xl);
	}

	.dashboard-header h1 {
		font-size: 2.5rem;
		margin-bottom: var(--space-sm);
	}

	.subtitle {
		font-size: 1.1rem;
		color: var(--text-secondary);
	}

	.user-section {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: var(--space-xl);
		margin-bottom: var(--space-xl);
	}

	.user-info {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-lg);
	}

	.user-email {
		font-size: 1rem;
		color: var(--text-primary);
	}

	.plan-badge {
		background: var(--bg-tertiary);
		color: var(--text-secondary);
		padding: var(--space-xs) var(--space-sm);
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		font-weight: 500;
	}

	.plan-badge.pro {
		background: rgba(249, 115, 22, 0.15);
		color: var(--accent);
	}

	.usage-meter {
		margin-bottom: var(--space-lg);
	}

	.usage-header {
		display: flex;
		justify-content: space-between;
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: var(--space-sm);
	}

	.usage-bar {
		height: 8px;
		background: var(--bg-tertiary);
		border-radius: var(--radius-full);
		overflow: hidden;
	}

	.usage-fill {
		height: 100%;
		background: var(--gradient-accent);
		border-radius: var(--radius-full);
		transition: width 0.3s ease;
	}

	.upgrade-btn {
		width: 100%;
	}

	.api-key-section {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: var(--space-xl);
		margin-bottom: var(--space-xl);
	}

	.api-key-section h3 {
		font-size: 1rem;
		margin-bottom: var(--space-md);
	}

	.api-key-row {
		display: flex;
		gap: var(--space-sm);
		align-items: center;
		flex-wrap: wrap;
	}

	.api-key-display {
		flex: 1;
		min-width: 200px;
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		font-family: var(--font-mono);
		font-size: 0.85rem;
		word-break: break-all;
	}

	.api-key-hint {
		font-size: 0.8rem;
		color: var(--text-tertiary);
		margin-top: var(--space-sm);
	}

	.limit-alert {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		background: rgba(239, 68, 68, 0.15);
		border: 1px solid rgba(239, 68, 68, 0.4);
		border-radius: var(--radius-md);
		padding: var(--space-md) var(--space-lg);
		color: #ef4444;
		font-size: 0.9rem;
	}

	.limit-alert-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.alert-icon {
		font-size: 1.2rem;
	}

	.limit-alert .upgrade-btn {
		background: var(--gradient-accent);
		box-shadow: 0 0 20px rgba(249, 115, 22, 0.4);
		white-space: nowrap;
		width: auto;
		flex-shrink: 0;
	}

	.upgrade-prompt {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-md);
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-md) var(--space-lg);
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.upgrade-prompt > span {
		flex: 1;
	}

	.upgrade-prompt .upgrade-btn {
		font-size: 0.8rem;
		padding: 0.5rem 1rem;
		width: auto;
		flex-shrink: 0;
	}

	.btn.danger {
		border-color: var(--danger);
		color: var(--danger);
	}

	.btn.danger:hover {
		background: rgba(239, 68, 68, 0.1);
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 300px;
		gap: var(--space-lg);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-xl);
		margin-bottom: var(--space-3xl);
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}
	}

	.stat-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: var(--space-xl);
		display: flex;
		align-items: center;
		gap: var(--space-lg);
		transition: all 0.3s ease;
	}

	.stat-card:hover {
		border-color: var(--accent);
		transform: translateY(-2px);
	}

	.stat-icon {
		width: 56px;
		height: 56px;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.stat-icon.total {
		background: rgba(99, 102, 241, 0.15);
		color: #818cf8;
	}

	.stat-icon.loops {
		background: rgba(249, 115, 22, 0.15);
		color: var(--accent);
	}

	.stat-icon.saved {
		background: rgba(34, 197, 94, 0.15);
		color: var(--success);
	}

	.stat-content {
		display: flex;
		flex-direction: column;
	}

	.stat-label {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: var(--space-xs);
	}

	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		font-family: var(--font-mono);
	}

	.sessions-section h2 {
		font-size: 1.5rem;
		margin-bottom: var(--space-xl);
	}

	.sessions-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--space-xl);
	}

	.sessions-header h2 {
		margin-bottom: 0;
	}

	.date-filters {
		display: flex;
		gap: var(--space-md);
		align-items: center;
		margin-bottom: var(--space-xl);
		flex-wrap: wrap;
	}

	.date-filters label {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.date-filters input[type="date"] {
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		color: var(--text-primary);
		font-size: 0.85rem;
	}

	.date-filters input[type="date"]:focus {
		outline: none;
		border-color: var(--accent);
	}

	.btn-sm {
		padding: var(--space-xs) var(--space-md);
		font-size: 0.8rem;
	}

	.empty-state {
		background: var(--bg-secondary);
		border: 1px dashed var(--border);
		border-radius: var(--radius-lg);
		padding: var(--space-3xl);
		text-align: center;
	}

	.empty-icon {
		margin-bottom: var(--space-lg);
		color: var(--text-tertiary);
	}

	.empty-state h3 {
		font-size: 1.25rem;
		margin-bottom: var(--space-sm);
	}

	.empty-state p {
		margin-bottom: var(--space-xl);
	}

	.sessions-table {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.table-header {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr;
		padding: var(--space-lg);
		background: var(--bg-tertiary);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.table-row {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr;
		padding: var(--space-lg);
		border-top: 1px solid var(--border);
		align-items: center;
		transition: background 0.2s;
	}

	.table-row:hover {
		background: var(--bg-tertiary);
	}

	.session-id {
		color: var(--text-primary);
		font-size: 0.9rem;
	}

	.step-count {
		font-family: var(--font-mono);
		color: var(--text-secondary);
	}

	.loop-badge {
		display: inline-flex;
		padding: var(--space-xs) var(--space-sm);
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		font-weight: 500;
		background: var(--bg-tertiary);
		color: var(--text-tertiary);
		width: fit-content;
	}

	.loop-badge.detected {
		background: rgba(239, 68, 68, 0.15);
		color: var(--danger);
	}

	.timestamp {
		color: var(--text-tertiary);
		font-size: 0.85rem;
	}

	@media (max-width: 640px) {
		.table-header,
		.table-row {
			grid-template-columns: 1fr 1fr;
			gap: var(--space-sm);
		}

		.table-header span:nth-child(3),
		.table-header span:nth-child(4),
		.table-row span:nth-child(3),
		.table-row span:nth-child(4) {
			display: none;
		}
	}

	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--space-lg);
	}

	.modal-content {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		width: 100%;
		max-width: 700px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-lg) var(--space-xl);
		border-bottom: 1px solid var(--border);
	}

	.modal-header h2 {
		font-size: 1.25rem;
		margin: 0;
	}

	.modal-close {
		background: none;
		border: none;
		font-size: 1.5rem;
		color: var(--text-secondary);
		cursor: pointer;
		padding: 0;
		line-height: 1;
	}

	.modal-close:hover {
		color: var(--text-primary);
	}

	.modal-actions {
		display: flex;
		align-items: center;
		gap: var(--space-md);
	}

	.btn-danger {
		background: transparent;
		border: 1px solid var(--danger);
		color: var(--danger);
	}

	.btn-danger:hover {
		background: rgba(239, 68, 68, 0.1);
	}

	.modal-close:hover {
		color: var(--text-primary);
	}

	.modal-body {
		padding: var(--space-xl);
		overflow-y: auto;
		flex: 1;
	}

	.session-meta {
		margin-bottom: var(--space-lg);
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-tertiary);
		border-radius: var(--radius-md);
		font-size: 0.85rem;
		word-break: break-all;
	}

	.loading-steps {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--space-2xl);
		gap: var(--space-md);
		color: var(--text-secondary);
	}

	.steps-timeline {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.step-item {
		padding: var(--space-md);
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
	}

	.step-item.loop-detected {
		border-color: rgba(239, 68, 68, 0.5);
		background: rgba(239, 68, 68, 0.05);
	}

	.step-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-sm);
		font-size: 0.85rem;
		flex-wrap: wrap;
	}

	.step-number {
		font-weight: 600;
		color: var(--text-primary);
	}

	.loop-flag {
		background: rgba(239, 68, 68, 0.2);
		color: var(--danger);
		padding: 2px var(--space-sm);
		border-radius: var(--radius-full);
		font-size: 0.75rem;
		font-weight: 500;
	}

	.similarity {
		color: var(--text-tertiary);
		margin-left: auto;
	}

	.step-reasoning {
		font-size: 0.9rem;
		color: var(--text-secondary);
		white-space: pre-wrap;
		word-break: break-word;
		max-height: 150px;
		overflow-y: auto;
	}

	.table-row {
		cursor: pointer;
	}

	.detector-badges {
		display: flex;
		gap: var(--space-sm);
		margin-bottom: var(--space-sm);
		flex-wrap: wrap;
	}

	.detector {
		font-size: 0.7rem;
		padding: 2px 6px;
		border-radius: var(--radius-sm);
		background: var(--bg-tertiary);
		color: var(--text-tertiary);
		font-weight: 500;
	}

	.detector.fired {
		background: rgba(249, 115, 22, 0.2);
		color: var(--accent);
	}

	.confidence {
		font-size: 0.7rem;
		color: var(--text-tertiary);
		margin-left: auto;
	}
</style>
