import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge variant="success">active</Badge>);
    expect(screen.getByText("active")).toBeTruthy();
  });

  it("applies severity classes", () => {
    const { container } = render(<Badge variant="critical">blocked</Badge>);
    expect(container.querySelector("span")?.className).toContain("bg-[#d03b3b]");
  });
});
