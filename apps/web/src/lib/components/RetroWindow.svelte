<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		class?: string;
		bodyClass?: string;
		children?: Snippet;
	}

	let { title, class: className = '', bodyClass = 'p-4', children }: Props = $props();
</script>

<div class="nb-window {className}">
	<div class="nb-window-bar">
		<span>{title}</span>
		<span class="nb-window-bar-dots" aria-hidden="true"><i></i><i></i><i></i></span>
	</div>
	<div class={bodyClass}>
		{@render children?.()}
	</div>
</div>
