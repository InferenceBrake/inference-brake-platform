<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { supabase } from '$lib/supabase';

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

<div class="auth-page">
	<div class="auth-card">
		<a href="/" class="logo">
			<span class="logo-icon"></span>
			InferenceBrake
		</a>

		<h1>Create new password</h1>
		<p class="subtitle">Enter your new password below</p>

		{#if error}
			<div class="error">{error}</div>
		{/if}

		{#if success}
			<div class="success">
				Password reset successfully! Redirecting to login...
			</div>
		{:else}
			<form onsubmit={(e) => { e.preventDefault(); handleReset(); }}>
				<div class="field">
					<label for="password">New Password</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						placeholder="••••••••"
						required
						minlength="8"
					/>
				</div>

				<div class="field">
					<label for="confirmPassword">Confirm Password</label>
					<input
						type="password"
						id="confirmPassword"
						bind:value={confirmPassword}
						placeholder="••••••••"
						required
						minlength="8"
					/>
				</div>

				<button type="submit" class="btn-primary" disabled={loading}>
					{loading ? 'Resetting...' : 'Reset Password'}
				</button>
			</form>
		{/if}

		<p class="footer">
			<a href="/login">Back to sign in</a>
		</p>
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
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 700;
		font-size: 1.25rem;
		margin-bottom: 2rem;
	}

	.logo-icon {
		width: 28px;
		height: 28px;
		background: var(--gradient-accent);
		border-radius: 6px;
	}

	h1 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.subtitle {
		color: var(--text-secondary);
		margin-bottom: 2rem;
	}

	.error {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #ef4444;
		padding: 0.75rem 1rem;
		border-radius: var(--radius-md);
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}

	.success {
		background: rgba(34, 197, 94, 0.1);
		border: 1px solid rgba(34, 197, 94, 0.3);
		color: #22c55e;
		padding: 0.75rem 1rem;
		border-radius: var(--radius-md);
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}

	.field {
		margin-bottom: 1.25rem;
	}

	label {
		display: block;
		font-size: 0.85rem;
		font-weight: 500;
		margin-bottom: 0.5rem;
		color: var(--text-secondary);
	}

	input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		color: var(--text-primary);
		font-size: 1rem;
		transition: border-color 0.2s;
	}

	input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.btn-primary {
		width: 100%;
		padding: 0.875rem;
		background: var(--gradient-accent);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-primary:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 20px rgba(249, 115, 22, 0.3);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.footer {
		margin-top: 1.5rem;
		text-align: center;
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.footer a {
		color: var(--accent);
		font-weight: 500;
	}

	.footer a:hover {
		text-decoration: underline;
	}
</style>
