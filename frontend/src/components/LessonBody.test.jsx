import { render, screen } from "@testing-library/react";
import LessonBody, { groupBlocks } from "./LessonBody.jsx";

test("groups consecutive list items and keeps ordered/unordered apart", () => {
  const g = groupBlocks([
    { t: "li", text: "a", ordered: true },
    { t: "li", text: "b", ordered: true },
    { t: "li", text: "c", ordered: false },
    { t: "p", text: "after" },
  ]);
  expect(g.map((b) => b.t)).toEqual(["list", "list", "p"]);
  expect(g[0].items).toEqual(["a", "b"]);
  expect(g[0].tag).toBe("ol");
  expect(g[1].tag).toBe("ul");
});

test("renders headings, tables and escapes text instead of injecting HTML", () => {
  render(
    <LessonBody
      blocks={[
        { t: "h", level: 3, text: "Activity 1" },
        { t: "p", text: "<img src=x onerror=alert(1)>" },
        { t: "table", rows: [["Name", "Age"], ["Emma", "10"]] },
      ]}
    />,
  );
  expect(screen.getByRole("heading", { name: "Activity 1" })).toBeInTheDocument();
  expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
  expect(document.querySelector("img")).toBeNull();
  expect(screen.getByText("Emma")).toBeInTheDocument();
});
