import { isSessionExpired, messageFrom } from "./api.js";
import { safeNext } from "./pages/Login.jsx";

test("extracts readable messages from DRF error shapes", () => {
  expect(messageFrom({ error: "Nope" }, 400)).toBe("Nope");
  expect(messageFrom({ email: ["Taken."], password: ["Too short.", "Too common."] }, 400)).toBe("Taken. Too short. Too common.");
  expect(messageFrom({ detail: "Request was throttled." }, 429)).toMatch(/Too many attempts/);
  expect(messageFrom(null, 500)).toMatch(/Something went wrong/);
});

test("safeNext only allows same-site paths", () => {
  expect(safeNext("/courses/excel/l2")).toBe("/courses/excel/l2");
  expect(safeNext("//evil.com")).toBe("/dashboard");
  expect(safeNext("https://evil.com")).toBe("/dashboard");
  expect(safeNext(null)).toBe("/dashboard");
});

test("recognises an expired login but not other 403s", () => {
  expect(isSessionExpired(403, { detail: "Authentication credentials were not provided." })).toBe(true);
  expect(isSessionExpired(403, { error: "Finish all lessons before paying for the certificate." })).toBe(false);
  expect(isSessionExpired(403, { detail: "CSRF Failed: token missing." })).toBe(false);
  expect(isSessionExpired(400, { detail: "Authentication credentials were not provided." })).toBe(false);
});
