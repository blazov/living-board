import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const password = typeof body?.password === "string" ? body.password : "";
  const secret = process.env.AUTH_SECRET;

  if (!secret) {
    return NextResponse.json({ error: "Not configured" }, { status: 503 });
  }

  // Constant-time comparison to prevent timing attacks
  const encoder = new TextEncoder();
  const a = encoder.encode(password);
  const b = encoder.encode(secret);

  if (a.length !== b.length) {
    return NextResponse.json({ error: "Invalid" }, { status: 401 });
  }

  const crypto = await import("crypto");
  const match = crypto.timingSafeEqual(a, b);

  if (!match) {
    return NextResponse.json({ error: "Invalid" }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set("lb_auth", secret, {
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    maxAge: 60 * 60 * 24 * 30, // 30 days
    path: "/",
  });
  return response;
}
