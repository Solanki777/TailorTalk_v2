/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        panel: {
          black: "#0A0D12",
          graphite: "#151A22",
          wire: "#262D3A",
        },
        instrument: {
          amber: "#F2A93B",
          gray: "#808A9E",
        },
        phosphor: "#34D399",
        caution: "#F2545B",
        fog: "#E7EAF0",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
        body: ['"IBM Plex Sans"', "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
    },
  },
  plugins: [],
}