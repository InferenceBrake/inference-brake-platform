<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
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
		try {
			const { supabase } = await import('$lib/supabase');
			const { data: { session } } = await supabase.auth.getSession();
			if (session?.user) {
				user = { email: session.user.email || '' };
			}

			supabase.auth.onAuthStateChange((_event, session) => {
				if (!session?.user) {
					localStorage.removeItem('inferencebrake_api_key');
				}
				user = session?.user ? { email: session.user.email || '' } : null;
			});
		} catch (e) {
			console.log('Supabase not configured');
		}
	});

	async function handleSignOut() {
		if (!confirm('Are you sure you want to sign out?')) return;
		const { supabase } = await import('$lib/supabase');
		try {
			await supabase.auth.signOut();
		} catch (e) {
			console.error('Sign out error:', e);
		}
		localStorage.removeItem('inferencebrake_api_key');
		window.location.href = '/';
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
	<meta name="theme-color" content="#f5efe3" />
	<title>InferenceBrake - Detect Reasoning Loops in AI Agents</title>
	<meta name="description" content="Multi-detector loop detection for AI agents." />
</svelte:head>

<div class="flex min-h-screen flex-col bg-base-100 text-base-content">
	<div class="nb-ticks" aria-hidden="true"></div>
	{#if !isAuthPage}
		<nav class="fixed inset-x-0 top-0 z-50 border-b-2 border-base-content bg-base-100">
			<div class="mx-auto flex h-18 w-full max-w-6xl items-center justify-between gap-4 px-4 md:px-8">
				<a href="/" class="flex items-center gap-2 text-xl font-extrabold">
					<img src={favicon} alt="" class="nb-brutal-sm size-7" />
					InferenceBrake
				</a>

			<div class="hidden items-center gap-6 md:flex">
				{#if isLanding}
					<a href="#detection" class="text-sm font-bold hover:underline hover:underline-offset-4">Detection</a>
					<a href="#demo" class="text-sm font-bold hover:underline hover:underline-offset-4">Demo</a>
					<a href="#pricing" class="text-sm font-bold hover:underline hover:underline-offset-4">Pricing</a>
				{:else}
					<a href="/" class="text-sm font-bold hover:underline hover:underline-offset-4">Home</a>
					<a href="/docs" class="text-sm font-bold hover:underline hover:underline-offset-4">Docs</a>
				{/if}
			</div>

			<div class="flex items-center gap-3">
				<ThemeToggle />
				{#if user}
					<span class="nb-muted hidden font-mono text-xs lg:block">{user.email}</span>
					<a href="/dashboard" class="hidden text-sm font-bold hover:underline hover:underline-offset-4 sm:block">Dashboard</a>
					<a href="/settings" class="hidden text-sm font-bold hover:underline hover:underline-offset-4 sm:block">Settings</a>
					<button class="nb-btn nb-btn-neutral nb-btn-sm nb-brutal-sm" onclick={handleSignOut}>Sign Out</button>
				{:else}
					<a href="/login" class="text-sm font-bold hover:underline hover:underline-offset-4">Sign In</a>
					<a href="/register" class="nb-btn nb-btn-primary nb-btn-sm nb-brutal-sm nb-pop">Get Started</a>
				{/if}
			</div>
		</div>
	</nav>
	{/if}

	<main class="flex-1" class:pt-18={!isAuthPage}>
		{@render children()}
	</main>

	{#if !isAuthPage}
	<footer class="border-t-2 border-base-content bg-neutral text-neutral-content">
		<div class="mx-auto w-full max-w-6xl px-4 py-12 md:px-8">
			<div class="grid gap-10 md:grid-cols-[2fr_1fr_1fr]">
				<div>
					<p class="flex items-center gap-2 text-xl font-extrabold">
						<img src={favicon} alt="" class="size-7 border-2 border-base-content bg-base-100 p-0.5" />
						InferenceBrake
					</p>
					<p class="mt-4 max-w-xs text-sm font-medium opacity-70">Multi-detector loop detection for AI agents.</p>
				</div>

				<div>
					<h4 class="mb-4 font-mono text-xs font-bold tracking-widest uppercase">Product</h4>
					<a href="#pricing" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Pricing</a>
					<a href="/docs" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Docs</a>
					<a href="/dashboard" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Dashboard</a>
					<a href="/settings" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Settings</a>
				</div>

				<div>
					<h4 class="mb-4 font-mono text-xs font-bold tracking-widest uppercase">Legal</h4>
					<a href="/impressum" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Impressum</a>
					<a href="/privacy" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Privacy</a>
					<a href="/terms" class="block py-1 text-sm font-medium opacity-70 hover:opacity-100 hover:underline hover:underline-offset-4">Terms</a>
				</div>
			</div>

			<div class="mt-10 border-t border-neutral-content/20 pt-6 text-center">
				<p class="font-mono text-xs opacity-70">© 2026 InferenceBrake.</p>
			</div>
		</div>
	</footer>
	{/if}
</div>
