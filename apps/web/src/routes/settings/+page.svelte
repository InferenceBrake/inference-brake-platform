<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let userEmail = $state('');
	let userPlan = $state('hobby');
	let userDailyLimit = $state(1000);
	let subscriptionStatus = $state('active');
	let subscriptionPeriodEnd = $state<string | null>(null);
	let apiKey = $state('');
	let testApiKey = $state('');
	let showApiKey = $state(false);
	let showTestApiKey = $state(false);
	let loading = $state(true);
	let processing = $state(false);
	let message = $state('');
	let messageType = $state<'success' | 'error'>('success');

	onMount(() => {
		loadData();
	});

	async function loadData() {
		try {
			const { supabase } = await import('$lib/supabase');
			
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) {
				window.location.href = '/login';
				return;
			}
			
			userEmail = authUser.email || '';
			
			const { data: userData } = await supabase
				.from('users')
				.select('api_key, test_mode_api_key, plan, daily_limit, subscription_status, subscription_current_period_end')
				.eq('id', authUser.id)
				.single();
			
			if (userData) {
				apiKey = userData.api_key || '';
				testApiKey = userData.test_mode_api_key || '';
				userPlan = userData.plan || 'hobby';
				userDailyLimit = userData.daily_limit || 1000;
				subscriptionStatus = userData.subscription_status || 'active';
				subscriptionPeriodEnd = userData.subscription_current_period_end;
			}
		} catch (e) {
			console.error('Failed to load settings:', e);
		} finally {
			loading = false;
		}
	}

	async function deleteAccount() {
		if (!confirm('Are you sure you want to delete your account? This will permanently remove all your data including session history and usage metrics.')) return;
		if (!confirm('This action is IRREVERSIBLE. All your data will be lost forever. Continue?')) return;
		if (!confirm('Final warning: Type DELETE to confirm')) return;
		
		const input = prompt('Type DELETE to confirm account deletion');
		if (input !== 'DELETE') return;
		
		processing = true;
		message = '';
		
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			
			if (!storedApiKey) {
				throw new Error('No API key found');
			}
			
			const response = await supabase.functions.invoke('account-delete', {
				headers: {
					Authorization: `Bearer ${storedApiKey}`
				}
			});
			
			if (response.error) {
				throw new Error(response.error);
			}
			
			await supabase.auth.signOut();
			localStorage.removeItem('inferencebrake_api_key');
			window.location.href = '/';
		} catch (e: any) {
			showMessage(e.message || 'Failed to delete account', 'error');
		} finally {
			processing = false;
		}
	}

	async function generateTestKey() {
		if (!confirm('Generate a test mode API key? Test mode requests will not count against your daily limit.')) return;
		
		processing = true;
		message = '';
		
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			
			if (!storedApiKey) {
				throw new Error('No API key found');
			}
			
			const response = await supabase.functions.invoke('generate-test-key', {
				headers: {
					Authorization: `Bearer ${storedApiKey}`
				}
			});
			
			if (response.error) {
				throw new Error(response.error);
			}
			
			testApiKey = response.data.test_api_key;
			showMessage('Test mode key generated successfully!', 'success');
		} catch (e: any) {
			showMessage(e.message || 'Failed to generate test key', 'error');
		} finally {
			processing = false;
		}
	}

	async function resetPassword() {
		processing = true;
		message = '';

		try {
			const { supabase } = await import('$lib/supabase');
			const { error: resetError } = await supabase.auth.resetPasswordForEmail(userEmail, {
				redirectTo: `${window.location.origin}/reset-password`,
			});

			if (resetError) {
				throw new Error(resetError.message);
			}

			showMessage('Password reset email sent. Check your inbox.', 'success');
		} catch (e: any) {
			showMessage(e.message || 'Failed to send reset email', 'error');
		} finally {
			processing = false;
		}
	}

	async function copyApiKey() {
		await navigator.clipboard.writeText(apiKey);
		showMessage('API key copied to clipboard', 'success');
	}

	async function copyTestApiKey() {
		await navigator.clipboard.writeText(testApiKey);
		showMessage('Test API key copied to clipboard', 'success');
	}

	function showMessage(msg: string, type: 'success' | 'error') {
		message = msg;
		messageType = type;
		setTimeout(() => { message = ''; }, 5000);
	}

	function formatDate(dateStr: string | null) {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Settings - InferenceBrake</title>
</svelte:head>

<div class="settings-page">
	<div class="container">
		<header class="page-header">
			<h1>Settings</h1>
			<p class="subtitle">Manage your account, subscription, and preferences</p>
		</header>

		{#if message}
			<div class="message" class:error={messageType === 'error'} class:success={messageType === 'success'}>
				{message}
			</div>
		{/if}

		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Loading settings...</p>
			</div>
		{:else}
			<div class="settings-grid">
				<section class="settings-card">
					<h2>Profile</h2>
					<p class="card-description">Your account information</p>
					
					<div class="field">
						<label>Email</label>
						<div class="value">{userEmail}</div>
					</div>
					
					<div class="field">
						<label>Account Status</label>
						<div class="value">
							<span class="badge" class:active={subscriptionStatus === 'active'}>
								{subscriptionStatus}
							</span>
						</div>
					</div>
				</section>

				<section class="settings-card">
					<h2>API Key</h2>
					<p class="card-description">Your API key for integrating InferenceBrake</p>
					
					<div class="api-key-display">
						<code>{showApiKey ? apiKey : apiKey.slice(0, 12) + '...' + apiKey.slice(-4)}</code>
						<button class="btn btn-secondary btn-sm" onclick={() => showApiKey = !showApiKey}>
							{showApiKey ? 'Hide' : 'Show'}
						</button>
						<button class="btn btn-secondary btn-sm" onclick={copyApiKey}>
							Copy
						</button>
					</div>
					<p class="hint">Keep this key secret. It provides full access to your account.</p>
				</section>

				<!-- Hidden during beta - re-enable when paid plans launch
			<section class="settings-card">
					<h2>Test Mode API Key</h2>
					<p class="card-description">Use this key for testing - requests won't count against your daily limit</p>
					
					{#if testApiKey}
						<div class="api-key-display">
							<code>{showTestApiKey ? testApiKey : testApiKey.slice(0, 12) + '...' + testApiKey.slice(-4)}</code>
							<button class="btn btn-secondary btn-sm" onclick={() => showTestApiKey = !showTestApiKey}>
								{showTestApiKey ? 'Hide' : 'Show'}
							</button>
							<button class="btn btn-secondary btn-sm" onclick={copyTestApiKey}>
								Copy
							</button>
						</div>
						<p class="hint test-mode-badge">Test mode active - requests are unlimited</p>
					{:else}
						<p class="hint">No test mode key generated yet.</p>
						<button 
							class="btn btn-secondary" 
							onclick={generateTestKey}
							disabled={processing}
						>
							{processing ? 'Generating...' : 'Generate Test Key'}
						</button>
					{/if}
				</section>
			-->

				<section class="settings-card">
					<h2>Plan</h2>
					<p class="card-description">Your current plan during beta</p>
					
					<div class="current-plan">
						<div class="plan-info">
							<span class="plan-name">
								Free Beta
							</span>
							<span class="beta-badge">Open Beta</span>
						</div>
						<div class="plan-details">
							<span>{userDailyLimit.toLocaleString()} checks/day</span>
							<span class="period-end">All features included</span>
						</div>
					</div>

					<div class="beta-notice">
						<p>Pro plan coming later. Get notified when it launches.</p>
					</div>
				</section>

				<section class="settings-card">
					<h2>Security</h2>
					<p class="card-description">Manage your account security</p>

					<div class="reset-password">
						<div class="reset-info">
							<strong>Reset Password</strong>
							<p>Send a password reset link to {userEmail}</p>
						</div>
						<button
							class="btn btn-secondary"
							onclick={resetPassword}
							disabled={processing}
						>
							{processing ? 'Sending...' : 'Send Reset Email'}
						</button>
					</div>
				</section>

				<section class="settings-card danger-zone">
					<h2>Danger Zone</h2>
					<p class="card-description">Irreversible account actions</p>
					
					<div class="delete-account">
						<div class="delete-info">
							<strong>Delete Account</strong>
							<p>Permanently delete your account and all associated data. This action cannot be undone.</p>
						</div>
						<button 
							class="btn btn-danger" 
							onclick={deleteAccount}
							disabled={processing}
						>
							Delete My Account
						</button>
					</div>
				</section>
			</div>
		{/if}
	</div>
</div>

<style>
	.settings-page {
		min-height: 100vh;
		padding: var(--space-2xl) 0;
		background: var(--gradient-dark);
	}

	.page-header {
		margin-bottom: var(--space-2xl);
	}

	.page-header h1 {
		font-size: 2rem;
		margin-bottom: var(--space-sm);
	}

	.subtitle {
		color: var(--text-secondary);
	}

	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 0 var(--space-lg);
	}

	.message {
		padding: var(--space-md) var(--space-lg);
		border-radius: var(--radius-md);
		margin-bottom: var(--space-xl);
		font-size: 0.9rem;
	}

	.message.success {
		background: rgba(34, 197, 94, 0.15);
		border: 1px solid rgba(34, 197, 94, 0.3);
		color: var(--success);
	}

	.message.error {
		background: rgba(239, 68, 68, 0.15);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: var(--danger);
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

	.settings-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-xl);
	}

	.settings-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: var(--space-xl);
	}

	.settings-card h2 {
		font-size: 1.25rem;
		margin-bottom: var(--space-xs);
	}

	.card-description {
		color: var(--text-secondary);
		font-size: 0.9rem;
		margin-bottom: var(--space-xl);
	}

	.field {
		margin-bottom: var(--space-lg);
	}

	.field label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: var(--space-xs);
	}

	.value {
		color: var(--text-primary);
		font-size: 1rem;
	}

	.badge {
		display: inline-block;
		padding: var(--space-xs) var(--space-sm);
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		font-weight: 500;
		background: var(--bg-tertiary);
		color: var(--text-secondary);
	}

	.badge.active {
		background: rgba(34, 197, 94, 0.15);
		color: var(--success);
	}

	.api-key-display {
		display: flex;
		gap: var(--space-sm);
		align-items: center;
		margin-bottom: var(--space-sm);
	}

	.api-key-display code {
		flex: 1;
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		font-family: var(--font-mono);
		font-size: 0.85rem;
		word-break: break-all;
	}

	.hint {
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.test-mode-badge {
		color: var(--success);
		font-weight: 500;
	}

	.current-plan {
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-lg);
		margin-bottom: var(--space-lg);
	}

	.plan-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-sm);
	}

	.plan-name {
		font-size: 1.25rem;
		font-weight: 600;
	}

	.plan-name.pro {
		color: var(--accent);
	}

	.plan-price {
		font-size: 1.1rem;
		font-weight: 600;
	}

	.plan-details {
		display: flex;
		justify-content: space-between;
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.period-end {
		color: var(--text-tertiary);
	}

	.beta-badge {
		display: inline-block;
		background: var(--gradient-accent);
		color: white;
		padding: 0.2rem 0.6rem;
		font-size: 0.7rem;
		font-weight: 600;
		border-radius: var(--radius-full);
		text-transform: uppercase;
	}

	.beta-notice {
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-md);
		margin-top: var(--space-md);
	}

	.beta-notice p {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin: 0;
	}

	.plan-options {
		margin-bottom: var(--space-lg);
	}

	.cancel-section {
		border-top: 1px solid var(--border);
		padding-top: var(--space-lg);
	}

	.cancel-hint {
		font-size: 0.8rem;
		color: var(--text-tertiary);
		margin-top: var(--space-sm);
	}

	.reset-password {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--space-lg);
	}

	.reset-info {
		flex: 1;
	}

	.reset-info strong {
		display: block;
		margin-bottom: var(--space-xs);
	}

	.reset-info p {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin: 0;
	}

	.danger-zone {
		border-color: rgba(239, 68, 68, 0.3);
	}

	.danger-zone h2 {
		color: var(--danger);
	}

	.delete-account {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--space-lg);
	}

	.delete-info {
		flex: 1;
	}

	.delete-info strong {
		display: block;
		margin-bottom: var(--space-xs);
	}

	.delete-info p {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin: 0;
	}

	.btn {
		padding: var(--space-sm) var(--space-lg);
		border-radius: var(--radius-md);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border: 1px solid transparent;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary {
		background: var(--gradient-accent);
		color: white;
		border: none;
	}

	.btn-primary:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 20px rgba(249, 115, 22, 0.3);
	}

	.btn-secondary {
		background: transparent;
		color: var(--text-primary);
		border: 1px solid var(--border);
	}

	.btn-secondary:hover:not(:disabled) {
		border-color: var(--accent);
	}

	.btn-danger {
		background: var(--danger);
		color: white;
		border: none;
	}

	.btn-danger:hover:not(:disabled) {
		background: #dc2626;
	}

	.btn-danger-outline {
		background: transparent;
		color: var(--danger);
		border: 1px solid var(--danger);
	}

	.btn-danger-outline:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.1);
	}

	.btn-sm {
		padding: var(--space-xs) var(--space-md);
		font-size: 0.8rem;
		white-space: nowrap;
	}
</style>
