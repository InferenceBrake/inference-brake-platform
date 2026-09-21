<script lang="ts">
	import { supabase } from '$lib/supabase';
	import AuthCard from '$lib/components/AuthCard.svelte';

	let email = $state('');
	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	async function handleResetRequest() {
		loading = true;
		error = '';

		const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
			redirectTo: `${window.location.origin}/reset-password`,
		});

		if (authError) {
			error = authError.message;
			loading = false;
		} else {
			success = true;
		}
	}
</script>

<svelte:head>
	<title>Forgot Password - InferenceBrake</title>
</svelte:head>

<div class="bg-base-100 text-base-content">
	<AuthCard title="Reset your password" subtitle="Enter your email and we'll send you a reset link">
		{#if error}
			<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm text-sm font-bold">{error}</div>
		{/if}

		{#if success}
			<div role="alert" class="nb-alert nb-alert-success nb-brutal-sm text-sm font-bold">
				Check your email for a password reset link. The link will expire in 1 hour.
			</div>
		{:else}
			<form onsubmit={(e) => { e.preventDefault(); handleResetRequest(); }} class="flex flex-col gap-5">
				<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
					Email
					<input
						type="email"
						bind:value={email}
						placeholder="you@example.com"
						required
						class="nb-input nb-input-bordered w-full font-medium normal-case"
					/>
				</label>

				<button type="submit" class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" disabled={loading}>
					{loading ? 'Sending...' : 'Send Reset Link'}
				</button>
			</form>
		{/if}

		{#snippet footer()}
			Remember your password? <a href="/login">Sign in</a>
		{/snippet}
	</AuthCard>
</div>
