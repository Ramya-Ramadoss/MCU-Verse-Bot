/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          bg: "#020813",          // deep dark tech blue
          card: "rgba(6, 18, 36, 0.65)", // semi-transparent tech card
          border: "rgba(0, 242, 254, 0.15)", // soft glowing cyan border
          cyan: "#00f2fe",        // main neon cyan accent
          blue: "#4facfe",        // main neon blue accent
          gold: "#f6d365",        // gold highlights
          text: "#e2e8f0",        // slate white text
          muted: "#64748b"        // slate gray muted text
        }
      },
      fontFamily: {
        tech: ["Orbitron", "Outfit", "Inter", "sans-serif"]
      },
      boxShadow: {
        glow: "0 0 15px rgba(0, 242, 254, 0.25)",
        goldGlow: "0 0 15px rgba(246, 211, 101, 0.2)"
      }
    },
  },
  plugins: [],
}
