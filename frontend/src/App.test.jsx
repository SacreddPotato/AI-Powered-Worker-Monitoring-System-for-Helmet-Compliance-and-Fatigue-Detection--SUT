import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

vi.mock("./pages/LandingPage", () => ({ default: () => <h1>landing page</h1> }));
vi.mock("./pages/FeedsPage", () => ({ default: () => <h1>feeds page</h1> }));
vi.mock("./pages/AlertsPage", () => ({ default: () => <h1>alerts page</h1> }));
vi.mock("./pages/ModelsPage", () => ({ default: () => <h1>models page</h1> }));
vi.mock("./pages/DevLabPage", () => ({ default: () => <h1>devlab page</h1> }));

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );
}

describe("App routes", () => {
  afterEach(() => cleanup());

  it.each([
    ["/", "landing page"],
    ["/feeds", "feeds page"],
    ["/alerts", "alerts page"],
    ["/models", "models page"],
    ["/devlab", "devlab page"],
  ])("renders %s", (path, text) => {
    renderAt(path);
    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it("redirects unknown routes to landing", () => {
    renderAt("/does-not-exist");
    expect(screen.getByText("landing page")).toBeInTheDocument();
  });
});
