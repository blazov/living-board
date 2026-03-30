import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE = "lb_auth";

export function middleware(request: NextRequest) {
  // Allow the login API route through
  if (request.nextUrl.pathname === "/api/login") {
    return NextResponse.next();
  }

  const token = request.cookies.get(AUTH_COOKIE)?.value;
  const expectedToken = process.env.AUTH_SECRET;

  if (!expectedToken) {
    // If no secret configured, block everything with a warning
    return new NextResponse("AUTH_SECRET environment variable not set", { status: 503 });
  }

  if (token === expectedToken) {
    return NextResponse.next();
  }

  // Not authenticated -- return the login page
  return new NextResponse(loginHTML(), {
    status: 401,
    headers: { "Content-Type": "text/html" },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

function loginHTML(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Living Board - Login</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a0a; color: #ededed; font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    .card { background: #111; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 32px; width: 100%; max-width: 360px; }
    h1 { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
    .sub { font-size: 13px; color: rgba(255,255,255,0.4); margin-bottom: 24px; }
    input { width: 100%; padding: 10px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #ededed; font-size: 14px; outline: none; margin-bottom: 12px; }
    input:focus { border-color: rgba(255,255,255,0.3); }
    button { width: 100%; padding: 10px; background: #fff; color: #000; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; }
    button:hover { background: rgba(255,255,255,0.9); }
    .error { color: #f87171; font-size: 13px; margin-bottom: 12px; display: none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Living Board</h1>
    <p class="sub">Enter password to continue</p>
    <p class="error" id="error">Incorrect password</p>
    <form id="form">
      <input type="password" id="password" placeholder="Password" autocomplete="current-password" autofocus />
      <button type="submit">Sign in</button>
    </form>
  </div>
  <script>
    document.getElementById('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const pw = document.getElementById('password').value;
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pw }),
      });
      if (res.ok) {
        window.location.reload();
      } else {
        document.getElementById('error').style.display = 'block';
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
      }
    });
  </script>
</body>
</html>`;
}
