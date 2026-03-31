(function(){'use strict';if(sessionStorage.getItem('lexvox_popup_shown'))return;var DELAY=10000;var popupHTML='<div id="lexvox-popup-overlay" style="'+
'position:fixed;top:0;left:0;right:0;bottom:0;'+
'background:rgba(20,20,19,0.75);z-index:9999;'+
'display:flex;align-items:center;justify-content:center;'+
'opacity:0;transition:opacity 0.4s ease;padding:1rem;">'+
'<div id="lexvox-popup" style="'+
'background:#FAF9F5;border:3px solid #141413;border-radius:8px;'+
'max-width:480px;width:100%;padding:2.5rem;position:relative;'+
'box-shadow:8px 8px 0 0 #4A7BA8;transform:translateY(20px);'+
'transition:transform 0.4s ease;">'+
'<button id="lexvox-popup-close" style="'+
'position:absolute;top:0.8rem;right:1rem;background:none;border:none;'+
'font-size:1.8rem;cursor:pointer;color:#141413;font-family:Consolas,monospace;'+
'line-height:1;">&times;</button>'+
'<p style="font-size:0.8rem;text-transform:uppercase;letter-spacing:2px;'+
'color:#4A7BA8;font-weight:700;margin-bottom:0.5rem;">Guide gratuit</p>'+
'<h3 style="font-family:Georgia,serif;font-size:1.3rem;color:#141413;'+
'margin-bottom:0.5rem;line-height:1.3;">Les 7 erreurs fatales qui r\u00e9duisent votre indemnisation</h3>'+
'<p style="font-size:0.9rem;color:#666;margin-bottom:1.5rem;">'+
'T\u00e9l\u00e9chargez notre guide et prot\u00e9gez vos droits. Par Me Humbert, avocat sp\u00e9cialis\u00e9 depuis plus de 20 ans.</p>'+
'<form id="lexvox-popup-form">'+
'<input type="email" id="lexvox-email" placeholder="Votre email" required style="'+
'width:100%;padding:0.7rem;border:2px solid #141413;border-radius:4px;'+
'font-size:1rem;margin-bottom:0.8rem;box-sizing:border-box;font-family:Calibri,sans-serif;">'+
'<label style="display:flex;align-items:flex-start;gap:0.5rem;margin-bottom:1rem;cursor:pointer;font-size:0.8rem;line-height:1.4;color:#666;">'+
'<input type="checkbox" id="lexvox-rgpd" required style="margin-top:2px;min-width:16px;min-height:16px;">'+
'<span>J\'accepte de recevoir le guide et des informations utiles aux victimes par email. '+
'<a href="/politique-confidentialite" target="_blank" style="color:#4A7BA8;">RGPD</a>. D\u00e9sinscription possible \u00e0 tout moment.</span></label>'+
'<button type="submit" style="'+
'width:100%;padding:0.9rem;background:#141413;color:#FAF9F5;border:3px solid #141413;'+
'border-radius:4px;font-size:1rem;font-weight:700;cursor:pointer;'+
'font-family:Calibri,sans-serif;transition:all 0.2s;">'+
'Recevoir mon guide gratuit \u2192</button>'+
'</form>'+
'<p style="font-size:0.7rem;color:#999;margin-top:0.8rem;text-align:center;">'+
'SELARL LEXVOX AVOCATS \u2014 Responsable de traitement. Aucune cession \u00e0 des tiers.</p>'+
'</div></div>';function showPopup(){document.body.insertAdjacentHTML('beforeend',popupHTML);var overlay=document.getElementById('lexvox-popup-overlay');var popup=document.getElementById('lexvox-popup');var closeBtn=document.getElementById('lexvox-popup-close');var form=document.getElementById('lexvox-popup-form');requestAnimationFrame(function(){overlay.style.opacity='1';popup.style.transform='translateY(0)';});function closePopup(){overlay.style.opacity='0';popup.style.transform='translateY(20px)';setTimeout(function(){overlay.remove();},400);sessionStorage.setItem('lexvox_popup_shown','1');}
closeBtn.addEventListener('click',closePopup);overlay.addEventListener('click',function(e){if(e.target===overlay)closePopup();});document.addEventListener('keydown',function(e){if(e.key==='Escape')closePopup();});form.addEventListener('submit',function(e){e.preventDefault();var email=document.getElementById('lexvox-email').value;var rgpd=document.getElementById('lexvox-rgpd');if(!rgpd.checked){rgpd.style.outline='2px solid #C0392B';return;}
var lead={email:email,source:'popup_guide',rgpd_consent:true,rgpd_date:new Date().toISOString(),date:new Date().toISOString(),page:window.location.pathname};var leads=JSON.parse(localStorage.getItem('lexvox_leads')||'[]');leads.push(lead);localStorage.setItem('lexvox_leads',JSON.stringify(leads));var consents=JSON.parse(localStorage.getItem('lexvox_rgpd_consents')||'[]');consents.push({email:email,type:'guide',consent:true,date:new Date().toISOString()});localStorage.setItem('lexvox_rgpd_consents',JSON.stringify(consents));sessionStorage.setItem('lexvox_popup_shown','1');window.open('/guide-7-erreurs-indemnisation.pdf','_blank');closePopup();});var btn=form.querySelector('button[type="submit"]');btn.addEventListener('mouseenter',function(){btn.style.background='#4A7BA8';btn.style.borderColor='#4A7BA8';btn.style.transform='translate(-2px,-2px)';btn.style.boxShadow='6px 6px 0 0 #141413';});btn.addEventListener('mouseleave',function(){btn.style.background='#141413';btn.style.borderColor='#141413';btn.style.transform='none';btn.style.boxShadow='none';});}
setTimeout(showPopup,DELAY);})();