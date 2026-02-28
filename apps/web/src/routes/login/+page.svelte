<script lang="ts">
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');

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
			goto('/dashboard');
		}
	}
</script>

<svelte:head>
	<title>Sign In - InferenceBrake</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-card">
		<a href="/" class="logo">
			<span class="logo-icon"></span>
			InferenceBrake
		</a>

		<h1>Welcome back</h1>
		<p class="subtitle">Sign in to your account</p>

		{#if error}
			<div class="error">{error}</div>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
			<div class="field">
				<label for="email">Email</label>
				<input
					type="email"
					id="email"
					bind:value={email}
					placeholder="you@example.com"
					required
				/>
			</div>

			<div class="field">
				<label for="password">Password</label>
				<input
					type="password"
					id="password"
					bind:value={password}
					placeholder="••••••••"
					required
				/>
			</div>

			<button type="submit" class="btn-primary" disabled={loading}>
				{loading ? 'Signing in...' : 'Sign In'}
			</button>
		</form>

		<p class="footer">
			Don't have an account? <a href="/register">Sign up</a>
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
