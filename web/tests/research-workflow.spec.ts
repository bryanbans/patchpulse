import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";

test("topic investigation keeps a stable reader and a source-linked session notebook", async ({
  page,
}, info) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Inspect Gameplay evidence" }).click();
  await expect(page.getByLabel("Topic mention")).toHaveValue("Gameplay");
  await expect(page.getByRole("status")).toContainText("matching reviews / 48");
  const second = page.getByRole("button", {
    name: "Read review 2",
    exact: true,
  });
  const secondText = await second.locator("p").textContent();
  await second.click();
  await expect(second).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("article", { name: "Selected review" }),
  ).toBeFocused();
  const quote = (await page.locator(".review > p").textContent())!;
  expect(quote.startsWith(secondText!.replace(/…$/, ""))).toBeTruthy();
  await page
    .getByRole("button", { name: "Save review +", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Saved to notebook ✓", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Notebook", exact: true })
    .click();
  await expect(page.locator(".research-note blockquote")).toHaveText(quote);
  await expect(page.locator(".notebook-toast")).toHaveCount(0);
  await expect(page.locator(".note-source")).toContainText(
    "Synthetic example · version",
  );
  await expect(page.locator(".research-note")).toContainText(
    "Recorded recommendation:",
  );
  await page
    .getByLabel("Your interpretation")
    .fill("A passage to investigate, not a causal conclusion.");
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export notebook", exact: false })
    .click();
  const file = await download;
  const saved = info.outputPath("session-notebook.txt");
  await file.saveAs(saved);
  const content = await fs.readFile(saved, "utf8");
  expect(content).toContain(quote);
  expect(content).toContain("A passage to investigate");
  expect(content).toContain("not validated findings");
  await page.screenshot({
    path: `../assets/${info.project.name}-notebook.png`,
    fullPage: true,
  });
  await page.reload();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Notebook", exact: true })
    .click();
  await expect(page.locator(".research-note")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Export notebook", exact: false }),
  ).toBeDisabled();
});

test("saved analysis preserves uncertainty and survives task navigation without re-running", async ({
  page,
}) => {
  await page.goto("/feedback");
  await page
    .getByLabel("Review to analyze")
    .fill("If the servers were reliable, I would play again.");
  await page
    .getByRole("button", { name: "Analyze praise and complaints" })
    .click();
  await expect(page.locator(".feedback-card")).toContainText(
    "Needs review · suggested",
  );
  await page.getByRole("button", { name: "Save passage +" }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Notebook", exact: true })
    .click();
  await expect(page.locator(".research-note")).toContainText(
    "Suggested Needs review",
  );
  await expect(page.locator(".note-source")).toContainText(
    "Pasted text; source not verified",
  );
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Analyze feedback", exact: true })
    .click();
  await expect(page.getByLabel("Review to analyze")).toHaveValue(
    "If the servers were reliable, I would play again.",
  );
  await expect(page.locator(".feedback-card")).toContainText(
    "Needs review · suggested",
  );
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Notebook", exact: true })
    .click();
  await page.getByRole("button", { name: "Remove note 1" }).click();
  await expect(page.locator(".research-note")).toHaveCount(0);
});

test("negative recommendation shortcut and topic navigation set explicit scopes", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator(".concern-shortcut").click();
  await expect(
    page.getByRole("combobox", { name: "Window", exact: true }),
  ).toHaveValue("after");
  await expect(
    page.getByRole("combobox", {
      name: "Recorded recommendation",
      exact: true,
    }),
  ).toHaveValue("negative");
  await expect(page.getByRole("status")).toContainText(
    "12 matching reviews / 24",
  );
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Overview", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Inspect Multiplayer evidence" })
    .click();
  await expect(
    page.getByRole("combobox", { name: "Window", exact: true }),
  ).toHaveValue("all");
  await expect(
    page.getByRole("combobox", {
      name: "Recorded recommendation",
      exact: true,
    }),
  ).toHaveValue("all");
  await expect(page.getByLabel("Topic mention")).toHaveValue("Multiplayer");
});

test("task workspaces fit compact screens without clipping their controls", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto("/");
  for (const name of ["Overview", "Reviews", "Notebook"]) {
    await page
      .getByRole("navigation")
      .getByRole("button", { name, exact: true })
      .click();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
});
