(function(){'use strict';var API_URL='/api/chat';var LEAD_URL='/api/lead';var CAL_URL='https://cal.com/patrice-humbert-4hvxey/30min';var SYSTEM_PROMPT="Tu es l'assistante virtuelle du cabinet d'avocats LEXVOX AVOCATS. Tu t'appelles Sophia.\n\n"+
"REGLES ABSOLUES :\n"+
"1. Tu ne donnes JAMAIS de conseil juridique. Tu n'es pas avocate.\n"+
"2. Tu orientes vers un rendez-vous GRATUIT de 30 minutes avec un avocat du cabinet.\n"+
"3. Tu es empathique, chaleureuse et rassurante avec les victimes.\n"+
"4. Tu reponds d'abord a 1 ou 2 questions de la personne pour comprendre sa situation AVANT de demander ses coordonnees. NE DEMANDE PAS les coordonnees immediatement.\n"+
"5. Apres avoir compris la situation, propose naturellement un RDV GRATUIT de 30 minutes et collecte : prenom + nom, telephone, email.\n"+
"6. Bureaux et avocats :\n"+
"   - Salon-de-Provence → Me Patrice HUMBERT (RDV en ligne disponible)\n"+
"   - Marignane → Me Patrice HUMBERT (RDV en ligne disponible)\n"+
"   - Aix-en-Provence → Me Patrice HUMBERT (RDV via secretariat uniquement)\n"+
"   - Arles → Me Cedrine RAYBAUD (RDV via secretariat uniquement)\n"+
"   Les deux avocats peuvent intervenir dans tous les domaines.\n"+
"7. PRISE DE RDV selon le bureau :\n"+
"   - Si la personne souhaite un RDV a Salon-de-Provence ou Marignane : collecte prenom+nom+telephone+email puis dis 'LEAD_COMPLET' (la plateforme de reservation en ligne sera proposee automatiquement).\n"+
"   - Si la personne souhaite un RDV a Aix-en-Provence ou Arles (ou ne precise pas) : collecte prenom+nom+telephone+email puis dis 'LEAD_COMPLET_SECRETARIAT' (le secretariat les rappellera).\n"+
"8. Distingue nouveau client (→ RDV gratuit) vs client existant (→ noter infos + rappel avocat).\n"+
"9. Sois concise (2-3 phrases max par reponse).\n"+
"10. Le cabinet defend EXCLUSIVEMENT les victimes, JAMAIS les assureurs.\n"+
"11. La premiere consultation est GRATUITE 30 min.\n"+
"12. Contact secretariat : 04 90 54 58 10 / contact@avocat-lexvox.com\n"+
"13. Si la personne prefere appeler directement : 04 90 54 58 10\n"+
"14. INTERDIT ABSOLU : ne jamais mentionner ni donner le lien consultation.avocat.fr — ni aucun autre lien externe payant. Pour la prise de RDV en ligne, UNIQUEMENT cal.com (Salon/Marignane) ou le secretariat 04 90 54 58 10 (Aix/Arles).\n\n"+
"Domaines : dommage corporel, accident de la route, erreur medicale, infection nosocomiale, "+
"accident du travail, agression, divorce, droit de la famille, violences conjugales, permis de conduire.\n\n"+
"IMPORTANT : Reponds toujours en francais. Sois naturelle et humaine. Ne fais pas de liste a puces. Parle comme une vraie personne.";var history=[];var isOpen=false;var leadSent=false;var style=document.createElement('style');style.textContent='#lx-chat-btn{position:fixed;bottom:20px;right:20px;width:80px;height:80px;border-radius:50%;background:#4A7BA8;border:3px solid #141413;cursor:pointer;z-index:9998;display:flex;align-items:center;justify-content:center;box-shadow:4px 4px 0 0 #141413;transition:all 0.3s;overflow:hidden}'+
'#lx-chat-btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 0 #141413}'+
'#lx-chat-btn{animation:lx-bounce 2s ease-in-out infinite}'+
'@keyframes lx-bounce{0%,100%{transform:translateY(0)}25%{transform:translateY(-12px)}50%{transform:translateY(0)}75%{transform:translateY(-6px)}}'+
'#lx-chat-btn:hover{animation:none;transform:translate(-2px,-2px)}'+
'#lx-chat-bubble{position:fixed;bottom:105px;right:20px;background:#fff;border:2px solid #4A7BA8;border-radius:16px 16px 4px 16px;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#141413;z-index:9997;box-shadow:3px 3px 0 0 #141413;animation:lx-bubble-pop 0.4s ease-out;font-family:Calibri,sans-serif}'+
'#lx-chat-bubble::after{content:"";position:absolute;bottom:-10px;right:15px;width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;border-top:10px solid #fff}'+
'#lx-chat-bubble::before{content:"";position:absolute;bottom:-13px;right:14px;width:0;height:0;border-left:11px solid transparent;border-right:11px solid transparent;border-top:11px solid #4A7BA8}'+
'@keyframes lx-bubble-pop{0%{transform:scale(0);opacity:0}50%{transform:scale(1.1)}100%{transform:scale(1);opacity:1}}'+
'#lx-chat-btn svg{width:34px;height:34px;fill:white}'+
'#lx-chat-btn.has-avatar{background:none;border:3px solid #4A7BA8}'+
'#lx-chat-btn.has-avatar img{width:100%;height:100%;object-fit:cover;border-radius:50%}'+
'#lx-chat-win{position:fixed;bottom:90px;right:20px;width:380px;height:520px;background:#FAF9F5;border:3px solid #141413;border-radius:8px;z-index:9999;display:none;flex-direction:column;box-shadow:8px 8px 0 0 #4A7BA8;overflow:hidden}'+
'#lx-chat-hdr{background:#141413;color:#FAF9F5;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;font-family:Georgia,serif;font-size:0.95rem;font-weight:700}'+
'#lx-chat-hdr button{background:none;border:none;color:#FAF9F5;font-size:1.5rem;cursor:pointer;line-height:1}'+
'#lx-chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}'+
'.lx-msg{max-width:85%;padding:10px 14px;border-radius:8px;font-size:0.88rem;line-height:1.5;font-family:Calibri,sans-serif}'+
'.lx-msg-bot{align-self:flex-start;background:#fff;border:2px solid #ddd;color:#333}'+
'.lx-msg-user{align-self:flex-end;background:#4A7BA8;color:#fff;border:2px solid #3a6a97}'+
'.lx-msg-bot a{color:#4A7BA8;font-weight:700}'+
'#lx-chat-input{display:flex;border-top:2px solid #141413;background:#fff}'+
'#lx-chat-input input{flex:1;border:none;padding:12px;font-size:0.9rem;font-family:Calibri,sans-serif;outline:none}'+
'#lx-chat-input button{background:#141413;color:#FAF9F5;border:none;padding:0 16px;cursor:pointer;font-weight:700;font-size:0.9rem;transition:background 0.2s}'+
'#lx-chat-input button:hover{background:#4A7BA8}'+
'.lx-typing{align-self:flex-start;color:#9FA8AC;font-size:0.82rem;font-style:italic;padding:4px 14px}'+
'.lx-rdv-btn{display:inline-block;margin-top:8px;padding:8px 16px;background:#4A7BA8;color:#fff;border-radius:6px;font-weight:700;font-size:0.82rem;text-decoration:none;border:2px solid #3a6a97}'+
'.lx-rdv-btn:hover{background:#3a6a97}'+
'@media(max-width:500px){#lx-chat-win{width:100%;height:100%;bottom:0;right:0;border-radius:0;box-shadow:none}#lx-chat-btn{bottom:15px;right:15px;width:54px;height:54px}}';document.head.appendChild(style);var btn=document.createElement('div');btn.id='lx-chat-btn';btn.className='has-avatar';btn.innerHTML='<img src="/img/chatbot-avatar.jpg" alt="Assistant LEXVOX" width="80" height="80">';btn.title='Discuter avec notre assistante';document.body.appendChild(btn);setTimeout(function(){if(!isOpen){var bubble=document.createElement('div');bubble.id='lx-chat-bubble';bubble.innerHTML='💬 À votre service !';document.body.appendChild(bubble);setTimeout(function(){if(bubble.parentNode)bubble.parentNode.removeChild(bubble);},6000);}},3000);var win=document.createElement('div');win.id='lx-chat-win';win.innerHTML='<div id="lx-chat-hdr"><div style="display:flex;align-items:center;gap:8px"><img src="/img/chatbot-avatar.jpg" alt="" style="width:32px;height:32px;border-radius:50%;border:2px solid #4A7BA8"><span>LEXVOX AVOCATS — Sophia</span></div><button id="lx-chat-close">&times;</button></div>'+
'<div id="lx-chat-msgs"></div>'+
'<div id="lx-chat-input"><input type="text" placeholder="Votre message..." id="lx-chat-field" autocomplete="off"><button id="lx-chat-send">Envoyer</button></div>';document.body.appendChild(win);var msgs=document.getElementById('lx-chat-msgs');var field=document.getElementById('lx-chat-field');function addMsg(text,isUser){var div=document.createElement('div');div.className='lx-msg '+(isUser?'lx-msg-user':'lx-msg-bot');div.innerHTML=text.replace(/(https?:\/\/[^\s<]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>').replace(/\n/g,'<br>');msgs.appendChild(div);msgs.scrollTop=msgs.scrollHeight;}
function showTyping(){var t=document.createElement('div');t.className='lx-typing';t.id='lx-typing';t.textContent='En train de répondre...';msgs.appendChild(t);msgs.scrollTop=msgs.scrollHeight;}
function hideTyping(){var t=document.getElementById('lx-typing');if(t)t.remove();}
function extractLeadData(text){var data=JSON.parse(localStorage.getItem('lexvox_chatbot_lead')||'{}');var email=text.match(/[\w.-]+@[\w.-]+\.\w+/);if(email)data.email=email[0];var phone=text.match(/(?:0[1-9][\s.-]?(?:\d{2}[\s.-]?){4}|\+33[\s.-]?\d[\s.-]?(?:\d{2}[\s.-]?){4})/);if(phone)data.phone=phone[0];var name=text.match(/\b([A-ZÉÈÀÙÂÊÔÎÛ][a-zéèàùâêôîûç]+)\s+([A-ZÉÈÀÙÂÊÔÎÛ][a-zéèàùâêôîûç]+)\b/);if(name&&!data.name)data.name=name[0];data.lastMessage=text;data.page=window.location.pathname;data.date=new Date().toISOString();localStorage.setItem('lexvox_chatbot_lead',JSON.stringify(data));return data;}
function getConversationText(){var lines=[];for(var i=0;i<history.length;i++){var role=history[i].role==='model'?'Sophia':'Visiteur';lines.push(role+' : '+history[i].parts[0].text);}
return lines.join('\n\n');}
async function sendLeadEmail(lead){if(leadSent)return;leadSent=true;try{await fetch(LEAD_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lead:lead,conversation:getConversationText(),page:window.location.href,userAgent:navigator.userAgent})});}catch(e){console.error('Lead send error:',e);}}
async function sendMessage(userText){addMsg(userText,true);var lead=extractLeadData(userText);history.push({role:'user',parts:[{text:userText}]});showTyping();field.disabled=true;try{var messages=[{role:'system',content:SYSTEM_PROMPT}];for(var i=0;i<history.length;i++){messages.push({role:history[i].role==='model'?'assistant':'user',content:history[i].parts[0].text});}
var resp=await fetch(API_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:'gpt-4o-mini',messages:messages,max_tokens:500,temperature:0.7})});if(!resp.ok)throw new Error('API '+resp.status);var data=await resp.json();var reply=data.choices&&data.choices[0]&&data.choices[0].message&&data.choices[0].message.content;if(reply){history.push({role:'model',parts:[{text:reply}]});hideTyping();if(reply.indexOf('LEAD_COMPLET_SECRETARIAT')!==-1){sendLeadEmail(lead);reply=reply.replace('LEAD_COMPLET_SECRETARIAT','').trim();if(!reply){reply="Parfait, j'ai bien noté vos coordonnées. Notre secrétariat vous rappellera dans les 24 heures pour confirmer votre rendez-vous.";}
addMsg(reply,false);var secDiv=document.createElement('div');secDiv.className='lx-msg lx-msg-bot';secDiv.innerHTML='Vous pouvez aussi contacter directement notre secrétariat :<br>'+
'<a href="tel:+33490545810" class="lx-rdv-btn" style="margin-right:8px">📞 04 90 54 58 10</a>'+
'<a href="mailto:contact@avocat-lexvox.com" class="lx-rdv-btn" style="background:#141413;border-color:#141413">✉ Par email</a>';msgs.appendChild(secDiv);msgs.scrollTop=msgs.scrollHeight;}else if(reply.indexOf('LEAD_COMPLET')!==-1){sendLeadEmail(lead);reply=reply.replace('LEAD_COMPLET','').trim();if(!reply){reply="Parfait, j'ai bien noté vos coordonnées. Vous pouvez réserver directement votre créneau de 30 minutes en ligne, ou notre équipe vous confirmera par téléphone.";}
addMsg(reply,false);var calDiv=document.createElement('div');calDiv.className='lx-msg lx-msg-bot';calDiv.innerHTML='Réservez directement votre créneau de 30 minutes :<br><a href="'+CAL_URL+'" target="_blank" rel="noopener" class="lx-rdv-btn">📅 Réserver en ligne</a>';msgs.appendChild(calDiv);msgs.scrollTop=msgs.scrollHeight;}else{addMsg(reply,false);}}else{hideTyping();addMsg("Je suis désolée, je rencontre un problème technique. Appelez-nous au 04 90 54 58 10.",false);}}catch(e){hideTyping();addMsg("Erreur de connexion. Appelez-nous directement au 04 90 54 58 10 ou écrivez à contact@avocat-lexvox.com",false);}
field.disabled=false;field.focus();}
btn.addEventListener('click',function(){win.style.display='flex';btn.style.display='none';isOpen=true;var bub=document.getElementById('lx-chat-bubble');if(bub)bub.parentNode.removeChild(bub);field.focus();if(history.length===0){showTyping();setTimeout(function(){hideTyping();var greeting="Bonjour ! Je suis Sophia, l'assistante du cabinet LEXVOX AVOCATS. 👋\n\nJe suis là pour vous orienter et organiser un rendez-vous gratuit de 30 minutes avec nos avocats spécialisés en dommage corporel.\n\nComment puis-je vous aider aujourd'hui ?";history.push({role:'model',parts:[{text:greeting}]});addMsg(greeting,false);},800);}});document.getElementById('lx-chat-close').addEventListener('click',function(){win.style.display='none';btn.style.display='flex';isOpen=false;if(history.length>=3&&!leadSent){var lead=JSON.parse(localStorage.getItem('lexvox_chatbot_lead')||'{}');sendLeadEmail(lead);}});document.getElementById('lx-chat-send').addEventListener('click',function(){var text=field.value.trim();if(text){field.value='';sendMessage(text);}});field.addEventListener('keydown',function(e){if(e.key==='Enter'){var text=field.value.trim();if(text){field.value='';sendMessage(text);}}});window.addEventListener('beforeunload',function(){if(history.length>=3&&!leadSent){var lead=JSON.parse(localStorage.getItem('lexvox_chatbot_lead')||'{}');navigator.sendBeacon(LEAD_URL,JSON.stringify({lead:lead,conversation:getConversationText(),page:window.location.href}));}});})();