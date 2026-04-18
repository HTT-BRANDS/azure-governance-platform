/**
 * Tailwind CSS v3 config — HTT Brands design system.
 *
 * Ported from ~/dev/master-hub-infra/tailwind.config.ts and extended with
 * our Fluent-style 10-stop brand ramps (brand-primary-5 .. -180) and the
 * Walmart/Riverside color scale (wm-*) used by the Riverside tenant.
 *
 * See: docs/decisions/adr-0005-design-system-overhaul.md
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/templates/**/*.html',
    './app/**/*.py',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },

      /* Brand tokens — pulled from CSS vars (single source of truth lives in
       * design-tokens.css so css_generator.py can override per-tenant via
       * [data-brand="..."] selectors).
       *
       * Using the rgb(var(--foo-rgb) / <alpha-value>) pattern so Tailwind
       * opacity suffixes work: bg-brand-primary/50 etc. */
      colors: {
        /* Legacy HTT shorthand (keeps older template class usage working) */
        'htt-primary':       'var(--htt-primary)',
        'htt-primary-light': 'var(--htt-primary-light)',
        'htt-primary-dark':  'var(--htt-primary-dark)',
        'htt-secondary':     'var(--htt-secondary)',
        'htt-accent':        'var(--htt-accent)',

        /* Fluent-style 10-stop brand ramps */
        'brand-primary': {
          DEFAULT: 'var(--brand-primary)',
          5:   'var(--brand-primary-5)',
          10:  'var(--brand-primary-10)',
          50:  'var(--brand-primary-50)',
          100: 'var(--brand-primary-100)',
          110: 'var(--brand-primary-110)',
          130: 'var(--brand-primary-130)',
          140: 'var(--brand-primary-140)',
          160: 'var(--brand-primary-160)',
          180: 'var(--brand-primary-180)',
        },
        'brand-secondary': {
          DEFAULT: 'var(--brand-secondary)',
          5:   'var(--brand-secondary-5)',
          10:  'var(--brand-secondary-10)',
          50:  'var(--brand-secondary-50)',
          100: 'var(--brand-secondary-100)',
          110: 'var(--brand-secondary-110)',
          130: 'var(--brand-secondary-130)',
          140: 'var(--brand-secondary-140)',
          160: 'var(--brand-secondary-160)',
          180: 'var(--brand-secondary-180)',
        },
        'brand-accent': {
          DEFAULT: 'var(--brand-accent)',
          5:   'var(--brand-accent-5)',
          10:  'var(--brand-accent-10)',
          50:  'var(--brand-accent-50)',
          100: 'var(--brand-accent-100)',
          110: 'var(--brand-accent-110)',
          130: 'var(--brand-accent-130)',
          140: 'var(--brand-accent-140)',
          160: 'var(--brand-accent-160)',
          180: 'var(--brand-accent-180)',
        },

        /* Walmart/Riverside scale */
        'wm-blue': {
          5:   '#f2f8ff',
          10:  '#e0edff',
          30:  '#74a8ff',
          50:  '#3d7eff',
          100: '#0053e2',
          110: '#004bc8',
          130: '#003ba0',
        },
        'wm-gray':  { 5: '#fafafa', 10: '#f5f5f5', 30: '#e5e5e5', 50: '#a0a0a0', 100: '#2e2f32' },
        'wm-green': { 5: '#f0f9e8', 10: '#d9f2c4', 50: '#5cc44e', 100: '#2a8703' },
        'wm-red':   { 100: '#a00b00' },
        'wm-spark': { 100: '#ffc220' },
        'wm-orange':{ 100: '#ae3a0b' },

        /* Tenant accent colors (matches master-hub-infra) */
        tenant: {
          htt:         '#500711',
          bishops:     '#c2410c',
          lashlounge:  '#7c3aed',
          frenchies:   '#2563eb',
          deltacrown:  '#004538',
        },

        /* Semantic surface + text (backed by CSS vars, dark-mode aware) */
        'bg-primary':       'var(--bg-primary)',
        'bg-secondary':     'var(--bg-secondary)',
        'bg-tertiary':      'var(--bg-tertiary)',
        'text-primary':     'var(--text-primary)',
        'text-secondary':   'var(--text-secondary)',
        'text-muted':       'var(--text-muted)',
        'border-color':     'var(--border-color)',

        /* Colorblind-safe semantic colors */
        'success': 'var(--color-success)',
        'warning': 'var(--color-warning)',
        'error':   'var(--color-error)',
        'info':    'var(--color-info)',
      },

      animation: {
        'fade-in':    'fadeIn 0.5s ease-out',
        'slide-up':   'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: {
          '0%':   { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',    opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
