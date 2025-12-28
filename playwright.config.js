// Playwright config for simple UI smoke tests
/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
  testDir: 'tests/ui',
  timeout: 30000,
  use: {
    headless: true,
    viewport: { width: 1280, height: 800 },
    actionTimeout: 10000
  }
};
