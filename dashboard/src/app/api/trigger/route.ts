import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  // Verify auth
  const token = request.cookies.get("lb_auth")?.value;
  if (token !== process.env.AUTH_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const apiKey = process.env.CLAUDE_API_KEY;
  const triggerId = process.env.TRIGGER_ID;

  if (!apiKey || !triggerId) {
    return NextResponse.json(
      { error: "CLAUDE_API_KEY or TRIGGER_ID not configured" },
      { status: 503 }
    );
  }

  const body = await request.json().catch(() => ({}));
  const taskId = body.task_id;

  // If a specific task was requested, mark it as in_progress in Supabase
  // so the agent picks it up. The agent's Orient phase checks for in_progress tasks first.
  if (taskId) {
    const { createClient } = await import("@supabase/supabase-js");
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    await supabase
      .from("tasks")
      .update({ status: "in_progress", started_at: new Date().toISOString() })
      .eq("id", taskId);
  }

  // Trigger the remote agent via Claude API
  const res = await fetch(
    `https://api.anthropic.com/v1/code/triggers/${triggerId}/run`,
    {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
    }
  );

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json({ ok: true, run: data });
}
