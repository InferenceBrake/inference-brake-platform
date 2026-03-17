-- Waitlist table for beta users who want to be notified about Pro plan
create table if not exists waitlist (
    id uuid default gen_random_uuid() primary key,
    email text not null unique,
    created_at timestamptz default now()
);

-- RLS
alter table waitlist enable row level security;

-- Allow anyone to insert their email
create policy "Allow anyone to join waitlist" on waitlist
    for insert with check (true);

-- Allow only service role to read
create policy "Service role can read waitlist" on waitlist
    for select using (true);
