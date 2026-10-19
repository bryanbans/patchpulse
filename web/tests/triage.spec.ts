import {test, expect} from '@playwright/test';
test('complaint investigation includes recommended reviews and returns to its scope', async ({page}, info) => {
 await page.goto('/');
 await page.getByRole('button',{name:'Find potential complaints'}).click();
 await expect(page.getByLabel('Suggested feedback')).toHaveValue('complaint');
 await expect(page.getByRole('combobox',{name:'Window',exact:true})).toHaveValue('after');
 await expect(page.getByRole('combobox',{name:'Recorded recommendation',exact:true})).toHaveValue('all');
 await page.getByRole('combobox',{name:'Recorded recommendation',exact:true}).selectOption('positive');
 await expect(page.locator('.matched-passages')).toBeVisible();
 await expect(page.locator('.review-meta')).toContainText('Recommended');
 await expect(page.locator('.matched-passages')).toContainText('Potential complaint');
 await page.screenshot({path:`../assets/${info.project.name}-complaint-triage.png`,fullPage:true});
 await page.getByRole('button',{name:'Analyze this review'}).click();
 await page.getByRole('button',{name:'Back to review and filters'}).click();
 await expect(page.getByLabel('Suggested feedback')).toHaveValue('complaint');
 await expect(page.getByRole('combobox',{name:'Recorded recommendation',exact:true})).toHaveValue('positive');
 await expect(page.locator('.matched-passages')).toBeVisible();
});
test('evidence errors offer a retry and hide stale results',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Browse reviews',exact:false}).click();
 await expect(page.locator('.review-reader')).toBeVisible();
 await page.route('**/api/evidence?**',route=>route.fulfill({status:503,body:'unavailable'}));
 await page.getByLabel('Suggested feedback').selectOption('complaint');
 await expect(page.getByRole('button',{name:'Retry evidence'})).toBeVisible();
 await expect(page.locator('.review-reader')).toHaveCount(0);
 await page.unroute('**/api/evidence?**');
 await page.getByRole('button',{name:'Retry evidence'}).click();
 await expect(page.locator('.matched-passages')).toBeVisible();
});
