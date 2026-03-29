/**
 * LEXVOX AVOCATS — Simulateur d'indemnisation
 * Basé sur les fourchettes BASSES du référentiel Mornet
 * Méthode LexVictime : +15% à +100% selon les dossiers
 */

// Valeur du point DFP par tranche d'âge (fourchette BASSE Mornet)
var DFP_POINTS = [
  { min: 0, max: 10, val: 2800 },
  { min: 11, max: 20, val: 2600 },
  { min: 21, max: 30, val: 2400 },
  { min: 31, max: 40, val: 2200 },
  { min: 41, max: 50, val: 1900 },
  { min: 51, max: 60, val: 1600 },
  { min: 61, max: 70, val: 1300 },
  { min: 71, max: 80, val: 1000 },
  { min: 81, max: 120, val: 800 }
];

// Souffrances endurées (fourchette BASSE)
var SE_MONTANTS = [0, 1500, 3000, 6000, 10000, 20000, 35000, 50000];

// Préjudice esthétique permanent (fourchette BASSE)
var PE_MONTANTS = [0, 1000, 2000, 4000, 8000, 15000, 25000, 40000];

// DFT par jour (base 100% = 25€/jour)
var DFT_JOUR = 25;

function getPointDFP(age) {
  for (var i = 0; i < DFP_POINTS.length; i++) {
    if (age >= DFP_POINTS[i].min && age <= DFP_POINTS[i].max) {
      return DFP_POINTS[i].val;
    }
  }
  return 800;
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

  // Calculs
  var pointDFP = getPointDFP(age);
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
