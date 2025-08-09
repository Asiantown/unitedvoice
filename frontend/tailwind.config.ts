import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    screens: {
      'xs': '475px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        // United Airlines Brand Colors
        united: {
          blue: "#0057B8",
          "blue-dark": "#003B7A",
          "blue-light": "#1E6BB8",
          gold: "#FFB81C",
          "gold-dark": "#E6A617",
        },
        // Dark theme colors similar to 11.ai
        dark: {
          bg: "#0A0A0A",
          surface: "#1A1A1A",
          "surface-elevated": "#2A2A2A",
          border: "#333333",
          text: "#FFFFFF",
          "text-muted": "#A0A0A0",
        },
        // Accent colors
        accent: {
          purple: "#8B5CF6",
          "purple-dark": "#7C3AED",
          blue: "#3B82F6",
          "blue-dark": "#2563EB",
        },
        // Semantic colors
        success: "#10B981",
        warning: "#F59E0B",
        error: "#EF4444",
        // Override default background and foreground
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
