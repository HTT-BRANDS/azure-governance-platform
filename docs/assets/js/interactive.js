// Azure Governance Platform - Interactive Features

// Initialize Mermaid diagrams
document.addEventListener('DOMContentLoaded', function() {
  // Initialize mermaid if available
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      themeVariables: {
        primaryColor: '#0078d4',
        primaryTextColor: '#fff',
        primaryBorderColor: '#005a9e',
        lineColor: '#605e5c',
        secondaryColor: '#71afe5',
        tertiaryColor: '#f3f2f1'
      }
    });
  }

  // Add smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add hover effects to metric cards
  const metricCards = document.querySelectorAll('.metric-card');
  metricCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-4px)';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // Highlight current page in navigation
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.site-nav a');
  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath || 
        currentPath.startsWith(link.getAttribute('href')) && link.getAttribute('href') !== '/') {
      link.style.color = '#0078d4';
      link.style.fontWeight = '600';
    }
  });

  // Console greeting for developers
  console.log('%c🔷 Azure Governance Platform', 'color: #0078d4; font-size: 20px; font-weight: bold;');
  console.log('%cProduction Certified • Rock Solid • Enterprise Grade', 'color: #107c10; font-size: 14px;');
  console.log('%cDocumentation: https://htt-brands.github.io/azure-governance-platform/', 'color: #605e5c; font-size: 12px;');
});

// Utility function to format numbers
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// Utility function to animate counters
function animateCounter(element, target, duration = 1000) {
  const start = 0;
  const increment = target / (duration / 16);
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = formatNumber(target);
      clearInterval(timer);
    } else {
      element.textContent = formatNumber(Math.floor(current));
    }
  }, 16);
}

// Export functions for global access
window.AzureGov = {
  formatNumber,
  animateCounter
};
