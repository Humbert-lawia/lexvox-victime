// Cloudflare Pages Function — chatbot Sophia via Gemini API
// Clé stockée dans GEMINI_API_KEY (variable d'environnement Cloudflare)

export async function onRequestPost(context) {
  const GEMINI_KEY = context.env.GEMINI_API_KEY;

  if (!GEMINI_KEY) {
    return new Response(JSON.stringify({ error: 'API key not configured' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  try {
    const body = await context.request.json();
    const messages = body.messages || [];

    // Extraire le system prompt (premier message de rôle "system")
    let systemText = '';
    const conversationMessages = [];
    for (const msg of messages) {
      if (msg.role === 'system') {
        systemText = msg.content;
      } else {
        conversationMessages.push(msg);
      }
    }

    // Convertir au format Gemini
    const geminiContents = conversationMessages.map(msg => ({
      role: msg.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: msg.content }]
    }));

    const geminiBody = {
      system_instruction: systemText ? { parts: [{ text: systemText }] } : undefined,
      contents: geminiContents,
      generationConfig: {
        maxOutputTokens: body.max_tokens || 500,
        temperature: body.temperature || 0.7
      }
    };

    const geminiResp = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(geminiBody)
      }
    );

    if (!geminiResp.ok) {
      const errText = await geminiResp.text();
      return new Response(JSON.stringify({ error: 'Gemini error ' + geminiResp.status, detail: errText }), {
        status: 502,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    const geminiData = await geminiResp.json();
    const text = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text || '';

    // Retourner au format OpenAI-compatible (chatbot.js n'a pas besoin d'être modifié)
    return new Response(JSON.stringify({
      choices: [{ message: { role: 'assistant', content: text } }]
    }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }
}

// Handle CORS preflight
export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
