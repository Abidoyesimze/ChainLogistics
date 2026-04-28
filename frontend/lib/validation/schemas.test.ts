import { describe, expect, it, vi } from "vitest";

import {
  formatFirstErrorMessage,
  productIdSchema,
  productRegistrationSchema,
  productSearchSchema,
  requiredString,
  stellarPublicKeySchema,
  transferProductSchema,
} from "@/lib/validation";

vi.mock("@stellar/stellar-sdk", async () => {
  const actual = await vi.importActual<typeof import("@stellar/stellar-sdk")>("@stellar/stellar-sdk");
  return {
    ...actual,
    StrKey: {
      ...actual.StrKey,
      isValidEd25519PublicKey: (val: string) => {
        if (val === "GBRPYHIL2CI3FN7YZXRLS62W3N5H3NVBUNNV3DPH3TSRY3OTYJ75SNCJ") return true;
        return actual.StrKey.isValidEd25519PublicKey(val);
      },
    },
  };
});

describe("validation schemas", () => {
  it("validates product ID format", () => {
    expect(productIdSchema.safeParse("SKU-123_ABC").success).toBe(true);
    expect(productIdSchema.safeParse("bad id").success).toBe(false);
    expect(productIdSchema.safeParse("*").success).toBe(false);
  });

  it("validates required strings", () => {
    const schema = requiredString("Name");
    expect(schema.safeParse("Coffee").success).toBe(true);
    expect(schema.safeParse("").success).toBe(false);
  });

  it("validates Stellar public key", () => {
    const valid = "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWHF";
    expect(stellarPublicKeySchema.safeParse(valid).success).toBe(true);

    expect(stellarPublicKeySchema.safeParse("not-a-key").success).toBe(false);
    expect(stellarPublicKeySchema.safeParse("SB".padEnd(56, "A")).success).toBe(false);
  });

  it("formats first available error message", () => {
    expect(formatFirstErrorMessage([undefined, "", "Bad value", "Other"])).toBe(
      "Bad value"
    );
    expect(formatFirstErrorMessage([undefined, null, "  "])).toBe("Invalid value");
  });

  describe("productRegistrationSchema", () => {
    it("should validate a correct registration payload", () => {
      const result = productRegistrationSchema.safeParse({
        id: "PROD-001",
        name: "Coffee Beans",
        origin: "Ethiopia",
        description: "Single origin coffee",
        category: "Food",
      });
      expect(result.success).toBe(true);
    });

    it("should reject invalid origin characters", () => {
      const result = productRegistrationSchema.safeParse({
        id: "PROD-001",
        name: "Coffee Beans",
        origin: "<script>",
        category: "Food",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("transferProductSchema", () => {
    it("should validate a correct transfer request", () => {
      const result = transferProductSchema.safeParse({
        productId: "PROD-001",
        recipientAddress: "GBRPYHIL2CI3FN7YZXRLS62W3N5H3NVBUNNV3DPH3TSRY3OTYJ75SNCJ",
      });
      expect(result.success).toBe(true);
    });

    it("should reject a missing recipient address", () => {
      const result = transferProductSchema.safeParse({ productId: "PROD-001" });
      expect(result.success).toBe(false);
    });

    it("should reject an invalid recipient Stellar address", () => {
      const result = transferProductSchema.safeParse({
        productId: "PROD-001",
        recipientAddress: "not-a-stellar-key",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("productSearchSchema", () => {
    it("should validate a normal search query", () => {
      const result = productSearchSchema.safeParse({ query: "laptop" });
      expect(result.success).toBe(true);
    });

    it("should reject an empty search query", () => {
      const result = productSearchSchema.safeParse({ query: "" });
      expect(result.success).toBe(false);
    });

    it("should reject a query with dangerous characters", () => {
      const result = productSearchSchema.safeParse({ query: "<script>alert(1)</script>" });
      expect(result.success).toBe(false);
    });
  });
});
