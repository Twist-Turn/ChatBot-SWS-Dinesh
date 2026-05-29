-- Chat history table. Run once in the Supabase SQL editor.
--
-- Only the service-role key (used server-side by FastAPI) ever touches this
-- table, so RLS stays disabled. If you later expose the table to the anon
-- key, enable RLS and add a policy that scopes rows by session_id.

create table if not exists public.chat_messages (
    id          bigserial primary key,
    session_id  uuid        not null,
    role        text        not null check (role in ('user', 'assistant')),
    text        text        not null,
    sources     jsonb       not null default '[]'::jsonb,
    created_at  timestamptz not null default now()
);

create index if not exists chat_messages_session_created_idx
    on public.chat_messages (session_id, created_at);
