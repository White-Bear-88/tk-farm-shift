const { test, expect } = require('@playwright/test');
const path = require('path');

test('tasks modal: open and cancel', async ({ page }) => {
  await page.route('**/tasks', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));

  const menuPath = path.join(__dirname, '../../src/menu.html');
  await page.goto('file://' + menuPath);
  await page.click('text=各種設定へ');
  await page.waitForLoadState('domcontentloaded');

  await page.click('#addTaskButton');
  await expect(page.locator('#taskModal')).toBeVisible();

  await page.click('#taskCancelButton');
  await expect(page.locator('#taskModal')).toBeHidden();
});

test('tasks modal: duplicate ID validation blocks submit', async ({ page }) => {
  // Initial tasks list
  await page.route('**/tasks', route => route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } }));
  // When checking for existing ID, return 200 to indicate it exists
  await page.route('**/tasks/existing', route => route.fulfill({ status: 200, body: JSON.stringify({ task_type: 'existing', name: '既存' }), headers: { 'Content-Type': 'application/json' } }));

  const menuPath = path.join(__dirname, '../../src/menu.html');
  await page.goto('file://' + menuPath);
  await page.click('text=各種設定へ');
  await page.waitForLoadState('domcontentloaded');

  await page.click('#addTaskButton');
  await expect(page.locator('#taskModal')).toBeVisible();

  await page.fill('#taskCode', 'existing');
  await page.fill('#taskName', '重複テスト');

  await page.click('button[type="submit"]');

  // Expect error message about duplicate ID
  await expect(page.locator('#formMessage .message.error')).toHaveText(/入力された作業IDは既に存在します/);
  await expect(page.locator('#taskModal')).toBeVisible();
});

test('tasks modal: successful add with unique ID', async ({ page }) => {
  // Initial tasks list
  await page.route('**/tasks', route => {
    if (route.request().method() === 'GET') {
      route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } });
    } else {
      route.continue();
    }
  });

  // Checking for ID: return 404 (not found)
  await page.route('**/tasks/newid', route => route.fulfill({ status: 404 }));

  // Intercept POST to create and return 201
  await page.route('**/tasks', route => {
    if (route.request().method() === 'POST') {
      route.fulfill({ status: 201, body: '' });
    } else {
      route.fulfill({ status: 200, body: '[]', headers: { 'Content-Type': 'application/json' } });
    }
  });

  const menuPath = path.join(__dirname, '../../src/menu.html');
  await page.goto('file://' + menuPath);
  await page.click('text=各種設定へ');
  await page.waitForLoadState('domcontentloaded');

  await page.click('#addTaskButton');
  await expect(page.locator('#taskModal')).toBeVisible();

  await page.fill('#taskCode', 'newid');
  await page.fill('#taskName', '新規作業');

  await page.click('button[type="submit"]');

  // Expect success message
  await expect(page.locator('#formMessage .message.success')).toHaveText(/作業種別を登録しました/);
  // Modal should be closed
  await expect(page.locator('#taskModal')).toBeHidden();
});
