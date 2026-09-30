import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProvenanceBadge } from "./ProvenanceBadge";

describe("ProvenanceBadge", () => {
  it("renders nothing for empty provenance", () => {
    const { container } = render(<ProvenanceBadge provenance="" />);
    expect(container.querySelector("span")).toBeNull();
    const { container: c2 } = render(<ProvenanceBadge provenance={null} />);
    expect(c2.querySelector("span")).toBeNull();
  });

  it("labels real connected data as fresh connected data", () => {
    render(<ProvenanceBadge provenance="REAL_CONNECTED_DATA" />);
    expect(screen.getByText("Connected data")).toBeTruthy();
  });

  it("warns on stale data", () => {
    render(<ProvenanceBadge provenance="STALE_DATA" />);
    expect(screen.getByText("Stale data")).toBeTruthy();
  });

  it("flags unavailable data as no data", () => {
    render(<ProvenanceBadge provenance="UNAVAILABLE_DATA" />);
    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("keeps the AI provider provenance labels", () => {
    render(<ProvenanceBadge provenance="REAL_AI_PROVIDER" />);
    expect(screen.getByText("AI provider")).toBeTruthy();
    render(<ProvenanceBadge provenance="MOCK_PROVIDER" />);
    expect(screen.getByText("Mock provider")).toBeTruthy();
  });

  it("falls back to the raw value for unknown provenance", () => {
    render(<ProvenanceBadge provenance="SOMETHING_NEW" />);
    expect(screen.getByText("SOMETHING_NEW")).toBeTruthy();
  });
});
