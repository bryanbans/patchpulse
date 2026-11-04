import { expect, test } from "@playwright/test";

test("research snapshot distinguishes recommendation evidence from complaint detection", async ({ page }, info) => {
  await page.goto("/");
  const snapshot = page.locator(".nlp-snapshot");
  await expect(snapshot).toContainText("Word baseline");
  await expect(snapshot).toContainText("0 / 12");
  await expect(snapshot).toContainText("5 / 12");
  await expect(snapshot).toContainText("406 validation reviews");
  await expect(snapshot).toContainText("not complaint detection");
  await snapshot.screenshot({ path: info.outputPath("nlp-snapshot.png") });
  await snapshot.getByRole("button", { name: "Explore methods & evaluation" }).click();
  await expect(page.getByRole("heading", { name: "What is counted, and what is predicted?" })).toBeVisible();
});

test("unavailable research report is explained and analysis remains accessible", async ({ page }) => {
  await page.route("**/api/research-evaluation", (route) => route.fulfill({ status: 503 }));
  await page.goto("/");
  const snapshot = page.locator(".nlp-snapshot");
  await expect(snapshot).toContainText("Research results are unavailable");
  await snapshot.getByRole("button", { name: "Analyze a review" }).click();
  await expect(page.getByLabel("Review to analyze")).toBeVisible();
});
