import type { Config } from "tailwindcss";

/**
 * Aegis-KOBİ design tokens.
 *
 * Hedef kitle: tarım / el sanatları kooperatifleri, çoğunlukla teknik olmayan
 * kadın çalışanlar. Bu yüzden tema: beyaz zemin + doğal yeşil + sıcak krem,
 * yumuşak konturlar, geniş boşluklar, büyük tipografi.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Sage — primary brand (yumuşak yeşil, doğa, güven)
        sage: {
          50: "#f3f7f4",
          100: "#e3ede6",
          200: "#c7dccd",
          300: "#a4c3b2",
          400: "#86ac95",
          500: "#6b9080", // ana
          600: "#557566",
          700: "#445e52",
          800: "#374b42",
          900: "#2e3d36",
        },
        // Cream — yüzeyler, kartlar
        cream: {
          50: "#fefcf7",
          100: "#fbf8ee",
          200: "#f7f1de",
          300: "#efe6c5",
          400: "#e3d5a3",
          500: "#cdbb7d",
        },
        // Earth — sıcak vurgular
        earth: {
          50: "#fbf6f0",
          100: "#f3e8d8",
          200: "#e6cfa9",
          300: "#d4b07a",
          400: "#a4886a",
          500: "#8b6f4e",
        },
        // İşlevsel renkler — doğal tonlar
        ink: {
          50: "#fafaf7",
          100: "#f1f0ea",
          200: "#e0dfd5",
          300: "#c2c0b3",
          400: "#8a8b7e",
          500: "#5e5f54",
          600: "#3f4039",
          700: "#2c2d28",
          800: "#1d1e1a",
          900: "#101110",
        },
        success: "#6b9080",
        warning: "#d9a679",
        danger: "#c97d77",
        info: "#7a9eb1",
      },
      fontFamily: {
        sans: [
          "Inter",
          "Nunito",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
        ],
        display: ["Nunito", "Inter", "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(60, 80, 70, 0.04), 0 4px 12px -2px rgba(60, 80, 70, 0.06)",
        lift: "0 2px 4px rgba(60, 80, 70, 0.06), 0 12px 28px -8px rgba(60, 80, 70, 0.12)",
        ring: "0 0 0 3px rgba(107, 144, 128, 0.18)",
      },
      backgroundImage: {
        "leaf-fade":
          "radial-gradient(circle at 100% 0%, rgba(164,195,178,0.18), transparent 55%)",
      },
      keyframes: {
        pulseDot: {
          "0%,100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
        fadeUp: "fadeUp 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
