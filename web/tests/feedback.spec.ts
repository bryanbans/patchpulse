import { test, expect } from "@playwright/test";
test("mixed feedback produces aspect-specific praise and complaint with inspectable evidence", async ({
  page,
}, info) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Analyze feedback", exact: true })
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
  await expect(gameplay).toContainText("Praise · suggested");
  await expect(multiplayer).toContainText("Complaint · suggested");
  await expect(gameplay).toContainText("Great missions");
  await expect(multiplayer).toContainText(
    "our co-op sessions keep disconnecting",
  );
  await multiplayer.getByText("Why this label?").click();
  await expect(multiplayer).toContainText(
    "Words used by the rules: disconnecting",
  );
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
  await page.getByRole("button", { name: "No crashes", exact: true }).click();
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(
    page.locator(".feedback-card").filter({ hasText: "Stability" }),
  ).toContainText("Praise · suggested");
  await expect(
    page.locator(".feedback-card").filter({ hasText: "Performance" }),
  ).toContainText("Complaint · suggested");
  await page.getByRole("button", { name: "Mixed feedback" }).click();
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-card")).toHaveCount(1);
  await expect(page.locator(".feedback-card")).toContainText(
    "Mixed feedback · suggested",
  );
  await page
    .getByLabel("Review to analyze")
    .fill("<img src=x onerror=alert(1)> I recommend it.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.getByText("No topic was recognized.")).toBeVisible();
  await expect(page.locator(".feedback-results img")).toHaveCount(0);
});
test("an evidence review can be sent to the aspect lab without changing its recommendation", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Reviews", exact: true })
    .click();
  const reviewText = await page.locator(".review > p").first().textContent();
  await page
    .getByRole("button", { name: "Analyze this review" })
    .first()
    .click();
  await expect(page.getByLabel("Review to analyze")).toHaveValue(reviewText!);
  await expect(
    page.getByRole("heading", {
      name: "What does this review praise or criticize?",
    }),
  ).toBeVisible();
});

test("supervised prototype stays labeled synthetic", async ({ page }) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Analyze feedback", exact: true })
    .click();
  await page.getByLabel("Analysis method").selectOption("supervised");
  await page
    .getByLabel("Review to analyze")
    .fill("Our lobby disconnects every night.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-results")).toContainText(
    "Learned from invented example passages.",
  );
  await expect(page.locator(".feedback-card")).toContainText("Multiplayer");
  await page.locator(".feedback-card").getByText("Why this label?").click();
  await expect(page.locator(".feedback-card")).toContainText("uncalibrated");
});

test("feedback workspace has a direct URL", async ({ page }) => {
  await page.goto("/feedback");
  await expect(
    page.getByRole("heading", {
      name: "What does this review praise or criticize?",
    }),
  ).toBeVisible();
});

test("repair negation and learned abstentions remain visible with development provenance", async ({
  page,
}, info) => {
  await page.goto("/feedback");
  await page
    .getByText("How is this detector checked?", { exact: true })
    .click();
  await expect(page.locator(".feedback-checks")).toContainText("46 of 48");
  await expect(page.locator(".feedback-checks")).toContainText(
    "not an estimate of accuracy on new reviews",
  );
  await page.getByLabel("Review to analyze").fill("The crashes aren't fixed.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-card")).toContainText(
    "Complaint · suggested",
  );
  await expect(page.locator(".feedback-card")).not.toContainText(
    "Mixed feedback",
  );
  await page.getByLabel("Analysis method").selectOption("supervised");
  await page
    .getByLabel("Review to analyze")
    .fill("I hope the servers are reliable tomorrow.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-card")).toContainText(
    "Needs review · suggested",
  );
  await page.locator(".feedback-card").getByText("Why this label?").click();
  await expect(page.locator(".feedback-card")).toContainText(
    "condition, hope, or wish",
  );
  await expect(page.locator(".feedback-card")).not.toContainText(
    "Model score:",
  );
  await page.locator(".feedback-lab").screenshot({
    path: `../assets/${info.project.name}-aspect-validation.png`,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});
