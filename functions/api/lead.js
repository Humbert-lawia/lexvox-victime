// Cloudflare Pages Function — Envoi email compte-rendu chatbot
// Variables d'environnement Cloudflare à configurer :
//   RESEND_API_KEY  → clé API Resend (https://resend.com — gratuit jusqu'à 100 emails/jour)
//   NOTIFY_EMAIL    → adresse de réception (ex: contact@avocat-lexvox.com)

export async function onRequestPost(context) {
  const RESEND_KEY = context.env.RESEND_API_KEY;
  const NOTIFY_EMAIL = context.env.NOTIFY_EMAIL || 'contact@avocat-lexvox.com';

  if (!RESEND_KEY) {
    // Pas de clé → log silencieux, ne pas bloquer l'UX
    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  let body;
  try {
    body = await context.request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), { status: 400 });
  }

  const { lead = {}, conversation = '', page = '', userAgent = '' } = body;
  const now = new Date().toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });

  const htmlBody = `
<html><body style="font-family:Arial,sans-serif;color:#141413;max-width:700px;margin:auto;padding:20px">
<h2 style="color:#4A7BA8;border-bottom:2px solid #4A7BA8;padding-bottom:8px">
  🤖 Nouvelle conversation chatbot LEXVOX
</h2>
<table style="width:100%;border-collapse:collapse;margin-bottom:20px">
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold;width:140px">Date</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${now}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Page visitée</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${escHtml(page)}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Nom</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${escHtml(lead.name || 'Non renseigné')}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Téléphone</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${escHtml(lead.phone || 'Non renseigné')}</td></tr>
  <tr><td style="padding:8px;background:#f5f5f0;font-weight:bold">Email</td>
      <td style="padding:8px;border-bottom:1px solid #ddd">${escHtml(lead.email || 'Non renseigné')}</td></tr>
</table>

<h3 style="color:#4A7BA8">📝 Transcript de la conversation</h3>
<div style="background:#f9f9f7;border:1px solid #ddd;border-radius:6px;padding:16px;white-space:pre-wrap;font-size:0.9rem;line-height:1.6">
${escHtml(conversation)}
</div>

<p style="color:#888;font-size:0.8rem;margin-top:20px">
  Envoyé automatiquement par le chatbot Sophia — LEXVOX AVOCATS<br>
  ${escHtml(userAgent)}
</p>
</body></html>`;

  function escHtml(str) {
    return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_KEY}`
      },
      body: JSON.stringify({
        from: 'Chatbot LEXVOX <noreply@lexvox-victime.com>',
        to: [NOTIFY_EMAIL],
        subject: `[Chatbot] Nouvelle conversation${lead.name ? ' — ' + lead.name : ''}${lead.phone ? ' — ' + lead.phone : ''}`,
        html: htmlBody
      })
    });

    const data = await res.json();
    return new Response(JSON.stringify({ ok: true, id: data.id }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: e.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
