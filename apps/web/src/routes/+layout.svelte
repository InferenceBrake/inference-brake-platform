<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { onNavigate } from '$app/navigation';

	let { children } = $props();
	
	let user = $state<{ email: string } | null>(null);
	let currentPath = $state(typeof window !== 'undefined' ? window.location.pathname : '/');
	let isAuthPage = $derived(currentPath === '/login' || currentPath === '/register');
	let isDashboard = $derived(currentPath === '/dashboard');
	let isLanding = $derived(currentPath === '/' || currentPath === '');
	
	// Handle navigation - scroll to top
	onNavigate((navigation) => {
		if (!document) return;
		document.startViewTransition?.(() => {});
		// Scroll to top on every navigation
		Promise.resolve().then(() => {
			window.scrollTo(0, 0);
			document.documentElement.scrollTop = 0;
		});
	});
	
	// Subscribe to page changes
	$effect(() => {
		currentPath = $page.url.pathname;
	});
	
	onMount(async () => {
		// Check for stored API key (dev mode)
		const apiKey = localStorage.getItem('inferencebrake_api_key');
		if (apiKey) {
			user = { email: 'Developer Mode' };
		}
		
		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { session } } = await supabase.auth.getSession();
			if (session?.user) {
				user = { email: session.user.email || '' };
			}
					
			supabase.auth.onAuthStateChange((_event, session) => {
				user = session?.user ? { email: session.user.email || '' } : null;
			});
		} catch (e) {
			console.log('Supabase not configured');
		}
	});
	
	async function handleSignOut() {
		const { supabase } = await import('$lib/supabase');
		await supabase.auth.signOut();
		window.location.href = '/';
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>InferenceBrake - Detect Reasoning Loops in AI Agents</title>
	<meta name="description" content="Multi-detector loop detection for AI agents." />
</svelte:head>

<div class="app">
	{#if !isAuthPage}
	<nav class="nav">
		<div class="nav-inner container">
			<a href="/" class="logo">
				<span class="logo-icon"></span>
				InferenceBrake
			</a>
			
			<div class="nav-links">
				{#if isLanding}
					<a href="#detection" class="nav-link">Detection</a>
					<a href="#demo" class="nav-link">Demo</a>
					<a href="#pricing" class="nav-link">Pricing</a>
				{:else}
					<a href="/" class="nav-link">Home</a>
				{/if}
			</div>
			
			<div class="nav-actions">
				{#if user}
					<span class="user-email">{user.email}</span>
					<a href="/dashboard" class="nav-link">Dashboard</a>
					<button class="btn btn-secondary" onclick={handleSignOut}>Sign Out</button>
				{:else}
					<a href="/login" class="nav-link">Sign In</a>
					<a href="/register" class="btn btn-secondary">Get Started</a>
				{/if}
			</div>
		</div>
	</nav>
	{/if}

	<main class:with-nav={!isAuthPage}>
		{@render children()}
	</main>

	{#if !isAuthPage}
	<footer class="footer">
		<div class="container">
			<div class="footer-grid">
				<div class="footer-brand">
					<span class="logo-icon"></span>
					<span class="logo-text">InferenceBrake</span>
					<p>Multi-detector loop detection for AI agents.</p>
				</div>
				
				<div class="footer-col">
					<h4>Product</h4>
					<a href="#pricing">Pricing</a>
				</div>
				
				<div class="footer-col">
					<h4>Legal</h4>
					<a href="/privacy">Privacy</a>
					<a href="/terms">Terms</a>
				</div>
			</div>
			
			<div class="footer-bottom">
				<p>© 2026 InferenceBrake.</p>
			</div>
		</div>
	</footer>
	{/if}
</div>

<style>
	.app {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
	
	.nav {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 1000;
		background: rgba(8, 8, 8, 0.85);
		backdrop-filter: blur(20px);
		border-bottom: 1px solid var(--border);
	}
	
	.nav-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 72px;
	}
	
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
		width: 100%;
	}
	
	.logo {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 700;
		font-size: 1.25rem;
		text-decoration: none;
		color: inherit;
	}
	
	.logo-icon {
		width: 28px;
		height: 28px;
		background: var(--gradient-accent);
		border-radius: 6px;
	}
	
	.nav-links {
		display: flex;
		gap: 2rem;
	}
	
	.nav-link {
		color: var(--text-secondary);
		font-weight: 500;
		font-size: 0.9rem;
		transition: color 0.2s;
		text-decoration: none;
	}
	
	.nav-link:hover {
		color: var(--text-primary);
	}
	
	.nav-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.user-email {
		color: var(--text-secondary);
		font-size: 0.85rem;
	}
	
	main {
		flex: 1;
	}
	
	main.with-nav {
		padding-top: 72px;
	}
	
	.footer {
		margin-top: auto;
		padding: 4rem 0 2rem;
		background: var(--bg-secondary);
		border-top: 1px solid var(--border);
	}
	
	.footer-grid {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr;
		gap: 4rem;
	}
	
	.footer-brand {
		max-width: 300px;
	}
	
	.footer-brand .logo-text {
		font-weight: 700;
		font-size: 1.25rem;
		display: block;
		margin-bottom: 1rem;
	}
	
	.footer-brand p {
		font-size: 0.9rem;
		line-height: 1.6;
	}
	
	.footer-col h4 {
		font-size: 0.85rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: var(--text-primary);
	}
	
	.footer-col a {
		display: block;
		color: var(--text-secondary);
		font-size: 0.9rem;
		padding: 0.35rem 0;
		text-decoration: none;
		transition: color 0.2s;
	}
	
	.footer-col a:hover {
		color: var(--accent);
	}
	
	.footer-bottom {
		margin-top: 3rem;
		padding-top: 2rem;
		border-top: 1px solid var(--border);
		text-align: center;
	}
	
	.footer-bottom p {
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}
</style>
