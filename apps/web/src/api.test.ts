import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiBase, fetchMe, login, readToken, writeToken } from "./api";

describe("api helpers", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("defaults the API prefix", () => {
    expect(apiBase()).toBe("/api/v1");
  });

  it("stores a login token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify({ access_token: "tok-1" }),
      }),
    );
    const token = await login("engineer", "engineer-dev");
    expect(token).toBe("tok-1");
    writeToken(token);
    expect(readToken()).toBe("tok-1");
  });

  it("maps ForgeFlow error envelopes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: { code: "unauthenticated", message: "nope" } }),
      }),
    );
    await expect(login("x", "y")).rejects.toMatchObject({
      code: "unauthenticated",
      message: "nope",
    } satisfies Partial<ApiError>);
  });

  it("clears a stored token when a later request is 401", async () => {
    writeToken("stale-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: { code: "unauthenticated", message: "expired" } }),
      }),
    );
    await expect(fetchMe()).rejects.toMatchObject({ code: "unauthenticated" });
    expect(readToken()).toBeNull();
  });
});
