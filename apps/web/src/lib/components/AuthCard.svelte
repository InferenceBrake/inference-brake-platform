<script lang="ts">
	import type { Snippet } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';

	interface Props {
		title: string;
		subtitle: string;
		children: Snippet;
		footer?: Snippet;
	}

	let { title, subtitle, children, footer }: Props = $props();
</script>

<div class="flex min-h-[85vh] items-center justify-center px-4 py-12">
	<div class="nb-card nb-brutal w-full max-w-md bg-base-100">
		<div class="nb-card-body gap-5 p-6 md:p-8">
			<a href="/" class="flex w-fit items-center gap-3 text-xl font-extrabold">
				<img src={favicon} alt="" class="nb-brutal-sm size-8" />
				InferenceBrake
			</a>
			<div>
				<h1 class="text-2xl font-extrabold">{title}</h1>
				<p class="nb-muted mt-1 font-medium">{subtitle}</p>
			</div>
			{@render children()}
			{#if footer}
				<div class="auth-card-footer nb-muted text-center text-sm font-medium">
					{@render footer()}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.auth-card-footer a {
		font-weight: 700;
		text-decoration: underline;
		text-underline-offset: 4px;
	}
</style>
