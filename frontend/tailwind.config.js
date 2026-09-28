/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: { DEFAULT: "#1F4D3C", dk: "#123028" },
        wheat: { DEFAULT: "#D4A62A", dk: "#a9820f" },
        paper: { DEFAULT: "#F7F3E8", dk: "#efe8d6" },
      },
    },
  },
  plugins: [],
}