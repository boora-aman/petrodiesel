import frappeUIPreset from "frappe-ui/tailwind";
import twColors from "tailwindcss/colors";

const pick = (...names) => Object.fromEntries(names.map((n) => [n, twColors[n]]));

/** @type {import('tailwindcss').Config} */
export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts}",
		"./node_modules/frappe-ui/src/components/Toast/**/*.{vue,js,ts}",
	],
	theme: {
		extend: {
			// frappe-ui stops at xl (1280px); wide-screen layouts need 2xl
			screens: { "2xl": "1536px" },
			fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
			borderRadius: {
				none: "0",
				sm: "0.25rem",
				DEFAULT: "0.375rem",
				md: "0.5rem",
				lg: "0.5rem",
				xl: "0.75rem",
				"2xl": "1rem",
				full: "9999px",
			},
			colors: {
				...pick("slate", "gray", "red", "amber", "green", "blue", "purple", "teal"),
				white: "#fff",
				black: "#000",
				transparent: "transparent",
				current: "currentColor",
				brand: {
					50: "#F0FDFA",
					100: "#CCFBF1",
					600: "#0F766E",
					700: "#115E59",
					800: "#134E4A",
				},
				canvas: "#F7F7F8",
				line: "#E5E7EB",
				ink: { DEFAULT: "#0F172A", 2: "#475569", 3: "#94A3B8" },
			},
			maxWidth: { app: "1600px", sm: "24rem", md: "28rem", lg: "32rem" },
			boxShadow: {
				sm: "0 1px 2px 0 rgba(15,23,42,0.05)",
				lg: "0 10px 15px -3px rgba(15,23,42,0.08), 0 4px 6px -4px rgba(15,23,42,0.04)",
				xl: "0 20px 25px -5px rgba(15,23,42,0.1), 0 8px 10px -6px rgba(15,23,42,0.06)",
			},
		},
	},
	plugins: [],
};
