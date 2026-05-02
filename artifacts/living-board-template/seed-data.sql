-- Living Board: Example Seed Data
-- Insert this after running schema.sql to see the system in action.
-- Idempotent: safe to re-run (ON CONFLICT DO NOTHING on all inserts).

-- Example goal
INSERT INTO goals (id, title, description, status, priority, created_by) VALUES
  ('00000000-0000-0000-0000-000000000001', 'Write a weekly newsletter',
   'Publish a weekly newsletter covering AI agent developments. Research topics, draft articles, and build a subscriber base.',
   'in_progress', 3, 'user')
ON CONFLICT DO NOTHING;

-- Example tasks for the goal
INSERT INTO tasks (goal_id, title, description, sort_order, metadata) VALUES
  ('00000000-0000-0000-0000-000000000001',
   'Research newsletter platforms',
   'Compare Substack, Ghost, Buttondown, and Beehiiv. Evaluate API access, pricing, and audience discovery features.',
   10, '{"created_by": "agent"}'::jsonb),
  ('00000000-0000-0000-0000-000000000001',
   'Define content niche and voice',
   'Draft a 1-page content strategy: target audience, topic boundaries, tone, posting cadence.',
   20, '{"created_by": "agent"}'::jsonb),
  ('00000000-0000-0000-0000-000000000001',
   'Write first article draft',
   'Research a trending AI topic and write a 1000-1500 word article. Save to artifacts/content/.',
   30, '{"created_by": "agent"}'::jsonb),
  ('00000000-0000-0000-0000-000000000001',
   'Publish and promote first article',
   'Publish the draft to the chosen platform. Write 2-3 social posts to drive initial traffic.',
   40, '{"created_by": "agent"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Example learnings
INSERT INTO learnings (goal_id, category, content, confidence) VALUES
  (NULL, 'operational',
   'Always verify file existence after writing and commit in the same cycle as file creation.',
   0.95),
  (NULL, 'strategy',
   'Infrastructure without content is worthless. Ship content before optimizing the pipeline.',
   0.9),
  ('00000000-0000-0000-0000-000000000001', 'domain_knowledge',
   'Substack has no public API for publishing -- must use the web editor or build a workaround.',
   0.9)
ON CONFLICT DO NOTHING;
