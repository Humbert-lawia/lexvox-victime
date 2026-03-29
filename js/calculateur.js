/**
 * LEXVOX AVOCATS — Simulateur d'indemnisation
 * Basé sur les fourchettes BASSES du référentiel Mornet
 * Méthode LexVictime : +15% à +100% selon les dossiers
 */

// Table DFP Mornet 2025 (Référentiel indicatif cours d'appel)
// Format: DFP_TABLE[tranche_age][tranche_dfp] = valeur du point
// Tranches age: 0=0-10, 1=11-20, 2=21-30, 3=31-40, 4=41-50, 5=51-60, 6=61-70, 7=71-80, 8=81+
// Tranches DFP: 0=1-5%, 1=6-10%, 2=11-15%, ..., 19=96%+
var DFP_TABLE = [
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

function getPointDFP_Mornet(age, dfpPct) {
  // Tranche d'age
  var ageIdx;
  if (age <= 10) ageIdx = 0;
  else if (age <= 20) ageIdx = 1;
  else if (age <= 30) ageIdx = 2;
  else if (age <= 40) ageIdx = 3;
  else if (age <= 50) ageIdx = 4;
  else if (age <= 60) ageIdx = 5;
  else if (age <= 70) ageIdx = 6;
  else if (age <= 80) ageIdx = 7;
  else ageIdx = 8;
  // Tranche DFP (par tranches de 5%)
  var dfpIdx = Math.min(Math.floor((dfpPct - 1) / 5), 19);
  if (dfpIdx < 0) dfpIdx = 0;
  return DFP_TABLE[ageIdx][dfpIdx];
}

// Souffrances endurées — Mornet 2025 (fourchette BASSE)
var SE_MONTANTS = [0, 2000, 2000, 4000, 8000, 20000, 35000, 50000];

// Préjudice esthétique permanent — Mornet 2025 (identique SE)
var PE_MONTANTS = [0, 2000, 2000, 4000, 8000, 20000, 35000, 50000];

// DFT par jour — Mornet 2025 (750-1000€/mois soit 25-33€/jour, on prend 25€)
var DFT_JOUR = 25;

function getPointDFP(age, dfpPct) {
  return getPointDFP_Mornet(age, dfpPct || 5);
}

function formatMontant(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// Slider label update
var slider = document.getElementById('calc-dfp');
var sliderVal = document.getElementById('calc-dfp-val');
if (slider && sliderVal) {
  slider.addEventListener('input', function() {
    sliderVal.textContent = this.value + '%';
  });
}

function calculerIndemnisation() {
  var age = parseInt(document.getElementById('calc-age').value) || 35;
  var dfp = parseInt(document.getElementById('calc-dfp').value) || 0;
  var se = parseInt(document.getElementById('calc-se').value) || 0;
  var pe = parseInt(document.getElementById('calc-pe').value) || 0;
  var dftJours = parseInt(document.getElementById('calc-dft-jours').value) || 0;

  // Calculs — Table Mornet 2025
  var pointDFP = getPointDFP(age, dfp);
  var montantDFP = dfp * pointDFP;
  var montantSE = SE_MONTANTS[se] || 0;
  var montantPE = PE_MONTANTS[pe] || 0;
  var montantDFT = dftJours * DFT_JOUR;
  var total = montantDFP + montantSE + montantPE + montantDFT;

  // Affichage détaillé
  var detail = document.getElementById('calc-detail');
  var html = '<table style="width:100%;border-collapse:collapse;margin-bottom:1rem;">';
  html += '<tr style="border-bottom:1px solid #333;"><th style="text-align:left;padding:0.5rem 0;color:#9FA8AC;">Poste de préjudice</th><th style="text-align:right;padding:0.5rem 0;color:#9FA8AC;">Montant minimum</th></tr>';

  if (montantDFP > 0) {
    html += '<tr style="border-bottom:1px solid #222;"><td style="padding:0.5rem 0;">Déficit Fonctionnel Permanent (' + dfp + '% × ' + formatMontant(pointDFP) + ' €/pt)</td><td style="text-align:right;padding:0.5rem 0;color:#B89C58;font-weight:700;">' + formatMontant(montantDFP) + ' €</td></tr>';
  }
  if (montantSE > 0) {
    html += '<tr style="border-bottom:1px solid #222;"><td style="padding:0.5rem 0;">Souffrances endurées (' + se + '/7)</td><td style="text-align:right;padding:0.5rem 0;color:#B89C58;font-weight:700;">' + formatMontant(montantSE) + ' €</td></tr>';
  }
  if (montantPE > 0) {
    html += '<tr style="border-bottom:1px solid #222;"><td style="padding:0.5rem 0;">Préjudice esthétique permanent (' + pe + '/7)</td><td style="text-align:right;padding:0.5rem 0;color:#B89C58;font-weight:700;">' + formatMontant(montantPE) + ' €</td></tr>';
  }
  if (montantDFT > 0) {
    html += '<tr style="border-bottom:1px solid #222;"><td style="padding:0.5rem 0;">Déficit Fonctionnel Temporaire (' + dftJours + ' jours)</td><td style="text-align:right;padding:0.5rem 0;color:#B89C58;font-weight:700;">' + formatMontant(montantDFT) + ' €</td></tr>';
  }
  html += '</table>';
  html += '<p style="font-size:0.8rem;color:#9FA8AC;margin-top:0.5rem;">⚠️ Estimation basée sur les fourchettes <strong>basses</strong> du référentiel Mornet. Postes non inclus : préjudice d\'agrément, préjudice sexuel, PGPF, tierce personne, frais futurs, et autres postes Dintilhac.</p>';

  detail.innerHTML = html;
  document.getElementById('calc-total').textContent = formatMontant(total);
  document.getElementById('calc-results').style.display = 'block';

  // Scroll to results
  document.getElementById('calc-results').scrollIntoView({ behavior: 'smooth', block: 'center' });
}
