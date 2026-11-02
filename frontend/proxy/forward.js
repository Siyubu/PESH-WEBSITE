// Cloudflare Pages Functions pass /api, /admin and /static to the Django backend, so the browser only ever
// talks to one site and the session cookie and CSRF protection keep working. Set BACKEND_URL (for example
// https://pesh-backend.onrender.com) in the Pages project's environment variables.
export async function forward({ request, env }) {
  const backend = (env.BACKEND_URL || "").replace(/\/+$/, "");
  if (!backend) return new Response("BACKEND_URL is not set", { status: 500 });

  const url = new URL(request.url);
  const upstream = new Request(new URL(url.pathname + url.search, backend), request);
  const res = await fetch(upstream, { redirect: "manual" });

  const out = new Response(res.body, res);
  const location = out.headers.get("Location");
  if (location && location.startsWith(backend)) out.headers.set("Location", location.slice(backend.length) || "/");
  return out;
}
