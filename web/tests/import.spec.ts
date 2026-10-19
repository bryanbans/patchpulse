import { expect, test } from "@playwright/test";

test("a browser-parsed CSV produces local complaint candidates", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("navigation").getByRole("button", { name: "Import data" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "reviews.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      'review_id,review\nkeep,"The missions are fun, but matchmaking fails nightly."\nplain,"The subtitles are excellent."\n',
    ),
  });
  await expect(page.getByText("2 rows read in this browser")).toBeVisible();
  await expect(page.getByLabel("Review text column")).toHaveValue("review");
  await page.getByRole("button", { name: "Find complaint candidates" }).click();
  await expect(page.getByRole("heading", { name: "1 of 2 reviews have a complaint candidate." })).toBeVisible();
  await expect(page.locator(".candidate-list")).toContainText("matchmaking fails nightly");
  await expect(page.locator(".candidate-list")).toContainText("REVIEW keep");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export candidates" }).click();
  expect((await download).suggestedFilename()).toBe("patchpulse-complaint-candidates.txt");
});

test("malformed data explains the expected import shape", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("navigation").getByRole("button", { name: "Import data" }).click();
  await page.locator('input[type="file"]').setInputFiles({ name: "reviews.json", mimeType: "application/json", buffer: Buffer.from('{"not_records": true}') });
  await expect(page.getByRole("alert")).toContainText("JSON must be an array of review objects");
});
