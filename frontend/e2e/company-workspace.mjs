import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://localhost:4200/login');
 await page.locator('#email').waitFor();await page.evaluate(()=>document.fonts.ready);
 await page.screenshot({path:'/private/tmp/os-login-desktop.png',fullPage:true});
 assert.match(await page.locator('body').evaluate(e=>getComputedStyle(e).fontFamily),/Space Grotesk/);
 await page.locator('#email').fill('newtvnbrian@gmail.com');await page.locator('#password').fill('12428newton');await page.getByRole('button',{name:'Sign in →',exact:true}).click();
 await page.waitForURL('**/dashboard',{timeout:30000});
 for(const route of ['work','chat','profile','records/users','records/projects','records/people','dashboard','command','tech','finance','rnd','admin-desk','documents','knowledge']){
  await page.goto('http://localhost:4200/'+route);await page.waitForTimeout(1000);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  console.log(route,'overflow:',overflow);assert.equal(overflow,false,route+' desktop overflow');
  if(['work','chat','profile','records/users','dashboard'].includes(route))await page.screenshot({path:'/private/tmp/os-'+route.replaceAll('/','-')+'.png',fullPage:true});
 }
 await page.goto('http://localhost:4200/work');await page.getByText('Employee number',{exact:true}).waitFor();
 assert.equal(await page.locator('select[name="logProject"] option').count(),9);
 for(const route of ['work','chat','profile','records/users','dashboard']){
  await page.setViewportSize({width:390,height:844});await page.goto('http://localhost:4200/'+route);await page.waitForTimeout(600);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,route+' mobile overflow');
 }
 await page.screenshot({path:'/private/tmp/os-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS company typography, login, eight projects, desktop/mobile routes and browser errors');
}finally{await browser.close();}
