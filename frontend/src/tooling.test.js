import { describe, expect, test } from "vitest";
import packageJson from "../package.json";
import packageLock from "../package-lock.json";

const expectedDependencyMajors = {
  dependencies: {
    react: 18,
    "react-dom": 18,
    "react-router-dom": 7,
  },
  devDependencies: {
    "@tailwindcss/vite": 4,
    vite: 5,
    vitest: 3,
    jsdom: 27,
  },
};

function major(versionRange) {
  const match = versionRange.match(/\d+/);
  if (!match) throw new Error(`Could not parse version range: ${versionRange}`);
  return Number(match[0]);
}

describe("frontend tooling contract", () => {
  test("package contract stays private ESM with expected scripts", () => {
    expect(packageJson.private).toBe(true);
    expect(packageJson.type).toBe("module");
    expect(packageJson.scripts).toMatchObject({
      dev: "vite",
      build: "vite build",
      preview: "vite preview",
      test: "vitest",
    });
  });

  test("dependency major versions stay on approved lines", () => {
    for (const [section, packages] of Object.entries(expectedDependencyMajors)) {
      for (const [name, expectedMajor] of Object.entries(packages)) {
        expect(major(packageJson[section][name])).toBe(expectedMajor);
      }
    }
  });

  test("npm lockfile is committed and uses lockfile version 3", () => {
    expect(packageLock.name).toBe(packageJson.name);
    expect(packageLock.lockfileVersion).toBe(3);
  });
});
