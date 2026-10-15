import { afterEach, describe, expect, it, vi } from "vitest";
import { getApiHealth } from "./api";

describe("getApiHealth", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns the API health payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }),
    );

    await expect(getApiHealth()).resolves.toEqual({ status: "ok" });
  });

  it("surfaces non-success API responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    );

    await expect(getApiHealth()).rejects.toThrow(
      "API health check failed: 503",
    );
  });
});
