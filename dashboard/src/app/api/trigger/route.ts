import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  // Verify auth (timing-safe comparison)
  const token = request.cookies.get("lb_auth")?.value;
  const secret = process.env.AUTH_SECRET;
  if (!token || !secret) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const crypto = await import("crypto");
  const tokenBuf = Buffer.from(token);
  const secretBuf = Buffer.from(secret);
  if (tokenBuf.length !== secretBuf.length || !crypto.timingSafeEqual(tokenBuf, secretBuf)) {
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

  // Validate task_id is a valid UUID before using in query
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (taskId && typeof taskId === "string" && uuidRegex.test(taskId)) {
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
    return NextResponse.json({ error: "Failed to trigger agent" }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json({ ok: true, run: data });
}
