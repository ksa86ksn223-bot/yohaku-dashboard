// Web Crypto API — Edge Runtime (middleware) and Node.js both supported

const COOKIE_NAME = "yohaku_session";

function getSecret(): string {
  return process.env.DASHBOARD_SECRET ?? "dev-secret";
}

async function getKey(secret: string): Promise<CryptoKey> {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

function bufToHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function generateToken(payload: string): Promise<string> {
  const key = await getKey(getSecret());
  const enc = new TextEncoder();
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  const sigHex = bufToHex(sig);
  return btoa(`${payload}:${sigHex}`)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export async function verifyToken(token: string): Promise<boolean> {
  try {
    const padded = token.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = atob(padded);
    const lastColon = decoded.lastIndexOf(":");
    if (lastColon === -1) return false;
    const payload = decoded.slice(0, lastColon);
    const sigHex = decoded.slice(lastColon + 1);
    const sigBytes = Uint8Array.from(
      sigHex.match(/.{2}/g)!.map((h) => parseInt(h, 16))
    );
    const key = await getKey(getSecret());
    const enc = new TextEncoder();
    return crypto.subtle.verify("HMAC", key, sigBytes, enc.encode(payload));
  } catch {
    return false;
  }
}

export { COOKIE_NAME };
