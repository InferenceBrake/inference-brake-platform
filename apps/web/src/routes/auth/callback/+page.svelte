<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/supabase';

	let status = $state<'loading' | 'success' | 'error'>('loading');
	let errorMessage = $state('');

	onMount(async () => {
		try {
			const hashParams = new URLSearchParams(window.location.hash.substring(1));
			const accessToken = hashParams.get('access_token');
			const refreshToken = hashParams.get('refresh_token');
			const type = hashParams.get('type');

			if (accessToken && refreshToken) {
				const { data, error } = await supabase.auth.setSession({
					access_token: accessToken,
					refresh_token: refreshToken,
				});

				if (error) {
					console.error('Session error:', error);
					status = 'error';
					errorMessage = error.message;
					return;
				}

				if (data.session) {
					status = 'success';
					setTimeout(() => goto('/onboarding'), 1500);
					return;
				}
			}

			const { data: { session } } = await supabase.auth.getSession();

			if (session) {
				status = 'success';
				setTimeout(() => goto('/onboarding'), 1500);
			} else {
				status = 'error';
				errorMessage = 'No session found';
			}
		} catch (err: any) {
			console.error('Auth callback error:', err);
			status = 'error';
			errorMessage = err.message || 'Confirmation failed';
		}
	});
</script>

<svelte:head>
	<title>Confirming Email - InferenceBrake</title>
</svelte:head>

<div class="bg-base-100 text-base-content">
	<div class="flex min-h-[85vh] items-center justify-center px-4 py-12">
		<div class="nb-card nb-brutal w-full max-w-md bg-base-100">
			<div class="nb-card-body items-center gap-4 p-6 text-center md:p-8">
				{#if status === 'loading'}
					<span class="nb-loading nb-loading-spinner nb-loading-lg"></span>
					<p class="font-bold">Confirming your email...</p>
				{:else if status === 'success'}
					<span class="nb-brutal-sm flex size-16 items-center justify-center bg-success text-2xl font-extrabold text-success-content">✓</span>
					<p class="text-xl font-extrabold">Email confirmed!</p>
					<p class="nb-muted text-sm font-medium">Redirecting to dashboard...</p>
				{:else}
					<span class="nb-brutal-sm flex size-16 items-center justify-center bg-error text-2xl font-extrabold text-error-content">✕</span>
					<p class="text-xl font-extrabold">Confirmation failed</p>
					<p class="nb-muted text-sm font-medium">{errorMessage}</p>
					<a href="/login" class="nb-btn nb-btn-primary nb-brutal-sm nb-brutal-press">Go to Login</a>
				{/if}
			</div>
		</div>
	</div>
</div>
