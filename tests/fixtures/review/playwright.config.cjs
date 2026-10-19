// Test infrastructure only; Vera supplies browser assertions after GREEN.
const executablePath = process.env.REVIEW_BROWSER_EXECUTABLE;
module.exports = {
  testDir: __dirname,
  testMatch: /.*\.spec\.cjs/,
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: process.env.REVIEW_BASE_URL,
    headless: true,
    launchOptions: executablePath ? { executablePath } : {},
  },
};
