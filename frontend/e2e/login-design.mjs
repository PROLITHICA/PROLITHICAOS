import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1390, height: 768 } });
try {
  await page.goto('http://localhost:4200/login');
  await page.locator('#login-email').waitFor();
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: '/tmp/prolithica-login-desktop.png' });
  for (const width of [1390, 768, 390]) {
    await page.setViewportSize({ width, height: 844 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const form = await page.locator('.form').boundingBox();
    const intro = await page.locator('.introduction').boundingBox();
    assert.ok(width > 820 ? intro.x + intro.width <= form.x : intro.y + intro.height <= form.y);
  }
  await page.screenshot({ path: '/tmp/prolithica-login-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('alert').waitFor();
  await page.locator('#login-email').fill('newtvnbrian@gmail.com');
  await page.locator('#login-password').fill('12428newton');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL('**/dashboard');
  console.log('PASS: responsive login layout, validation, and successful sign-in');
} finally { await browser.close(); }
