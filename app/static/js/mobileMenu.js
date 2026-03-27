/**
 * Mobile Navigation Menu Toggle
 * CSP-safe: no inline event handlers.
 */
(function() {
  'use strict';
  var btn = document.getElementById('mobile-menu-btn');
  var menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;

  btn.addEventListener('click', function() {
    var expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!expanded));
    menu.classList.toggle('hidden');
  });

  // Close mobile menu after HTMX navigation
  document.addEventListener('htmx:afterSettle', function() {
    menu.classList.add('hidden');
    btn.setAttribute('aria-expanded', 'false');
  });
})();
