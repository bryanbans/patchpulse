import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
test("human annotation requires explicit review and preserves Unicode offsets", async ({
  page,
}, testInfo) => {
  await page.route("**/api/annotation-pilot", (r) =>
    r.fulfill({
      json: {
        mode: "synthetic",
        split_hash: "practice-only",
        aspects: ["Stability"],
        polarities: ["negative"],
        records: [
          {
            version_id: "synthetic-unicode",
            text: "🚀 Crashes on launch.",
            annotations: [],
            human_reviewed: false,
          },
          {
            version_id: "synthetic-second",
            text: "Another example.",
            annotations: [],
            human_reviewed: false,
          },
        ],
      },
    }),
  );
  await page.goto("/annotate");
  await expect(
    page.getByRole("button", { name: "Mark reviewed" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: /Export 0 reviewed/ }),
  ).toBeDisabled();
  await page.getByLabel("Reviewer pseudonym").fill("test-reviewer");
  const source = page.getByLabel("Source text — select a passage");
  await source.focus();
  await source.press("Control+Home");
  await source.press("ArrowRight");
  await source.press("ArrowRight");
  for (let i = 0; i < 7; i++) await source.press("Shift+ArrowRight");
  await expect(page.getByText("Selected: “Crashes”")).toBeVisible();
  await page
    .getByRole("combobox", { name: "Aspect", exact: true })
    .selectOption("Stability");
  await page
    .getByRole("combobox", { name: "Polarity", exact: true })
    .selectOption("negative");
  await page.getByRole("button", { name: "Add evidence span" }).click();
  await expect(page.getByText("Unicode offsets [2, 9)")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Export 0 reviewed/ }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Mark reviewed" }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: /Export 1 reviewed/ }).click();
  const download = await downloadPromise;
  const labels = JSON.parse(
    await fs.readFile((await download.path())!, "utf8"),
  );
  expect(labels).toHaveLength(1);
  expect(labels[0]).toMatchObject({
    human_reviewed: true,
    reviewer_id: "test-reviewer",
    annotations: [
      {
        start: 2,
        end: 9,
        passage: "Crashes",
        aspect: "Stability",
        polarity: "negative",
      },
    ],
  });
  expect(labels[0]).not.toHaveProperty("voted_up");
  await page.screenshot({
    path: `../assets/${testInfo.project.name}-annotation.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.reload();
  await expect(
    page.getByRole("button", { name: /Export 0 reviewed/ }),
  ).toBeDisabled();
  await page
    .getByLabel("Resume from a reviewed export (processed locally)")
    .setInputFiles({
      name: "reviewed.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(labels)),
    });
  await expect(
    page.getByRole("button", { name: /Export 1 reviewed/ }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "← Previous" }).click();
  await expect(page.getByText("Stability · negative")).toBeVisible();
  await page
    .getByLabel("Resume from a reviewed export (processed locally)")
    .setInputFiles({
      name: "wrong.json",
      mimeType: "application/json",
      buffer: Buffer.from(
        JSON.stringify([{ ...labels[0], text: "wrong source text" }]),
      ),
    });
  await expect(page.getByRole("alert")).toContainText("does not match");
  await page.getByRole("button", { name: "Dismiss", exact: true }).click();
  await page.getByRole("button", { name: "Remove span 1" }).click();
  await expect(
    page.getByRole("button", { name: /Export 0 reviewed/ }),
  ).toBeDisabled();
});
test("detector choice is sent to API and thresholds stay visible", async ({
  page,
}) => {
  await page.route("**/api/models", (r) =>
    r.fulfill({
      json: [
        {
          id: "selected",
          description: "Selected detector",
          negative_threshold: 0.5,
        },
        {
          id: "sensitive",
          description: "Sensitive detector",
          negative_threshold: 0.05,
        },
      ],
    }),
  );
  await page.route("**/api/predict", (r) => {
    expect(r.request().postDataJSON().model_id).toBe("sensitive");
    return r.fulfill({
      json: {
        model_id: "sensitive",
        prediction: "not recommended",
        score_recommended: 0.9,
        score_not_recommended: 0.1,
        negative_threshold: 0.05,
        abstention_reason: null,
      },
    });
  });
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Model lab", exact: true })
    .click();
  await page.getByLabel("Detector", { exact: true }).selectOption("sensitive");
  await page.getByRole("button", { name: "Predict recommendation" }).click();
  await expect(page.getByRole("status")).toContainText(
    "decision threshold: 0.05",
  );
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Methodology", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Detector comparison" }),
  ).toContainText("char-balanced-v2 · selected");
  await expect(
    page.getByText(
      "Metrics in this panel measure synthetic workflow behavior only.",
    ),
  ).toBeVisible();
});

test("neural study shows seed ablations and honest failure outcome", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Methodology", exact: true })
    .click();
  const study = page.getByRole("region", {
    name: "Neural ablation comparison",
  });
  await expect(study).toContainText("distilbert-unweighted-v1");
  await expect(study).toContainText("distilbert-balanced-v1");
  await expect(
    page.getByText("Measured outcome: retain the classical detector."),
  ).toBeVisible();
  await expect(
    page.getByText(/Every neural checkpoint predicts the majority class/),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});
