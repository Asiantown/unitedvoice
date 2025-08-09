import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#000000",
          secondary: "#0a0a0a",
          tertiary: "#111111",
        },
        foreground: {
          DEFAULT: "#ffffff",
          secondary: "#e5e5e5",
          muted: "#a1a1aa",
        },
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        accent: {
          purple: "#8b5cf6",
          pink: "#ec4899",
          blue: "#3b82f6",
          green: "#10b981",
          orange: "#f59e0b",
        },
        border: {
          DEFAULT: "#27272a",
          light: "#3f3f46",
        },
        card: {
          DEFAULT: "#0a0a0a",
          hover: "#111111",
        },
        gradient: {
          from: "#000000",
          via: "#1a1a1a",
          to: "#000000",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.75rem" }],
      },
      spacing: {
        18: "4.5rem",
        88: "22rem",
        92: "23rem",
        96: "24rem",
        104: "26rem",
        112: "28rem",
        128: "32rem",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "fade-out": "fadeOut 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-x": "gradientX 3s ease infinite",
        "gradient-y": "gradientY 3s ease infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeOut: {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideDown: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.9)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        gradientX: {
          "0%, 100%": {
            "background-size": "200% 200%",
            "background-position": "left center",
          },
          "50%": {
            "background-size": "200% 200%",
            "background-position": "right center",
          },
        },
        gradientY: {
          "0%, 100%": {
            "background-size": "200% 200%",
            "background-position": "center top",
          },
          "50%": {
            "background-size": "200% 200%",
            "background-position": "center bottom",
          },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "gradient-dark": "linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #000000 100%)",
        "gradient-accent": "linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #10b981 100%)",
        "gradient-purple": "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
        "gradient-blue": "linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)",
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        "dark-sm": "0 1px 2px 0 rgba(255, 255, 255, 0.05)",
        "dark-md": "0 4px 6px -1px rgba(255, 255, 255, 0.1), 0 2px 4px -1px rgba(255, 255, 255, 0.06)",
        "dark-lg": "0 10px 15px -3px rgba(255, 255, 255, 0.1), 0 4px 6px -2px rgba(255, 255, 255, 0.05)",
        "glow-sm": "0 0 20px rgba(139, 92, 246, 0.3)",
        "glow-md": "0 0 40px rgba(139, 92, 246, 0.4)",
        "glow-lg": "0 0 60px rgba(139, 92, 246, 0.5)",
      },
    },
  },
  plugins: [],
};

export default config;