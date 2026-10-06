import frappeUIPreset from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [{ pattern: /!(text|bg)-/, variants: ['hover', 'active'] }],
  theme: {
    extend: {
      // Merriweather everywhere in Pathways (loaded in index.html).
      fontFamily: {
        sans: ['Merriweather', 'Georgia', 'serif'],
      },
      // NLSIU maroon (#920C24 = brand-700) for accents.
      colors: {
        brand: {
          50: '#FDF2F4',
          100: '#FBE5E8',
          200: '#F5C2CA',
          300: '#EC94A2',
          400: '#DC5A6F',
          500: '#C42A44',
          600: '#A9142F',
          700: '#920C24',
          800: '#780A1E',
          900: '#5E0818',
        },
      },
    },
  },
  plugins: [],
}
