/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: {
          bg: "#1e293b",
          hover: "#334155",
          active: "#3b82f6",
          text: "#94a3b8",
          "text-active": "#f1f5f9",
        },
      },
    },
  },
  plugins: [],
};
