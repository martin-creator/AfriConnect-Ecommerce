// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
    // Add other paths as needed
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
