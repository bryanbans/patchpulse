import { test, expect } from "@playwright/test";
test("mixed feedback produces aspect-specific praise and complaint with inspectable evidence", async ({
  page,
}, info) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Model lab", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  const gameplay = page.locator(".feedback-card").filter({
    has: page.getByRole("heading", { name: "Gameplay", exact: true }),
  });
  const multiplayer = page.locator(".feedback-card").filter({
    has: page.getByRole("heading", { name: "Multiplayer", exact: true }),
  });
  await expect(gameplay).toContainText("Praise · provisional");
  await expect(multiplayer).toContainText("Complaint · provisional");
  await expect(gameplay).toContainText("Great missions");
  await expect(multiplayer).toContainText(
    "our co-op sessions keep disconnecting",
  );
  await multiplayer.getByText("Why this label?").click();
  await expect(multiplayer).toContainText("Rule cues: disconnecting");
  await page.evaluate(() => {
    (document.activeElement as HTMLElement)?.blur();
    window.scrollTo(0, 0);
  });
  await page.locator(".feedback-lab").screenshot({
    path: `../assets/${info.project.name}-aspect-feedback.png`,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Negation", exact: true }).click();
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(
    page.locator(".feedback-card").filter({ hasText: "Stability" }),
  ).toContainText("Praise · provisional");
  await expect(
    page.locator(".feedback-card").filter({ hasText: "Performance" }),
  ).toContainText("Complaint · provisional");
  await page
    .getByRole("button", { name: "Same topic, mixed feedback" })
    .click();
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-card")).toHaveCount(1);
  await expect(page.locator(".feedback-card")).toContainText(
    "Mixed feedback · provisional",
  );
  await page
    .getByLabel("Feedback to analyze")
    .fill("<img src=x onerror=alert(1)> I recommend it.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(
    page.getByText("No supported aspect was detected."),
  ).toBeVisible();
  await expect(page.locator(".feedback-results img")).toHaveCount(0);
});
test("an evidence review can be sent to the aspect lab without changing its recommendation", async ({
  page,
}) => {
  await page.goto("/");
  const reviewText = await page.locator(".review > p").first().textContent();
  await page
    .getByRole("button", { name: "Analyze topic sentiment" })
    .first()
    .click();
  await expect(page.getByLabel("Feedback to analyze")).toHaveValue(reviewText!);
  await expect(
    page.getByRole("heading", {
      name: "One review. Different kinds of feedback.",
    }),
  ).toBeVisible();
});

test("supervised prototype stays labeled synthetic", async ({ page }) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Model lab", exact: true })
    .click();
  await page.getByLabel("Aspect analysis method").selectOption("supervised");
  await page
    .getByLabel("Feedback to analyze")
    .fill("Our lobby disconnects every night.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-results")).toContainText(
    "synthetic authored examples; not real-world quality evidence",
  );
  await expect(page.locator(".feedback-card")).toContainText("Multiplayer");
  await page.locator(".feedback-card").getByText("Why this label?").click();
  await expect(page.locator(".feedback-card")).toContainText("uncalibrated");
});

test("feedback workspace has a direct URL", async ({ page }) => {
  await page.goto("/feedback");
  await expect(
    page.getByRole("heading", {
      name: "One review. Different kinds of feedback.",
    }),
  ).toBeVisible();
});
