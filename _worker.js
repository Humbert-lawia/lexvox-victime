/**
 * Cloudflare Pages Worker — LEXVOX AVOCATS
 * Gère les routes API :
 *   POST /api/chat  → proxy OpenAI ChatGPT
 *   POST /api/lead  → envoi email via Resend
 *
 * Variables d'environnement requises (Cloudflare Pages > Settings > Variables) :
 *   OPENAI_API_KEY  → clé API OpenAI
 *   RESEND_API_KEY  → clé API Resend
 *   NOTIFY_EMAIL    → email de notification (contact@avocat-lexvox.com)
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function corsResponse(body, status, extraHeaders) {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS, ...extraHeaders },
  });
}

async function handleChat(request, env) {
  const OPENAI_KEY = env.OPENAI_API_KEY;
  if (!OPENAI_KEY) {
    return corsResponse(JSON.stringify({ error: 'OPENAI_API_KEY non configurée' }), 500);
  }

  try {
    const body = await request.json();

    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${OPENAI_KEY}`,
      },
      body: JSON.stringify({
        model: body.model || 'gpt-4o-mini',
        messages: body.messages,
        max_tokens: body.max_tokens || 500,
        temperature: body.temperature || 0.7,
      }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      return corsResponse(JSON.stringify({ error: data.error || 'OpenAI error', status: resp.status }), 502);
    }

    return corsResponse(JSON.stringify(data), 200);
  } catch (e) {
    return corsResponse(JSON.stringify({ error: e.message }), 500);
  }
}

async function handleLead(request, env) {
  const RESEND_KEY = env.RESEND_API_KEY;
  const NOTIFY = env.NOTIFY_EMAIL || 'contact@avocat-lexvox.com';

  try {
    const body = await request.json();
    const { lead = {}, conversation = '', page = '' } = body;

    if (!RESEND_KEY) {
      // Pas de clé → log silencieux, ne pas bloquer
      return corsResponse(JSON.stringify({ ok: true, note: 'no key' }), 200);
    }

    const now = new Date().toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
    const htmlBody = `
<h2 style="color:#141413">Nouveau lead chatbot Sophia — LEXVOX</h2>
<table style="border-collapse:collapse;width:100%;max-width:600px">
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Date</td><td style="padding:8px">${now}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Page</td><td style="padding:8px">${page}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Nom</td><td style="padding:8px">${lead.name || '—'}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Téléphone</td><td style="padding:8px">${lead.phone || '—'}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Email</td><td style="padding:8px">${lead.email || '—'}</td></tr>
</table>
<h3 style="color:#4A7BA8;margin-top:24px">Conversation complète</h3>
<pre style="background:#f9f9f5;padding:16px;border-radius:6px;white-space:pre-wrap;font-size:13px">${conversation}</pre>
`;

    const resendResp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${RESEND_KEY}`,
      },
      body: JSON.stringify({
        from: 'Sophia LEXVOX <onboarding@resend.dev>',
        to: [NOTIFY],
        subject: `💬 Nouveau lead chatbot — ${lead.name || 'Visiteur'} — ${now}`,
        html: htmlBody,
      }),
    });

    const resendData = await resendResp.json().catch(() => ({}));
    return corsResponse(JSON.stringify({ ok: resendResp.ok, status: resendResp.status, detail: resendData }), 200);
  } catch (e) {
    return corsResponse(JSON.stringify({ ok: false, error: e.message }), 500);
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const { pathname } = url;
    const method = request.method.toUpperCase();

    // Redirection www → non-www (301)
    if (url.hostname.startsWith('www.')) {
      const nonWwwUrl = request.url.replace(`://${url.hostname}`, `://${url.hostname.slice(4)}`);
      return Response.redirect(nonWwwUrl, 301);
    }

    // CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // Route /api/chat
    if (pathname === '/api/chat' && method === 'POST') {
      return handleChat(request, env);
    }

    // Route /api/lead
    if (pathname === '/api/lead' && method === 'POST') {
      return handleLead(request, env);
    }

    // Toutes les autres routes → servir les assets statiques
    return env.ASSETS.fetch(request);
  },
};
