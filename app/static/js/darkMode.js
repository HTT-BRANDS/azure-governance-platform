// Dark Mode ThemeProvider — ported from microsoft-group-management
// Uses .dark/.light class on <html> element with localStorage persistence
// Source: ~/dev/microsoft-group-management/hub/frontend/src/providers/ThemeProvider.tsx
(function() {
  var saved = localStorage.getItem('theme');
  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  var theme = saved || (prefersDark ? 'dark' : 'light');

  document.documentElement.classList.remove('light', 'dark');
  document.documentElement.classList.add(theme);

  // Listen for system preference changes when no explicit theme is saved
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (!localStorage.getItem('theme')) {
      var next = e.matches ? 'dark' : 'light';
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(next);
    }
  });

  window.toggleTheme = function() {
    var current = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.classList.remove(current);
    document.documentElement.classList.add(next);
    localStorage.setItem('theme', next);
  };

  // CSP-safe: bind click via addEventListener instead of inline onclick
  var btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.addEventListener('click', window.toggleTheme);
})();
