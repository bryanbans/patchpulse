// Private local QA. No real-data screenshots are written into public assets.
import { chromium } from '../web/node_modules/@playwright/test/index.mjs';
import { mkdir } from 'node:fs/promises';
const browser = await chromium.launch();
try {
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8001');
  await page.getByText('PRIVATE REAL-DATA STUDY',{exact:true}).waitFor();
  if(!await page.getByText('98.1%',{exact:true}).isVisible()) throw new Error('Real before rate absent');
  if(!await page.getByText('97.1%',{exact:true}).isVisible()) throw new Error('Real after rate absent');
  await page.getByRole('navigation').getByRole('button',{name:'Evidence',exact:true}).click();
  await page.getByRole('combobox',{name:'Window',exact:true}).selectOption('before');
  await page.getByRole('combobox',{name:'Recorded recommendation',exact:true}).selectOption('negative');
  await page.getByRole('status').filter({hasText:'16 matching reviews / 853'}).waitFor();
  await page.getByRole('button',{name:'Inspect evidence +'}).first().click();
  await mkdir('../private/qa',{recursive:true});
  await page.screenshot({path:'../private/qa/real-evidence.png',fullPage:true});
  await page.getByRole('navigation').getByRole('button',{name:'Model lab'}).click();
  await page.getByRole('button',{name:'Predict recommendation'}).click();
  await page.getByRole('status').filter({hasText:'Recommended-class score'}).waitFor();
  if(errors.length) throw new Error(errors.join('\n'));
  console.log('Private real-data UI smoke passed: rates, filters, evidence, prediction, console.');
} finally { await browser.close(); }
