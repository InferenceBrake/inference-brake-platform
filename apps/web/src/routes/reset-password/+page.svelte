<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { supabase } from '$lib/supabase';
	import AuthCard from '$lib/components/AuthCard.svelte';

	let password = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	onMount(async () => {
		const { data: { session } } = await supabase.auth.getSession();
		if (!session) {
			const hashParams = new URLSearchParams(window.location.hash.substring(1));
			const accessToken = hashParams.get('access_token');
			const type = hashParams.get('type');

			if (accessToken && type === 'recovery') {
				const { error: setError } = await supabase.auth.setSession({
					access_token: accessToken,
					refresh_token: hashParams.get('refresh_token') || '',
				});
				if (setError) {
					error = setError.message;
				}
			}
		}
	});

	async function handleReset() {
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		if (password.length < 8) {
			error = 'Password must be at least 8 characters';
			return;
		}

		loading = true;
		error = '';

		const { error: authError } = await supabase.auth.updateUser({ password });

		if (authError) {
			error = authError.message;
			loading = false;
		} else {
			success = true;
			setTimeout(() => {
				goto('/login');
			}, 2000);
		}
	}
</script>

<svelte:head>
	<title>Reset Password - InferenceBrake</title>
</svelte:head>

<div class="bg-base-100 text-base-content">
	<AuthCard title="Create new password" subtitle="Enter your new password below">
		{#if error}
			<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm text-sm font-bold">{error}</div>
		{/if}

		{#if success}
			<div role="alert" class="nb-alert nb-alert-success nb-brutal-sm text-sm font-bold">
				Password reset successfully! Redirecting to login...
			</div>
		{:else}
			<form onsubmit={(e) => { e.preventDefault(); handleReset(); }} class="flex flex-col gap-5">
				<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
					New Password
					<input
						type="password"
						bind:value={password}
						placeholder="••••••••"
						required
						minlength="8"
						class="nb-input nb-input-bordered w-full font-medium normal-case"
					/>
				</label>

				<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
					Confirm Password
					<input
						type="password"
						bind:value={confirmPassword}
						placeholder="••••••••"
						required
						minlength="8"
						class="nb-input nb-input-bordered w-full font-medium normal-case"
					/>
				</label>

				<button type="submit" class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" disabled={loading}>
					{loading ? 'Resetting...' : 'Reset Password'}
				</button>
			</form>
		{/if}

		{#snippet footer()}
			<a href="/login">Back to sign in</a>
		{/snippet}
	</AuthCard>
</div>
