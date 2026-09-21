<script lang="ts">
	import type { Snippet } from 'svelte';

	export type StatTone =
		| 'primary'
		| 'secondary'
		| 'accent'
		| 'success'
		| 'warning'
		| 'error'
		| 'neutral';

	interface Props {
		label: string;
		value: string;
		desc?: string;
		tone?: StatTone;
		icon?: Snippet;
	}

	let { label, value, desc, tone = 'primary', icon }: Props = $props();

	const toneChip: Record<StatTone, string> = {
		primary: 'bg-primary text-primary-content',
		secondary: 'bg-secondary text-secondary-content',
		accent: 'bg-accent text-accent-content',
		success: 'bg-success text-success-content',
		warning: 'bg-warning text-warning-content',
		error: 'bg-error text-error-content',
		neutral: 'bg-neutral text-neutral-content'
	};
</script>

<div class="nb-stats nb-brutal w-full bg-base-100">
	<div class="nb-stat gap-2 p-8">
		{#if icon}
			<div class="nb-stat-figure">
				<div class="nb-brutal-sm flex size-12 items-center justify-center {toneChip[tone]}">
					{@render icon()}
				</div>
			</div>
		{/if}
		<div class="nb-stat-title nb-muted text-xs font-bold tracking-wide uppercase">{label}</div>
		<div class="nb-stat-value font-mono">{value}</div>
		{#if desc}
			<div class="nb-stat-desc nb-muted">{desc}</div>
		{/if}
	</div>
</div>
