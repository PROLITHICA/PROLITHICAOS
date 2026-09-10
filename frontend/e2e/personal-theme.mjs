import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const base = 'http://localhost:4200';
try {
  await page.goto(`${base}/login`);
  await page.locator('#login-email').fill('edwin.ndiritu@prolithica.com');
  await page.locator('#login-password').fill('12428newton');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL('**/dashboard');
  await page.locator('.sidebar').waitFor();
  assert.deepEqual(await page.locator('.dept-label').allTextContents(), ['Technology']);
  assert.equal(await page.locator('.nav-label').first().textContent(), 'Dashboard');
  await page.getByRole('button', { name: 'Dark mode', exact: true }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  for (const selector of ['body', '.shell', '.sidebar']) {
    assert.equal(await page.locator(selector).evaluate(e => getComputedStyle(e).backgroundColor), 'rgb(0, 0, 0)');
  }
  assert.equal(await page.locator('.signed-name').evaluate(e => getComputedStyle(e).color), 'rgb(255, 255, 255)');
  await page.reload();
  await page.locator('.sidebar').waitFor();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  await page.goto(`${base}/finance`);
  await page.waitForURL('**/dashboard');
  await page.goto(`${base}/rnd`);
  await page.waitForURL('**/dashboard');
  await page.goto(`${base}/tech`);
  await page.locator('.sidebar').waitFor();
  await page.screenshot({ path: '/tmp/prolithica-dark.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('button', { name: 'Dark mode', exact: true }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  await page.screenshot({ path: '/tmp/prolithica-mobile.png' });
  console.log('PASS: personal sidebar, dark palette, persisted theme, restricted routes, mobile toggle');
} finally { await browser.close(); }
