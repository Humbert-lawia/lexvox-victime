/**
 * LEXVOX AVOCATS — Chatbot Gemini Flash
 * Assistant virtuel pour capture leads et orientation RDV
 * JAMAIS de conseil juridique
 */
(function() {
  'use strict';

  var API_KEY = 'AIzaSyDED7nDlN3-MwkRbLDB47e5lHA_Cyg5U0s';
  var API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + API_KEY;

  var SYSTEM_PROMPT = "Tu es l'assistant virtuel du cabinet d'avocats LEXVOX AVOCATS. Regles ABSOLUES :\n\n" +
    "1. Tu ne donnes JAMAIS de conseil juridique. Tu n'es pas avocat.\n" +
    "2. Tu orientes TOUJOURS vers un rendez-vous avec un avocat du cabinet.\n" +
    "3. Tu es empathique et rassurant avec les victimes.\n" +
    "4. Tu collectes : prenom, nom, telephone, email, nature du probleme.\n" +
    "5. Tu proposes un RDV selon le lieu prefere :\n" +
    "   - Arles → Me Cedrine RAYBAUD (droit famille, divorce, violences)\n" +
    "   - Salon-de-Provence → Me Patrice HUMBERT (dommage corporel, erreur medicale)\n" +
    "   - Marignane → Me Patrice HUMBERT (dommage corporel, erreur medicale)\n" +
    "   Les deux avocats peuvent intervenir dans tous les domaines.\n" +
    "6. Tu distingues nouveau client (→ proposer RDV) vs client existant (→ noter infos + rappel avocat).\n" +
    "7. Tu es concis (3-5 minutes max de conversation).\n" +
    "8. Le cabinet defend EXCLUSIVEMENT les victimes, JAMAIS les assureurs.\n" +
    "9. Premiere consultation gratuite 30 min.\n" +
    "10. Contact : 04 90 54 58 10 / contact@avocat-lexvox.com\n" +
    "11. Lien RDV : https://consultation.avocat.fr/avocat-marignane/patrice-humbert-12417.html\n\n" +
    "Domaines : dommage corporel, accident de la route (loi Badinter), erreur medicale, infection nosocomiale, " +
    "accident du travail (faute inexcusable), agression (CIVI), divorce, droit de la famille, violences conjugales, permis de conduire.\n\n" +
    "Commence par te presenter brievement et demander comment tu peux aider.";

  var history = [];
  var isOpen = false;

  // Inject CSS
  var style = document.createElement('style');
  style.textContent = '#lx-chat-btn{position:fixed;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;background:#4A7BA8;border:3px solid #141413;cursor:pointer;z-index:9998;display:flex;align-items:center;justify-content:center;box-shadow:4px 4px 0 0 #141413;transition:all 0.3s}' +
    '#lx-chat-btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 0 #141413}' +
    '#lx-chat-btn svg{width:28px;height:28px;fill:white}' +
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
  btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';
  btn.title = 'Discuter avec notre assistant';
  document.body.appendChild(btn);

  // Inject chat window
  var win = document.createElement('div');
  win.id = 'lx-chat-win';
  win.innerHTML = '<div id="lx-chat-hdr"><span>LEXVOX AVOCATS</span><button id="lx-chat-close">&times;</button></div>' +
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
      var body = {
        system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: history
      };

      var resp = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      var data = await resp.json();
      var reply = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts[0] && data.candidates[0].content.parts[0].text;

      if (reply) {
        history.push({ role: 'model', parts: [{ text: reply }] });
        hideTyping();
        addMsg(reply, false);
      } else {
        hideTyping();
        addMsg("Je suis désolé, je rencontre un problème technique. Vous pouvez nous joindre directement au 04 90 54 58 10.", false);
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
