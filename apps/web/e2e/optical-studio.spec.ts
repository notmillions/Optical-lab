import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("runs the accessible studio flow and exports reproducible results", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Configuration" })).toBeVisible();
  await expect(page.locator(".api-status")).toHaveText(/API CONNECTÉE/);
  await expect(page.getByText(/Catalogue connecté · \d+ matériaux · \d+ références originales/)).toBeVisible();

  // Exercise labelled controls, rather than relying on implementation-specific selectors.
  await expect(page.getByRole("button", { name: "Laser" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Longueur d'onde")).toBeVisible();
  await expect(page.getByLabel("Angle d'incidence")).toBeVisible();
  await expect(page.getByText("Polarisation", { exact: true })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Matériau couche 1" })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Source de données couche 1" })).toBeVisible();

  await page.getByRole("button", { name: /Calculer la réponse optique/ }).click();
  await expect(page.getByRole("heading", { name: "Simulation calculée" })).toBeVisible();
  await expect(page.getByText(/valeur\(s\) TMM calculée\(s\)/)).toBeVisible();
  await expect(page.getByText("RÉFLECTANCE · R", { exact: true })).toBeVisible();

  const jsonDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: /Exporter JSON reproductible/ }).click();
  const jsonFile = await (await jsonDownload).path();
  expect(jsonFile).not.toBeNull();
  const json = JSON.parse(await readFile(jsonFile!, "utf8")) as {
    export_schema_version: string;
    result: { status: string; points: unknown[] };
    interpretation: string;
  };
  expect(json.export_schema_version).toBe("1.0");
  expect(json.result.status).toBe("computed");
  expect(json.result.points.length).toBeGreaterThan(0);
  expect(json.interpretation).toContain("semi-infinite exit substrate");

  const csvDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: /Exporter CSV spectral/ }).click();
  const csvFile = await (await csvDownload).path();
  expect(csvFile).not.toBeNull();
  const csv = await readFile(csvFile!, "utf8");
  expect(csv).toContain("wavelength_nm");
  expect(csv).toContain("T_interpretation");
  expect(csv).toContain("semi-infinite exit substrate");
});
