import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

// Entry point for the news-image-20261124 bounty. The front page is
// drawn by render.py into entry.png; this program only checks that the
// PNG meets the bounty rules (1024x1024, at most 1 MiB, well-formed
// PNG with valid chunk CRCs) and copies it into the output directory
// the harness points at with $MAKEFUN_OUTPUT_DIR.

const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const EXPECTED_W = 1024;
const EXPECTED_H = 1024;
const MAX_BYTES = 1024 * 1024;

// CRC-32 (IEEE 802.3) table, built once at startup.
const CRC_TABLE: number[] = [];
for (let n = 0; n < 256; n++) {
  let c = n;
  for (let k = 0; k < 8; k++) {
    c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  }
  CRC_TABLE.push(c >>> 0);
}

function crc32(buf: Buffer): number {
  let c = 0xffffffff;
  for (const b of buf) {
    c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  }
  return (c ^ 0xffffffff) >>> 0;
}

function fail(msg: string): never {
  console.error(`entry check failed: ${msg}`);
  process.exit(1);
}

function checkPng(path: string): void {
  if (!existsSync(path)) {
    fail(`missing ${path} — run render.py first`);
  }
  const bytes = readFileSync(path);
  if (bytes.length > MAX_BYTES) {
    fail(`entry.png is ${bytes.length} bytes, over the 1 MiB cap`);
  }
  if (bytes.length < 8 || !bytes.subarray(0, 8).equals(PNG_SIG)) {
    fail("not a PNG file (bad signature)");
  }
  let off = 8;
  let sawIhdr = false;
  while (off + 12 <= bytes.length) {
    const len = bytes.readUInt32BE(off);
    const type = bytes.subarray(off + 4, off + 8).toString("ascii");
    const dataEnd = off + 8 + len;
    if (dataEnd + 4 > bytes.length) {
      fail(`chunk ${type} runs past the end of the file`);
    }
    const stored = bytes.readUInt32BE(dataEnd);
    const actual = crc32(bytes.subarray(off + 4, dataEnd));
    if (stored !== actual) {
      fail(`chunk ${type} has a bad CRC`);
    }
    if (type === "IHDR") {
      sawIhdr = true;
      const w = bytes.readUInt32BE(off + 8);
      const h = bytes.readUInt32BE(off + 12);
      const depth = bytes[off + 16];
      const colour = bytes[off + 17];
      if (w !== EXPECTED_W || h !== EXPECTED_H) {
        fail(`image is ${w}x${h}, expected ${EXPECTED_W}x${EXPECTED_H}`);
      }
      if (depth !== 8 || (colour !== 2 && colour !== 6)) {
        fail(`unexpected PNG colour setup (depth ${depth}, type ${colour})`);
      }
    }
    off = dataEnd + 4;
    if (type === "IEND") {
      break;
    }
  }
  if (!sawIhdr) {
    fail("no IHDR chunk found");
  }
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "./output";
checkPng("entry.png");
mkdirSync(outDir, { recursive: true });
const dest = join(outDir, "entry.png");
copyFileSync("entry.png", dest);
// Confirm the copy landed whole before reporting success.
const srcSize = statSync("entry.png").size;
const dstSize = statSync(dest).size;
if (dstSize !== srcSize) {
  fail(`copied entry.png is ${dstSize} bytes, expected ${srcSize}`);
}
console.log(`entry.png OK: 1024x1024, ${srcSize} bytes -> ${dest}`);
