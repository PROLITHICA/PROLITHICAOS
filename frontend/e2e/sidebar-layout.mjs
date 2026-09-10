import { chromium } from 'playwright';

const baseUrl = process.env.PROLITHICA_E2E_URL ?? 'http://127.0.0.1:4200';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

try {
  await page.goto(`${baseUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-email').fill('newtvnbrian@gmail.com');
  await page.locator('#login-password').fill('12428newton');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');

  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight / 2));

  const sidebar = await page.locator('.sidebar').evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return { top: rect.top, bottom: rect.bottom, height: rect.height, viewport: window.innerHeight };
  });

  const expectedHeight = sidebar.viewport - 28;
  if (Math.abs(sidebar.top - 14) > 1 || Math.abs(sidebar.height - expectedHeight) > 1 || Math.abs(sidebar.bottom - (sidebar.viewport - 14)) > 1) {
    throw new Error(`Sidebar must remain viewport-anchored while the page scrolls; received ${JSON.stringify(sidebar)}`);
  }

  await page.setViewportSize({ width: 900, height: 900 });
  const navigationToggle = page.getByRole('button', { name: 'Open navigation' });
  await navigationToggle.click();
  await page.waitForFunction(() => document.querySelector('.shell')?.classList.contains('nav-open'));
  if (await navigationToggle.getAttribute('aria-expanded') !== 'true') {
    throw new Error('Navigation drawer did not open at tablet width.');
  }

  await page.getByRole('button', { name: 'Close navigation' }).first().click();
  await page.waitForFunction(() => !document.querySelector('.shell')?.classList.contains('nav-open'));
  if (await navigationToggle.getAttribute('aria-expanded') !== 'false') {
    throw new Error('Navigation drawer did not close at tablet width.');
  }
} finally {
  await browser.close();
}
