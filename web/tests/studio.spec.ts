import { test, expect } from "@playwright/test";

test("studio study context and guided analysis remain keyboard accessible", async ({
  page,
}) => {
  await page.goto("/");
  const study = page.locator(".study-picker > summary");
  await study.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".study-picker-note")).toContainText(
    "one game update",
  );
  await study.press("Enter");
  await page.locator(".window-map summary").click();
  await expect(page.locator(".calendar-cells")).toHaveCount(2);
  await expect(page.locator(".calendar-cells").first()).toBeVisible();
  await page
    .getByRole("button", { name: "Explore praise & complaints" })
    .click();
  await expect(page.getByLabel("Review to analyze")).toHaveValue(
    "Great missions, but our co-op sessions keep disconnecting.",
  );
  await expect(
    page.getByRole("region", { name: "Passage notes" }),
  ).toContainText("Run an analysis");
  await expect(page.locator(".feedback-card")).toHaveCount(0);
});

test("passage highlighting preserves Unicode and distinguishes rule cues from model attribution", async ({
  page,
}) => {
  await page.goto("/feedback");
  await page
    .getByLabel("Review to analyze")
    .fill("🚀 Great missions, but the servers are broken.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  const praise = page.locator(".feedback-card").filter({
    has: page.getByRole("heading", { name: "Gameplay", exact: true }),
  });
  const complaint = page.locator(".feedback-card").filter({
    has: page.getByRole("heading", { name: "Multiplayer", exact: true }),
  });
  await expect(praise.locator("blockquote")).toHaveText("🚀 Great missions");
  await expect(praise.locator('mark[data-tone="positive"]')).toHaveText(
    "Great",
  );
  await expect(complaint.locator("blockquote")).toHaveText(
    "the servers are broken",
  );
  await expect(complaint.locator('mark[data-tone="negative"]')).toHaveText(
    "broken",
  );
  await page.getByLabel("Analysis method").selectOption("supervised");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(
    page
      .getByText(
        "Highlights show rule cues, not the learned model’s reasoning.",
      )
      .first(),
  ).toBeVisible();
  await expect(page.locator(".feedback-reading")).not.toHaveAttribute(
    "aria-busy",
    "true",
  );
});

test("studio layout remains usable at narrow and intermediate widths", async ({
  page,
}) => {
  for (const width of [320, 768, 1024]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/feedback");
    await expect(page.getByLabel("Review to analyze")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    for (const button of await page
      .getByRole("navigation")
      .getByRole("button")
      .all()) {
      const box = await button.boundingBox();
      expect(box && box.x >= 0 && box.x + box.width <= width).toBeTruthy();
    }
  }
});

test("the reading pane communicates pending analysis and recoverable errors", async ({
  page,
}) => {
  let finish: (() => void) | undefined;
  await page.route("**/api/analyze-feedback", async (route) => {
    await new Promise<void>((resolve) => {
      finish = resolve;
    });
    await route.fulfill({ status: 503, json: { detail: "Unavailable" } });
  });
  await page.goto("/feedback");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(
    page.getByRole("button", { name: "Analyzing…", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("region", { name: "Passage notes" }),
  ).toHaveAttribute("aria-busy", "true");
  await expect(
    page.getByText("Reading the feedback…", { exact: true }),
  ).toBeVisible();
  finish!();
  await expect(page.getByRole("alert")).toContainText(
    "Analysis unavailable (503)",
  );
  await expect(
    page.getByRole("button", { name: "Analyze praise and complaints" }),
  ).toBeEnabled();
  await expect(page.locator(".feedback-card")).toHaveCount(0);
});
