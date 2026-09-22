<script lang="ts">
	import { onMount } from 'svelte';

	const THEME_KEY = 'inferencebrake-theme';
	const META_THEME_COLOR = 'meta[name="theme-color"]';
	const LIGHT_THEME = 'brutal';
	const DARK_THEME = 'brutal-dark';
	const LIGHT_COLOR = '#f5efe3';
	const DARK_COLOR = '#1e1d1b';

	let isDark = $state(false);
	let ready = $state(false);

	onMount(() => {
		const media = window.matchMedia('(prefers-color-scheme: dark)');
		const stored = localStorage.getItem(THEME_KEY);

		if (stored) {
			isDark = stored === 'dark';
			applyTheme(isDark);
		} else {
			// No stored choice: let the daisyUI `prefersdark` theme follow the OS.
			isDark = media.matches;
			applyMetaColor(isDark);
		}
		ready = true;

		const handleChange = (event: MediaQueryListEvent) => {
			if (localStorage.getItem(THEME_KEY)) return;
			isDark = event.matches;
			applyMetaColor(isDark);
		};

		media.addEventListener('change', handleChange);
		return () => media.removeEventListener('change', handleChange);
	});

	function toggleTheme() {
		isDark = !isDark;
		localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
		applyTheme(isDark);
	}

	function applyTheme(dark: boolean) {
		document.documentElement.dataset.theme = dark ? DARK_THEME : LIGHT_THEME;
		applyMetaColor(dark);
	}

	function applyMetaColor(dark: boolean) {
		document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
		const meta = document.querySelector(META_THEME_COLOR);
		if (meta) {
			meta.setAttribute('content', dark ? DARK_COLOR : LIGHT_COLOR);
		}
	}
</script>

<button
	type="button"
	class="nb-btn nb-btn-sm nb-brutal-sm nb-brutal-press nb-pop"
	onclick={toggleTheme}
	aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
	title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
	disabled={!ready}
>
	{#if isDark}
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
			<circle cx="12" cy="12" r="4" />
			<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
		</svg>
	{:else}
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
			<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
		</svg>
	{/if}
</button>
