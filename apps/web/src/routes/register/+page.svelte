<script lang="ts">
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import AuthCard from '$lib/components/AuthCard.svelte';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	async function handleRegister() {
		loading = true;
		error = '';

		const { data, error: authError } = await supabase.auth.signUp({
			email,
			password,
			options: {
				emailRedirectTo: `${window.location.origin}/auth/callback`,
			}
		});

		if (authError) {
			error = authError.message;
			loading = false;
			return;
		}

		if (data.user) {
			// Check if already confirmed (dev mode without confirmation)
			const isConfirmed = !!data.user.email_confirmed_at;

			// The DB trigger (handle_new_user) auto-creates the user with api_key, plan, and daily_limit
			// No client-side upsert needed - RLS blocks unauthenticated writes

			if (isConfirmed) {
				// Auto-login if already confirmed (dev mode)
				const { error: signInError } = await supabase.auth.signInWithPassword({
					email,
					password
				});
				if (!signInError) {
					goto('/onboarding');
					return;
				}
			}

			// Show success message about email confirmation
			success = true;
		}
		loading = false;
	}
</script>

<svelte:head>
	<title>Sign Up - InferenceBrake</title>
</svelte:head>

<div class="bg-base-100 text-base-content">
	<AuthCard title="Create account" subtitle="Get started with free loop detection">
		{#if success}
			<div role="alert" class="nb-alert nb-alert-success nb-brutal-sm flex-col items-start gap-3">
				<span class="text-sm font-bold">Check your email to confirm your account!</span>
				<a href="/login" class="nb-btn nb-btn-primary nb-btn-sm nb-brutal-sm nb-brutal-press">Go to Login</a>
			</div>
		{:else}
			{#if error}
				<div role="alert" class="nb-alert nb-alert-error nb-brutal-sm text-sm font-bold">{error}</div>
			{/if}

			<form onsubmit={(e) => { e.preventDefault(); handleRegister(); }} class="flex flex-col gap-5">
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
						minlength="8"
						required
						class="nb-input nb-input-bordered w-full font-medium normal-case"
					/>
					<span class="text-xs font-medium normal-case">Must be at least 8 characters</span>
				</label>

				<button type="submit" class="nb-btn nb-btn-primary nb-brutal nb-brutal-press w-full text-base" disabled={loading}>
					{loading ? 'Creating account...' : 'Create Account'}
				</button>
			</form>
		{/if}

		{#snippet footer()}
			Already have an account? <a href="/login">Sign in</a>
		{/snippet}
	</AuthCard>
</div>
