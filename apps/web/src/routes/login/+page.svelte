<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/supabase';
	import AuthCard from '$lib/components/AuthCard.svelte';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');
	let queryError = $state('');

	// Check for error query param from callback
	$effect(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const err = urlParams.get('error');
		if (err) {
			if (err === 'email_confirmation_failed') {
				queryError = 'Email confirmation failed. Please try again or request a new confirmation email.';
			} else {
				queryError = err;
			}
		}
	});

	async function handleLogin() {
		loading = true;
		error = '';

		const { error: authError } = await supabase.auth.signInWithPassword({
			email,
			password,
		});

		if (authError) {
			error = authError.message;
			loading = false;
		} else {
			goto('/onboarding');
		}
	}
</script>

<svelte:head>
	<title>Sign In - InferenceBrake</title>
</svelte:head>

<div class="bg-base-100 text-base-content">
	<AuthCard title="Welcome back" subtitle="Sign in to your account">
		{#if error}
			<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm text-sm font-bold">{error}</div>
		{/if}

		{#if queryError}
			<div role="alert" class="nb-alert nb-alert-info nb-brutal-sm text-sm font-bold">{queryError}</div>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); handleLogin(); }} class="flex flex-col gap-5">
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

			<label class="nb-muted flex flex-col gap-2 text-xs font-bold tracking-widest uppercase">
				Password
				<input
					type="password"
					bind:value={password}
					placeholder="••••••••"
					required
					class="nb-input nb-input-bordered w-full font-medium normal-case"
				/>
			</label>

			<button type="submit" class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" disabled={loading}>
				{loading ? 'Signing in...' : 'Sign In'}
			</button>
		</form>

		{#snippet footer()}
			Don't have an account? <a href="/register">Sign up</a>
			<br />
			<a href="/forgot-password">Forgot password?</a>
		{/snippet}
	</AuthCard>
</div>
