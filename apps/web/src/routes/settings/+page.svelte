<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let userEmail = $state('');
	let userPlan = $state('hobby');
	let userMonthlyLimit = $state(5000);
	let subscriptionStatus = $state('active');
	let subscriptionPeriodEnd = $state<string | null>(null);
	let apiKey = $state('');
	let testApiKey = $state('');
	let showApiKey = $state(false);
	let showTestApiKey = $state(false);
	let loading = $state(true);
	let processing = $state(false);
	let billingProcessing = $state<string | null>(null);
	let message = $state('');
	let messageType = $state<'success' | 'error'>('success');
	let alertEmail = $state('');
	let webhookUrl = $state('');
	let savingAlerts = $state(false);

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

			// Try direct query first (subject to RLS)
			const { data: userData } = await supabase
				.from('users')
				.select('api_key, test_mode_api_key, plan, monthly_limit, subscription_status, subscription_current_period_end, alert_email, webhook_url')
				.eq('id', authUser.id)
				.single();

			if (userData) {
				apiKey = userData.api_key || '';
				testApiKey = userData.test_mode_api_key || '';
				userPlan = userData.plan || 'hobby';
				userMonthlyLimit = userData.monthly_limit || 5000;
				subscriptionStatus = userData.subscription_status || 'active';
				subscriptionPeriodEnd = userData.subscription_current_period_end;
				alertEmail = userData.alert_email || '';
				webhookUrl = userData.webhook_url || '';
			}

			// If key is missing, fall back to edge function (bypasses RLS)
			if (!apiKey) {
				const { data: fnData, error: fnError } = await supabase.functions.invoke('get-api-key');
				if (fnData?.api_key && !fnError) {
					apiKey = fnData.api_key;
				}
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

	async function regenerateKey() {
		processing = true;
		message = '';

		try {
			const { supabase } = await import('$lib/supabase');
			const { data: fnData, error: fnError } = await supabase.functions.invoke('get-api-key');
			if (fnData?.api_key && !fnError) {
				apiKey = fnData.api_key;
				showApiKey = true;
				showMessage('New API key generated', 'success');
			} else {
				showMessage(fnError?.message || 'Failed to generate key', 'error');
			}
		} catch (e: any) {
			showMessage(e.message || 'Failed to generate key', 'error');
		} finally {
			processing = false;
		}
	}

	function showMessage(msg: string, type: 'success' | 'error') {
		message = msg;
		messageType = type;
		setTimeout(() => { message = ''; }, 5000);
	}

	async function saveAlerts() {
		savingAlerts = true;
		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { user: authUser } } = await supabase.auth.getUser();
			if (!authUser) throw new Error('Not signed in');

			const { error } = await supabase
				.from('users')
				.update({
					alert_email: alertEmail.trim() || null,
					webhook_url: webhookUrl.trim() || null
				})
				.eq('id', authUser.id);

			if (error) throw new Error(error.message);
			showMessage('Alert settings saved', 'success');
		} catch (e: any) {
			showMessage(e.message || 'Failed to save alert settings', 'error');
		} finally {
			savingAlerts = false;
		}
	}

	function getPlanDisplayName(plan: string) {
		if (plan === 'hobby') return 'Free';
		return plan.charAt(0).toUpperCase() + plan.slice(1);
	}

	async function upgradePlan(plan: string) {
		billingProcessing = plan;
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) throw new Error('No API key found');

			const { data, error } = await supabase.functions.invoke('stripe-checkout', {
				body: { plan },
				headers: { Authorization: `Bearer ${storedApiKey}` }
			});

			if (data?.url) {
				window.location.href = data.url;
				return;
			}
			if (data?.demo) {
				userPlan = plan;
				userMonthlyLimit = plan === 'pro' ? 500000 : plan === 'growth' ? 100000 : 5000;
				subscriptionStatus = 'active';
				showMessage('Demo mode - plan updated', 'success');
				return;
			}
			throw new Error(data?.error || error?.message || 'Failed to start checkout');
		} catch (e: any) {
			showMessage(e.message || 'Failed to start checkout', 'error');
		} finally {
			billingProcessing = null;
		}
	}

	async function manageBilling() {
		billingProcessing = 'portal';
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) throw new Error('No API key found');

			const { data, error } = await supabase.functions.invoke('stripe-portal', {
				headers: { Authorization: `Bearer ${storedApiKey}` }
			});

			if (data?.url) {
				window.location.href = data.url;
				return;
			}
			throw new Error(data?.error || error?.message || 'Failed to open billing portal');
		} catch (e: any) {
			showMessage(e.message || 'Failed to open billing portal', 'error');
		} finally {
			billingProcessing = null;
		}
	}

	async function cancelSubscription() {
		if (!confirm('Cancel your subscription? You will be downgraded to the Free plan.')) return;
		billingProcessing = 'cancel';
		try {
			const { supabase } = await import('$lib/supabase');
			const storedApiKey = localStorage.getItem('inferencebrake_api_key');
			if (!storedApiKey) throw new Error('No API key found');

			const { data, error } = await supabase.functions.invoke('stripe-cancel', {
				headers: { Authorization: `Bearer ${storedApiKey}` }
			});

			if (error) throw new Error(error.message);
			if (data?.error) throw new Error(data.error);

			userPlan = 'hobby';
			userMonthlyLimit = 5000;
			subscriptionStatus = 'canceled';
			showMessage('Subscription canceled', 'success');
		} catch (e: any) {
			showMessage(e.message || 'Failed to cancel subscription', 'error');
		} finally {
			billingProcessing = null;
		}
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

<div class="settings-brutal bg-base-100 text-base-content">
	<section class="border-b-2 border-black">
		<div class="mx-auto w-full max-w-3xl px-4 pt-12 pb-10 md:px-8 md:pt-16">
			<p class="nb-muted mb-2 font-mono text-xs font-bold tracking-widest uppercase">Account</p>
			<h1 class="text-4xl font-extrabold tracking-tight md:text-5xl">Settings</h1>
			<p class="nb-muted mt-4 font-medium">Manage your account, subscription, and preferences</p>
		</div>
	</section>

	<div class="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-12 md:gap-8 md:px-8 md:py-16">
		{#if message}
			<div role="alert" class="nb-alert nb-brutal-sm text-sm font-bold {messageType === 'error' ? 'nb-alert-error' : 'nb-alert-success'}">
				{message}
			</div>
		{/if}

		{#if loading}
			<div class="flex flex-col items-center gap-4 py-16">
				<span class="nb-loading nb-loading-spinner nb-loading-lg"></span>
				<p class="nb-muted font-medium">Loading settings...</p>
			</div>
		{:else}
			<div class="flex flex-col gap-6 md:gap-8">
				<section class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">Profile</h2>
							<p class="nb-muted text-sm font-medium">Your account information</p>
						</div>

						<div>
							<p class="nb-muted mb-1 font-mono text-xs font-bold tracking-widest uppercase">Email</p>
							<p class="font-bold">{userEmail}</p>
						</div>

						<div>
							<p class="nb-muted mb-1 font-mono text-xs font-bold tracking-widest uppercase">Account Status</p>
							<span class="nb-badge font-mono text-xs font-bold {subscriptionStatus === 'active' ? 'nb-badge-success' : subscriptionStatus === 'past_due' ? 'nb-badge-error' : 'nb-badge-neutral'}">
								{subscriptionStatus}
							</span>
						</div>
					</div>
				</section>

				<section class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">API Key</h2>
							<p class="nb-muted text-sm font-medium">Your API key for integrating InferenceBrake</p>
						</div>

						{#if apiKey}
							<div class="flex flex-wrap items-center gap-3">
								<code class="block min-w-52 flex-1 border-2 border-black bg-base-200 p-3 font-mono text-sm break-all">{showApiKey ? apiKey : apiKey.slice(0, 12) + '...' + apiKey.slice(-4)}</code>
								<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={() => showApiKey = !showApiKey}>
									{showApiKey ? 'Hide' : 'Show'}
								</button>
								<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={copyApiKey}>
									Copy
								</button>
								<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={regenerateKey} disabled={processing}>
									{processing ? 'Generating...' : 'Regenerate'}
								</button>
							</div>
							<p class="nb-muted text-sm font-medium">Keep this key secret. It provides full access to your account.</p>
						{:else}
							<div class="flex flex-col items-start gap-3">
								<p class="font-medium">No API key found for your account.</p>
								<button class="nb-btn nb-btn-secondary nb-btn-sm nb-brutal-sm nb-brutal-press" onclick={regenerateKey} disabled={processing}>
									{processing ? 'Generating...' : 'Generate API Key'}
								</button>
							</div>
						{/if}
					</div>
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

				<section class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">Plan</h2>
							<p class="nb-muted text-sm font-medium">Your subscription and usage limits</p>
						</div>

						<div class="border-2 border-black bg-base-200 p-4 md:p-5">
							<div class="flex flex-wrap items-center gap-3">
								<span class="text-lg font-extrabold">
									{getPlanDisplayName(userPlan)}
								</span>
								<span class="nb-badge font-mono text-xs font-bold {subscriptionStatus === 'active' ? 'nb-badge-success' : subscriptionStatus === 'past_due' ? 'nb-badge-error' : 'nb-badge-neutral'}">
									{subscriptionStatus}
								</span>
							</div>
							<p class="nb-muted mt-2 text-sm font-medium">
								{userMonthlyLimit.toLocaleString()} checks/month
								{#if subscriptionPeriodEnd && userPlan !== 'hobby'}
									· Renews {formatDate(subscriptionPeriodEnd)}
								{:else}
									· No billing
								{/if}
							</p>
						</div>

						<div class="flex flex-col gap-3">
							{#if userPlan === 'hobby'}
								<button class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press w-full" onclick={() => upgradePlan('growth')} disabled={billingProcessing !== null}>
									{billingProcessing === 'growth' ? 'Redirecting...' : 'Upgrade to Growth - $49/mo'}
								</button>
								<button class="nb-btn nb-btn-primary nb-brutal-sm nb-brutal-press w-full" onclick={() => upgradePlan('pro')} disabled={billingProcessing !== null}>
									{billingProcessing === 'pro' ? 'Redirecting...' : 'Upgrade to Pro - $199/mo'}
								</button>
							{:else}
								<button class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press w-full" onclick={manageBilling} disabled={billingProcessing !== null}>
									{billingProcessing === 'portal' ? 'Opening...' : 'Manage billing'}
								</button>
							{/if}
						</div>

						{#if userPlan !== 'hobby' && subscriptionStatus !== 'canceled'}
							<div class="flex flex-col items-start gap-2">
								<button class="nb-btn nb-btn-error nb-brutal-sm nb-brutal-press" onclick={cancelSubscription} disabled={billingProcessing !== null}>
									{billingProcessing === 'cancel' ? 'Canceling...' : 'Cancel subscription'}
								</button>
								<p class="nb-muted text-sm font-medium">You will be downgraded to the Free plan at the end of the billing period.</p>
							</div>
						{/if}
					</div>
				</section>

				<section class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">Alerts</h2>
							<p class="nb-muted text-sm font-medium">Get notified when a loop is detected and halted</p>
						</div>

						<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
							Email
							<input
								type="email"
								bind:value={alertEmail}
								placeholder="ops@yourcompany.com"
								class="nb-input nb-input-bordered w-full font-medium normal-case"
							/>
						</label>

						<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
							Webhook URL
							<input
								type="url"
								bind:value={webhookUrl}
								placeholder="https://hooks.slack.com/services/..."
								class="nb-input nb-input-bordered w-full font-medium normal-case"
							/>
						</label>

						<button class="nb-btn nb-btn-primary nb-brutal-sm nb-brutal-press" onclick={saveAlerts} disabled={savingAlerts}>
							{savingAlerts ? 'Saving...' : 'Save alerts'}
						</button>
						<p class="nb-muted text-sm font-medium">Alerts fire once per session, on the first detected loop.</p>
					</div>
				</section>

				<section class="nb-card nb-brutal bg-base-100">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">Security</h2>
							<p class="nb-muted text-sm font-medium">Manage your account security</p>
						</div>

						<div class="flex flex-wrap items-center justify-between gap-4">
							<div>
								<p class="font-extrabold">Reset Password</p>
								<p class="nb-muted text-sm font-medium">Send a password reset link to {userEmail}</p>
							</div>
							<button
								class="nb-btn nb-btn-secondary nb-brutal-sm nb-brutal-press"
								onclick={resetPassword}
								disabled={processing}
							>
								{processing ? 'Sending...' : 'Send Reset Email'}
							</button>
						</div>
					</div>
				</section>

				<section class="nb-card nb-brutal bg-error/10">
					<div class="nb-card-body gap-4 p-6 md:p-8">
						<div>
							<h2 class="text-xl font-extrabold">Danger Zone</h2>
							<p class="nb-muted text-sm font-medium">Irreversible account actions</p>
						</div>

						<div class="flex flex-wrap items-center justify-between gap-4">
							<div>
								<p class="font-extrabold">Delete Account</p>
								<p class="nb-muted text-sm font-medium">Permanently delete your account and all associated data. This action cannot be undone.</p>
							</div>
							<button
								class="nb-btn nb-btn-error nb-brutal-sm nb-brutal-press"
								onclick={deleteAccount}
								disabled={processing}
							>
								Delete My Account
							</button>
						</div>
					</div>
				</section>
			</div>
		{/if}
	</div>
</div>

<style>
	.settings-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.settings-brutal h1,
	.settings-brutal h2 {
		color: #171310;
	}
</style>
