import { test, expect } from "@playwright/test";

test("signals use each window's denominator and lead to scoped evidence", async ({ page }) => {
  await page.route("**/api/case-studies/drg-season-05", async (route) => {
    const response = await route.fetch();
    const study = await response.json();
    study.periods.before.count = 100;
    study.periods.after.count = 20;
    study.mentions = [
      { aspect: "Gameplay", before: 20, after: 8 },
      { aspect: "Multiplayer", before: 40, after: 4 },
    ];
    await route.fulfill({ response, json: study });
  });
  await page.goto("/");
  const signals = page.locator(".signal-strip");
  await expect(signals).toContainText("120");
  await expect(signals).toContainText("8 of 20 reviews · 40.0%");
  await expect(signals).toContainText("TIED BIGGEST SHARE CHANGE");
  await expect(signals).toContainText("+20.0");
  await signals.getByRole("button", { name: /MOST MENTIONED AFTER/ }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Topic mention")).toHaveValue("Gameplay");
  await expect(page.getByRole("combobox", { name: "Window", exact: true })).toHaveValue("after");
});

test("the overview opens the review import workflow", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Import your reviews" }).click();
  await expect(page.getByRole("heading", { name: "Turn an export into an investigation queue." })).toBeVisible();
});

test("empty windows do not manufacture a leading topic or share change", async ({ page }) => {
  await page.route("**/api/case-studies/drg-season-05", async (route) => {
    const response = await route.fetch();
    const study = await response.json();
    study.periods.before.count = 0;
    study.periods.after.count = 0;
    study.mentions = [];
    await route.fulfill({ response, json: study });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto("/");
  await expect(page.locator(".signal-strip")).toContainText("0 before · 0 after");
  await expect(page.locator(".signal-strip button")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});
