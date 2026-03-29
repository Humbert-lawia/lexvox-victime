/**
 * LEXVOX AVOCATS — Chatbot IA (OpenAI GPT-4o-mini)
 * Assistant virtuel pour capture leads et orientation RDV
 * JAMAIS de conseil juridique
 */
(function() {
  'use strict';

  // Proxy API — clé sécurisée côté serveur (Cloudflare Pages Function)
  var API_URL = '/api/chat';

  var SYSTEM_PROMPT = "Tu es l'assistante virtuelle du cabinet d'avocats LEXVOX AVOCATS. Tu t'appelles Sophia.\n\n" +
    "REGLES ABSOLUES :\n" +
    "1. Tu ne donnes JAMAIS de conseil juridique. Tu n'es pas avocate.\n" +
    "2. Tu orientes vers un rendez-vous avec un avocat du cabinet.\n" +
    "3. Tu es empathique, chaleureuse et rassurante avec les victimes.\n" +
    "4. Tu reponds d'abord a 1 ou 2 questions de la personne pour comprendre sa situation AVANT de demander ses coordonnees. NE DEMANDE PAS les coordonnees immediatement, c'est trop agressif.\n" +
    "5. Apres avoir compris la situation, propose naturellement un RDV et demande les coordonnees.\n" +
    "6. Bureaux et avocats :\n" +
    "   - Arles → Me Cedrine RAYBAUD\n" +
    "   - Salon-de-Provence → Me Patrice HUMBERT\n" +
    "   - Marignane → Me Patrice HUMBERT\n" +
    "   Les deux avocats peuvent intervenir dans tous les domaines.\n" +
    "7. Distingue nouveau client (→ proposer RDV) vs client existant (→ noter infos + rappel avocat).\n" +
    "8. Sois concise (reponses courtes, 2-3 phrases max).\n" +
    "9. Le cabinet defend EXCLUSIVEMENT les victimes, JAMAIS les assureurs.\n" +
    "10. Premiere consultation gratuite 30 min.\n" +
    "11. Contact : 04 90 54 58 10 / contact@avocat-lexvox.com\n" +
    "12. PRISE DE RDV : Quand la personne veut prendre RDV, envoie-lui TOUJOURS ce lien pour qu'elle puisse reserver un creneau directement : https://consultation.avocat.fr/avocat-marignane/patrice-humbert-12417.html — dis-lui 'Vous pouvez reserver directement votre creneau de consultation gratuite ici' et donne le lien.\n" +
    "13. Si la personne prefere appeler : 04 90 54 58 10\n\n" +
    "Domaines : dommage corporel, accident de la route, erreur medicale, infection nosocomiale, " +
    "accident du travail, agression, divorce, droit de la famille, violences conjugales, permis de conduire.\n\n" +
    "IMPORTANT : Reponds toujours en francais. Sois naturelle et humaine. Ne fais pas de liste a puces. Parle comme une vraie personne. Quand tu donnes un lien, mets-le sur une ligne separee pour qu'il soit cliquable.";

  var history = [];
  var isOpen = false;

  // Inject CSS
  var style = document.createElement('style');
  style.textContent = '#lx-chat-btn{position:fixed;bottom:20px;right:20px;width:80px;height:80px;border-radius:50%;background:#4A7BA8;border:3px solid #141413;cursor:pointer;z-index:9998;display:flex;align-items:center;justify-content:center;box-shadow:4px 4px 0 0 #141413;transition:all 0.3s;overflow:hidden}' +
    '#lx-chat-btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 0 #141413}' +
    '#lx-chat-btn svg{width:34px;height:34px;fill:white}' +
    '#lx-chat-btn.has-avatar{background:none;border:3px solid #4A7BA8}' +
    '#lx-chat-btn.has-avatar img{width:100%;height:100%;object-fit:cover;border-radius:50%}' +
    '#lx-chat-win{position:fixed;bottom:90px;right:20px;width:380px;height:520px;background:#FAF9F5;border:3px solid #141413;border-radius:8px;z-index:9999;display:none;flex-direction:column;box-shadow:8px 8px 0 0 #4A7BA8;overflow:hidden}' +
    '#lx-chat-hdr{background:#141413;color:#FAF9F5;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;font-family:Georgia,serif;font-size:0.95rem;font-weight:700}' +
    '#lx-chat-hdr button{background:none;border:none;color:#FAF9F5;font-size:1.5rem;cursor:pointer;line-height:1}' +
    '#lx-chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}' +
    '.lx-msg{max-width:85%;padding:10px 14px;border-radius:8px;font-size:0.88rem;line-height:1.5;font-family:Calibri,sans-serif}' +
    '.lx-msg-bot{align-self:flex-start;background:#fff;border:2px solid #ddd;color:#333}' +
    '.lx-msg-user{align-self:flex-end;background:#4A7BA8;color:#fff;border:2px solid #3a6a97}' +
    '.lx-msg-bot a{color:#4A7BA8;font-weight:700}' +
    '#lx-chat-input{display:flex;border-top:2px solid #141413;background:#fff}' +
    '#lx-chat-input input{flex:1;border:none;padding:12px;font-size:0.9rem;font-family:Calibri,sans-serif;outline:none}' +
    '#lx-chat-input button{background:#141413;color:#FAF9F5;border:none;padding:0 16px;cursor:pointer;font-weight:700;font-size:0.9rem;transition:background 0.2s}' +
    '#lx-chat-input button:hover{background:#4A7BA8}' +
    '.lx-typing{align-self:flex-start;color:#9FA8AC;font-size:0.82rem;font-style:italic;padding:4px 14px}' +
    '@media(max-width:500px){#lx-chat-win{width:100%;height:100%;bottom:0;right:0;border-radius:0;box-shadow:none}#lx-chat-btn{bottom:15px;right:15px;width:54px;height:54px}}';
  document.head.appendChild(style);

  // Inject button
  var btn = document.createElement('div');
  btn.id = 'lx-chat-btn';
  btn.className = 'has-avatar';
  btn.innerHTML = '<img src="/img/chatbot-avatar.jpg" alt="Assistant LEXVOX" width="80" height="80">';
  btn.title = 'Discuter avec notre assistante';
  document.body.appendChild(btn);

  // Inject chat window
  var win = document.createElement('div');
  win.id = 'lx-chat-win';
  win.innerHTML = '<div id="lx-chat-hdr"><div style="display:flex;align-items:center;gap:8px"><img src="/img/chatbot-avatar.jpg" alt="" style="width:32px;height:32px;border-radius:50%;border:2px solid #4A7BA8"><span>LEXVOX AVOCATS</span></div><button id="lx-chat-close">&times;</button></div>' +
    '<div id="lx-chat-msgs"></div>' +
    '<div id="lx-chat-input"><input type="text" placeholder="Votre message..." id="lx-chat-field" autocomplete="off"><button id="lx-chat-send">Envoyer</button></div>';
  document.body.appendChild(win);

  var msgs = document.getElementById('lx-chat-msgs');
  var field = document.getElementById('lx-chat-field');

  function addMsg(text, isUser) {
    var div = document.createElement('div');
    div.className = 'lx-msg ' + (isUser ? 'lx-msg-user' : 'lx-msg-bot');
    // Convert URLs to links
    div.innerHTML = text.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>').replace(/\n/g, '<br>');
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() {
    var t = document.createElement('div');
    t.className = 'lx-typing';
    t.id = 'lx-typing';
    t.textContent = 'En train de répondre...';
    msgs.appendChild(t);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function hideTyping() {
    var t = document.getElementById('lx-typing');
    if (t) t.remove();
  }

  function extractLeadData(text) {
    var data = JSON.parse(localStorage.getItem('lexvox_chatbot_lead') || '{}');
    // Email
    var email = text.match(/[\w.-]+@[\w.-]+\.\w+/);
    if (email) data.email = email[0];
    // Phone
    var phone = text.match(/(?:0[1-9][\s.-]?(?:\d{2}[\s.-]?){4}|\+33[\s.-]?\d[\s.-]?(?:\d{2}[\s.-]?){4})/);
    if (phone) data.phone = phone[0];
    data.lastMessage = text;
    data.page = window.location.pathname;
    data.date = new Date().toISOString();
    localStorage.setItem('lexvox_chatbot_lead', JSON.stringify(data));
  }

  async function sendMessage(userText) {
    addMsg(userText, true);
    extractLeadData(userText);

    history.push({ role: 'user', parts: [{ text: userText }] });

    showTyping();
    field.disabled = true;

    try {
      var messages = [{ role: 'system', content: SYSTEM_PROMPT }];
      for (var i = 0; i < history.length; i++) {
        messages.push({ role: history[i].role === 'model' ? 'assistant' : 'user', content: history[i].parts[0].text });
      }

      var resp = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'gpt-4o-mini', messages: messages, max_tokens: 500, temperature: 0.7 })
      });

      if (!resp.ok) {
        var errText = await resp.text();
        console.error('Chatbot API error:', resp.status, errText);
        throw new Error('API ' + resp.status);
      }
      var data = await resp.json();
      var reply = data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;

      if (reply) {
        history.push({ role: 'model', parts: [{ text: reply }] });
        hideTyping();
        addMsg(reply, false);
      } else {
        console.error('Chatbot: no reply in data', JSON.stringify(data).substring(0, 300));
        hideTyping();
        addMsg("Je suis désolé, je rencontre un problème technique. Appelez-nous au 04 90 54 58 10.", false);
      }
    } catch (e) {
      hideTyping();
      addMsg("Erreur de connexion. Appelez-nous directement au 04 90 54 58 10 ou écrivez à contact@avocat-lexvox.com", false);
    }

    field.disabled = false;
    field.focus();
  }

  // Open/close handlers
  btn.addEventListener('click', function() {
    win.style.display = 'flex';
    btn.style.display = 'none';
    isOpen = true;
    field.focus();
    // First message
    if (history.length === 0) {
      showTyping();
      setTimeout(function() {
        hideTyping();
        var greeting = "Bonjour ! Je suis l'assistant du cabinet LEXVOX AVOCATS. 👋\n\nComment puis-je vous aider ? Je peux vous orienter vers un rendez-vous avec nos avocats spécialisés.\n\nÊtes-vous déjà client du cabinet ?";
        history.push({ role: 'model', parts: [{ text: greeting }] });
        addMsg(greeting, false);
      }, 800);
    }
  });

  document.getElementById('lx-chat-close').addEventListener('click', function() {
    win.style.display = 'none';
    btn.style.display = 'flex';
    isOpen = false;
  });

  // Send handlers
  document.getElementById('lx-chat-send').addEventListener('click', function() {
    var text = field.value.trim();
    if (text) { field.value = ''; sendMessage(text); }
  });

  field.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      var text = field.value.trim();
      if (text) { field.value = ''; sendMessage(text); }
    }
  });
})();
