import { sveltekit } from '@sveltejs/kit/vite';
import { sentrySvelteKit } from '@sentry/sveltekit';
import { defineConfig } from 'vite';

const sentryPlugin = sentrySvelteKit({
  adapter: 'vercel',
});

export default defineConfig({
	plugins: [
		sentryPlugin(),
		sveltekit()
	]
});
