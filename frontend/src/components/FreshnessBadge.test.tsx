import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { FreshnessBadge } from "./FreshnessBadge";

describe("FreshnessBadge", () => {
  it("renders nothing without a level", () => {
    const { container } = render(<FreshnessBadge level={undefined} />);
    expect(container.querySelector("span")).toBeNull();
  });

  it("renders each freshness level", () => {
    render(<FreshnessBadge level="fresh" />);
    expect(screen.getByText("fresh")).toBeTruthy();
    render(<FreshnessBadge level="aging" />);
    expect(screen.getByText("aging")).toBeTruthy();
    render(<FreshnessBadge level="stale" />);
    expect(screen.getByText("stale")).toBeTruthy();
    render(<FreshnessBadge level="unavailable" />);
    expect(screen.getByText("no data")).toBeTruthy();
  });

  it("prefers the backend message as tooltip when provided", () => {
    render(<FreshnessBadge level="stale" message="Data was last synchronized 10 days ago." />);
    const badge = screen.getByText("stale");
    expect(badge.getAttribute("title")).toBe("Data was last synchronized 10 days ago.");
  });

  it("falls back to the raw level when unknown", () => {
    render(<FreshnessBadge level="weird" />);
    expect(screen.getByText("weird")).toBeTruthy();
  });
});
