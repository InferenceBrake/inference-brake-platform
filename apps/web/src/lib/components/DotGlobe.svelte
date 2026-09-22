<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		size?: number;
		color?: string;
		dots?: number;
		speed?: number;
		class?: string;
	}

	let { size = 200, color = 'var(--color-primary)', dots = 300, speed = 0.28, class: className = '' }: Props = $props();

	let canvas: HTMLCanvasElement | undefined = $state();

	onMount(() => {
		const el = canvas;
		if (!el) return;
		const ctx = el.getContext('2d');
		if (!ctx) return;

		const dpr = Math.min(window.devicePixelRatio || 1, 2);
		el.width = size * dpr;
		el.height = size * dpr;
		ctx.scale(dpr, dpr);

		const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		const ink = getComputedStyle(el).color;

		// Even distribution on a unit sphere (Fibonacci lattice).
		const points: Array<[number, number, number]> = [];
		const golden = Math.PI * (3 - Math.sqrt(5));
		for (let i = 0; i < dots; i++) {
			const y = 1 - (i / (dots - 1)) * 2;
			const r = Math.sqrt(Math.max(0, 1 - y * y));
			const theta = golden * i;
			points.push([Math.cos(theta) * r, y, Math.sin(theta) * r]);
		}

		const cx = size / 2;
		const cy = size / 2;
		const radius = size * 0.42;

		let angle = 0;
		let last = performance.now();
		let raf = 0;

		const frame = (now: number) => {
			const dt = Math.min((now - last) / 1000, 0.05);
			last = now;
			if (!reduce) angle += dt * speed;

			const ca = Math.cos(angle);
			const sa = Math.sin(angle);

			ctx.clearRect(0, 0, size, size);
			ctx.fillStyle = ink;

			for (const [x, y, z] of points) {
				const rx = x * ca - z * sa;
				const rz = x * sa + z * ca;
				const depth = (rz + 1) / 2;
				ctx.globalAlpha = 0.12 + depth * 0.78;
				ctx.beginPath();
				ctx.arc(cx + rx * radius, cy + y * radius, 0.6 + depth * 1.5, 0, Math.PI * 2);
				ctx.fill();
			}
			ctx.globalAlpha = 1;

			raf = requestAnimationFrame(frame);
		};

		raf = requestAnimationFrame(frame);
		return () => cancelAnimationFrame(raf);
	});
</script>

<canvas
	bind:this={canvas}
	class={className}
	style="width:{size}px;height:{size}px;color:{color};"
	aria-hidden="true"
></canvas>
