import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
try {
  await page.goto('http://localhost:4200/login');
  await page.locator('#login-email').fill('newtvnbrian@gmail.com');
  await page.locator('#login-password').fill('12428newton');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL('**/dashboard');
  const clock = page.locator('.dashboard-clock time');
  await clock.waitFor();
  assert.match(await clock.textContent(), /^\d{2}:\d{2}:\d{2}$/);
  await page.waitForFunction(value => document.querySelector('.dashboard-clock time')?.textContent !== value, await clock.textContent());
  await page.goto('http://localhost:4200/projects/PRJ-041');
  await page.locator('.margin-gauge').waitFor();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    const plan = await page.locator('.margin-plan').boundingBox();
    const gauge = await page.locator('.margin-gauge').boundingBox();
    const caption = await page.locator('.margin-caption').boundingBox();
    assert.ok(plan.y + plan.height <= gauge.y);
    assert.ok(gauge.y + gauge.height <= caption.y);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  }
  console.log('PASS: live clock advances; margin labels do not overlap at desktop/mobile widths');
} finally { await browser.close(); }
