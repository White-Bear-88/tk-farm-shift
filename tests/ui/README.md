Playwright UI smoke tests

Setup:
1. npm install
2. npx playwright install

Run tests:
- npm run test:ui

Notes:
- Tests run against local static files (file://). Network requests to API endpoints are stubbed for determinism.
- If your environment blocks `file://` navigation, you can serve the `src/` folder with a simple static server (eg. `npx http-server src`) and update the test `page.goto` url accordingly.
