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
					setTimeout(() => goto('/dashboard'), 1500);
					return;
				}
			}

			const { data: { session } } = await supabase.auth.getSession();
			
			if (session) {
				status = 'success';
				setTimeout(() => goto('/dashboard'), 1500);
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

<div class="auth-page">
	<div class="auth-card">
		{#if status === 'loading'}
			<div class="loading">
				<div class="spinner"></div>
				<p>Confirming your email...</p>
			</div>
		{:else if status === 'success'}
			<div class="success-content">
				<div class="check-icon">✓</div>
				<p>Email confirmed!</p>
				<span class="redirect">Redirecting to dashboard...</span>
			</div>
		{:else}
			<div class="error-content">
				<div class="error-icon">✕</div>
				<p>Confirmation failed</p>
				<span class="error-detail">{errorMessage}</span>
				<a href="/login" class="btn">Go to Login</a>
			</div>
		{/if}
	</div>
</div>

<style>
	.auth-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		background: radial-gradient(ellipse at top, rgba(249, 115, 22, 0.08) 0%, transparent 60%);
	}

	.auth-card {
		width: 100%;
		max-width: 400px;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-xl);
		padding: 2.5rem;
		text-align: center;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.check-icon {
		width: 60px;
		height: 60px;
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		margin: 0 auto 1rem;
	}

	.error-icon {
		width: 60px;
		height: 60px;
		background: rgba(239, 68, 68, 0.2);
		color: #ef4444;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		margin: 0 auto 1rem;
	}

	.success-content p, .error-content p {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	.redirect {
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.error-detail {
		color: var(--text-secondary);
		font-size: 0.85rem;
		display: block;
		margin-bottom: 1rem;
	}

	.btn {
		display: inline-block;
		padding: 0.75rem 1.5rem;
		background: var(--gradient-accent);
		color: white;
		border-radius: var(--radius-md);
		text-decoration: none;
		font-weight: 500;
	}
</style>
