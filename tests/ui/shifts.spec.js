const { test, expect } = require('@playwright/test');
const path = require('path');

test('menu -> shifts: no modal on load, month defaults to current, click day opens modal', async ({ page }) => {
  // Stub backend endpoints used during page load to keep test deterministic
  await page.route('**/shifts/by-month/**', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));
  await page.route('**/shifts/by-date/**', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));
  await page.route('**/tasks', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));
  await page.route('**/employees', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));

  // Open local file menu.html and navigate to shifts page via UI
  const menuPath = path.join(__dirname, '../../src/menu.html');
  await page.goto('file://' + menuPath);
  await page.click('text=シフト管理へ');
  await page.waitForLoadState('domcontentloaded');

  // The shift modal should NOT be visible on initial navigation
  await expect(page.locator('#shiftModal')).toBeHidden();

  // The calendar month input should default to current month
  const cv = await page.locator('#calendarMonth').inputValue();
  const now = new Date();
  const expected = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  expect(cv).toBe(expected);

  // Click the first calendar day; modal should open
  const day = page.locator('.shift-calendar .calendar-day').first();
  await day.click();
  await expect(page.locator('#shiftModal')).toBeVisible();
});
