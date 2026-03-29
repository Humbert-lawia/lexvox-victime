/**
 * LEXVOX AVOCATS — Évaluateur complet de préjudices (Nomenclature Dintilhac)
 * Données: Référentiel Mornet 2025 (fourchettes BASSES)
 * Méthode LexVictime: +15% à +100% selon dossiers
 */

// Table DFP Mornet 2025 — valeur du point
var DFP_T = [
  [2310,2670,3025,3380,3740,4100,4455,4810,5170,5530,5885,6240,6600,6955,7315,7670,8030,8385,8745,9020],
  [2150,2475,2800,3135,3465,3795,4125,4455,4785,5115,5445,5775,6105,6435,6765,7095,7425,7755,8085,8415],
  [1960,2255,2550,2850,3145,3445,3740,4035,4335,4630,4930,5225,5520,5820,6115,6415,6710,7005,7305,7600],
  [1770,2035,2300,2560,2830,3090,3355,3620,3885,4150,4410,4675,4940,5205,5470,5730,5995,6260,6525,6785],
  [1580,1800,2025,2245,2465,2685,2905,3125,3345,3565,3785,4005,4225,4445,4665,4885,5105,5325,5545,5765],
  [1400,1560,1730,1890,2060,2220,2390,2550,2715,2880,3045,3210,3375,3540,3705,3870,4035,4200,4365,4530],
  [1210,1320,1430,1540,1650,1760,1870,1980,2090,2200,2310,2420,2530,2640,2750,2860,2970,3080,3190,3300],
  [1050,1130,1210,1290,1375,1455,1540,1620,1705,1790,1870,1950,2035,2115,2200,2280,2365,2445,2530,2610],
  [880,935,990,1045,1100,1155,1210,1265,1320,1375,1430,1485,1540,1595,1650,1705,1760,1815,1870,1925]
];

// SE et PE — Mornet 2025 fourchette basse
var SE_LOW = [0, 2000, 2000, 4000, 8000, 20000, 35000, 50000];
var PE_LOW = [0, 2000, 2000, 4000, 8000, 20000, 35000, 50000];

// Préjudice d'affection — fourchettes basses
var PA_PROCHES = { conjoint: 25000, enfant: 20000, parent: 20000, fratrie: 8000, grandparent: 5000 };

function getAgeIdx(a) { return a<=10?0:a<=20?1:a<=30?2:a<=40?3:a<=50?4:a<=60?5:a<=70?6:a<=80?7:8; }
function getDfpIdx(d) { return Math.min(Math.max(Math.floor((d-1)/5),0),19); }
function fmt(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,' '); }

