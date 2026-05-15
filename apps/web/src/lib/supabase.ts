import { createClient, type SupabaseClient } from '@supabase/supabase-js';

let _client: SupabaseClient | null = null;

function getClient(): SupabaseClient {
	if (!_client) {
		const supabaseUrl = import.meta.env.VITE_PUBLIC_SUPABASE_URL || '';
		const supabaseAnonKey = import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY || '';
		if (!supabaseUrl || !supabaseAnonKey) {
			console.warn('Supabase environment variables not set. Set VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY in your .env file or Vercel project settings.');
		}
		_client = createClient(supabaseUrl, supabaseAnonKey);
	}
	return _client;
}

export const supabase = new Proxy<SupabaseClient>({} as SupabaseClient, {
	get(_, prop) {
		return getClient()[prop as keyof SupabaseClient];
	}
});
