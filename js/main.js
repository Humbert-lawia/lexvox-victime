/* ═══ LEXVOX-VICTIME.FR — JavaScript principal ═══ */
/* Menu mobile, FAQ accordion, scroll nav */

(function() {
  'use strict';

  /* --- Mobile menu --- */
  var hamburger = document.querySelector('.hamburger');
  var mobileMenu = document.querySelector('.mobile-menu');
  var closeMenu = document.querySelector('.close-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', function() {
      mobileMenu.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  }
  if (closeMenu && mobileMenu) {
    closeMenu.addEventListener('click', function() {
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
  if (mobileMenu) {
    var mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        mobileMenu.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  /* --- FAQ accordion: fermer les autres quand on en ouvre un --- */
  var faqSections = document.querySelectorAll('.faq-section');
  faqSections.forEach(function(section) {
    var details = section.querySelectorAll('details');
    details.forEach(function(detail) {
      detail.addEventListener('toggle', function() {
        if (detail.open) {
          details.forEach(function(other) {
            if (other !== detail) other.removeAttribute('open');
          });
        }
      });
    });
  });

  /* --- Table des matieres (TOC) toggle --- */
  var tocElements = document.querySelectorAll('.toc-title');
  tocElements.forEach(function(tocTitle) {
    tocTitle.addEventListener('click', function() {
      tocTitle.parentElement.classList.toggle('collapsed');
    });
  });

  /* --- Nav border on scroll --- */
  var nav = document.querySelector('nav');
  if (nav) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 20) {
        nav.style.boxShadow = 'var(--shadow)';
      } else {
        nav.style.boxShadow = 'none';
      }
    }, { passive: true });
  }

})();