function evaluerPrejudices() {
  var age = parseInt(document.getElementById('ev-age').value) || 35;
  var results = [];
  var total = 0;

  // 1. DSA
  var dsa = parseFloat(document.getElementById('ev-dsa').value) || 0;
  if (dsa > 0) { results.push({poste:'Dépenses de Santé Actuelles (DSA)', montant:dsa}); total += dsa; }

  // 2. FD
  var fd = parseFloat(document.getElementById('ev-fd').value) || 0;
  if (fd > 0) { results.push({poste:'Frais Divers (FD)', montant:fd}); total += fd; }

  // 3. PGPA
  var pgpa_sal = parseFloat(document.getElementById('ev-pgpa-sal').value) || 0;
  var pgpa_mois = parseFloat(document.getElementById('ev-pgpa-mois').value) || 0;
  var pgpa = pgpa_sal * pgpa_mois;
  if (pgpa > 0) { results.push({poste:'Pertes de Gains Prof. Actuels (PGPA)', montant:pgpa, detail:fmt(pgpa_sal)+' €/mois × '+pgpa_mois+' mois'}); total += pgpa; }

  // 4. DSF
  var dsf = parseFloat(document.getElementById('ev-dsf').value) || 0;
  if (dsf > 0) { results.push({poste:'Dépenses de Santé Futures (DSF)', montant:dsf}); total += dsf; }

  // 5. FLA
  var fla = parseFloat(document.getElementById('ev-fla').value) || 0;
  if (fla > 0) { results.push({poste:'Frais de Logement Adapté (FLA)', montant:fla}); total += fla; }

  // 6. FVA
  var fva = parseFloat(document.getElementById('ev-fva').value) || 0;
  if (fva > 0) { results.push({poste:'Frais de Véhicule Adapté (FVA)', montant:fva}); total += fva; }

  // 7. ATP
  var atp_h = parseFloat(document.getElementById('ev-atp-h').value) || 0;
  var atp_cout = parseFloat(document.getElementById('ev-atp-cout').value) || 18;
  var atp_j = parseFloat(document.getElementById('ev-atp-j').value) || 0;
  var atp = atp_h * atp_cout * atp_j;
  if (atp > 0) { results.push({poste:'Assistance Tierce Personne (ATP)', montant:atp, detail:atp_h+'h/j × '+fmt(atp_cout)+' €/h × '+atp_j+' jours'}); total += atp; }

  // 8. PGPF
  var pgpf_perte = parseFloat(document.getElementById('ev-pgpf-perte').value) || 0;
  var pgpf_euro = parseFloat(document.getElementById('ev-pgpf-euro').value) || 0;
  var pgpf = pgpf_perte * 12 * pgpf_euro;
  if (pgpf > 0) { results.push({poste:'Pertes de Gains Prof. Futurs (PGPF)', montant:pgpf, detail:fmt(pgpf_perte)+' €/mois × 12 × '+pgpf_euro+' (euro rente)'}); total += pgpf; }

  // 9. IP
  var ip = parseFloat(document.getElementById('ev-ip').value) || 0;
  if (ip > 0) { results.push({poste:'Incidence Professionnelle (IP)', montant:ip}); total += ip; }

  // 10. DFT
  var dft_j = parseFloat(document.getElementById('ev-dft-j').value) || 0;
  var dft_classe = parseFloat(document.getElementById('ev-dft-classe').value) || 25;
  var dft = dft_j * dft_classe;
  if (dft > 0) { results.push({poste:'Déficit Fonctionnel Temporaire (DFT)', montant:dft, detail:dft_j+' jours × '+dft_classe+' €/jour'}); total += dft; }

  // 11. SE
  var se = parseInt(document.getElementById('ev-se').value) || 0;
  var se_m = SE_LOW[se] || 0;
  if (se_m > 0) { results.push({poste:'Souffrances Endurées (SE) '+se+'/7', montant:se_m}); total += se_m; }

  // 12. DFP
  var dfp = parseInt(document.getElementById('ev-dfp').value) || 0;
  if (dfp > 0) {
    var pt = DFP_T[getAgeIdx(age)][getDfpIdx(dfp)];
    var dfp_m = dfp * pt;
    results.push({poste:'Déficit Fonctionnel Permanent (DFP) '+dfp+'%', montant:dfp_m, detail:dfp+'% × '+fmt(pt)+' €/point (Mornet 2025, âge '+age+')'});
    total += dfp_m;
  }

  // 13. PA
  var pa = parseFloat(document.getElementById('ev-pa').value) || 0;
  if (pa > 0) { results.push({poste:"Préjudice d'Agrément (PA)", montant:pa}); total += pa; }

  // 14. PE
  var pe = parseInt(document.getElementById('ev-pe').value) || 0;
  var pe_m = PE_LOW[pe] || 0;
  if (pe_m > 0) { results.push({poste:'Préjudice Esthétique Permanent (PE) '+pe+'/7', montant:pe_m}); total += pe_m; }

  // 15. PS
  var ps = parseFloat(document.getElementById('ev-ps').value) || 0;
  if (ps > 0) { results.push({poste:'Préjudice Sexuel (PS)', montant:ps}); total += ps; }

  // 16. PEP
  var pep = parseFloat(document.getElementById('ev-pep').value) || 0;
  if (pep > 0) { results.push({poste:"Préjudice d'Établissement (PEP)", montant:pep}); total += pep; }

  // 17. PA proches
  var pa_type = document.getElementById('ev-pa-type').value;
  var pa_nb = parseInt(document.getElementById('ev-pa-nb').value) || 0;
  var pa_p = (PA_PROCHES[pa_type] || 0) * pa_nb;
  if (pa_p > 0) { results.push({poste:"Préjudice d'Affection (proches)", montant:pa_p, detail:pa_nb+' × '+fmt(PA_PROCHES[pa_type])+' €'}); total += pa_p; }

  // 18. PEco
  var peco = parseFloat(document.getElementById('ev-peco').value) || 0;
  if (peco > 0) { results.push({poste:'Préjudice Économique des proches', montant:peco}); total += peco; }

  // Affichage
  var html = '<table style="width:100%;border-collapse:collapse;">';
  html += '<tr style="border-bottom:1px solid #444;"><th style="text-align:left;padding:8px 0;color:#9FA8AC;font-size:0.85rem;">Poste Dintilhac</th><th style="text-align:right;padding:8px 0;color:#9FA8AC;font-size:0.85rem;">Montant min.</th></tr>';
  for (var i = 0; i < results.length; i++) {
    var r = results[i];
    html += '<tr style="border-bottom:1px solid #333;">';
    html += '<td style="padding:8px 0;font-size:0.88rem;">' + r.poste;
    if (r.detail) html += '<br><span style="font-size:0.75rem;color:#9FA8AC;">' + r.detail + '</span>';
    html += '</td>';
    html += '<td style="text-align:right;padding:8px 0;color:#B89C58;font-weight:700;font-size:1rem;">' + fmt(r.montant) + ' €</td>';
    html += '</tr>';
  }
  html += '</table>';

  if (results.length === 0) {
    html = '<p style="color:#9FA8AC;text-align:center;">Aucun poste renseigné. Complétez les champs ci-dessus.</p>';
  }

  document.getElementById('ev-detail').innerHTML = html;
  document.getElementById('ev-total').textContent = fmt(total);
  document.getElementById('ev-total-lv').textContent = fmt(Math.round(total * 1.15)) + ' € à ' + fmt(Math.round(total * 2)) + ' €';
  document.getElementById('ev-results').style.display = 'block';
  document.getElementById('ev-results').scrollIntoView({ behavior: 'smooth', block: 'center' });
}
