// THE WORLD TODAY — news-image-20261124 entry point.
//
// The front page is drawn ahead of time by render.py into entry.png.
// This program only proves the PNG is whole and within the bounty
// limits (1024x1024, at most 1 MiB, every chunk CRC valid) and then
// places it where the harness asks via $MAKEFUN_OUTPUT_DIR.
//
// The PNG is located next to this script, never relative to the
// process working directory: the grader may invoke the program from
// any directory, so the script's own directory is the anchor.

import { crc32 } from "node:zlib";
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SOURCE_PNG = join(HERE, "entry.png");
const MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const SIDE = 1024;
const CAP = 1024 * 1024;

function abort(why: string): never {
  console.error(`entry check failed: ${why}`);
  process.exit(1);
}

function inspect(png: Buffer): void {
  if (png.length < 8 || !png.subarray(0, 8).equals(MAGIC)) {
    abort("not a PNG file (bad signature)");
  }
  if (png.length > CAP) {
    abort(`entry.png is ${png.length} bytes, over the 1 MiB cap`);
  }
  let cursor = 8;
  let headerSeen = false;
  let endSeen = false;
  while (cursor + 12 <= png.length) {
    const payloadLen = png.readUInt32BE(cursor);
    const kind = png.toString("ascii", cursor + 4, cursor + 8);
    const payloadEnd = cursor + 8 + payloadLen;
    if (payloadEnd + 4 > png.length) {
      abort(`chunk ${kind} runs past the end of the file`);
    }
    const storedCrc = png.readUInt32BE(payloadEnd);
    const realCrc = crc32(png.subarray(cursor + 4, payloadEnd));
    if (storedCrc !== realCrc) {
      abort(`chunk ${kind} has a bad CRC`);
    }
    if (kind === "IHDR") {
      headerSeen = true;
      const width = png.readUInt32BE(cursor + 8);
      const height = png.readUInt32BE(cursor + 12);
      const bitDepth = png[cursor + 16];
      const colourKind = png[cursor + 17];
      if (width !== SIDE || height !== SIDE) {
        abort(`image is ${width}x${height}, expected ${SIDE}x${SIDE}`);
      }
      if (bitDepth !== 8 || (colourKind !== 2 && colourKind !== 6)) {
        abort(`unexpected PNG colour setup (depth ${bitDepth}, type ${colourKind})`);
      }
    }
    cursor = payloadEnd + 4;
    if (kind === "IEND") {
      endSeen = true;
      break;
    }
  }
  if (!headerSeen) {
    abort("no IHDR chunk found");
  }
  if (!endSeen) {
    abort("no IEND chunk — file is truncated");
  }
}

if (!existsSync(SOURCE_PNG)) {
  abort(`missing ${SOURCE_PNG} — run render.py first`);
}
if (!statSync(SOURCE_PNG).isFile()) {
  abort(`${SOURCE_PNG} is not a regular file`);
}
const image = readFileSync(SOURCE_PNG);
inspect(image);

const targetDir = process.env.MAKEFUN_OUTPUT_DIR ?? join(HERE, "output");
mkdirSync(targetDir, { recursive: true });
const target = join(targetDir, "entry.png");
copyFileSync(SOURCE_PNG, target);
const copied = readFileSync(target);
if (!copied.equals(image)) {
  abort("copied entry.png differs from the source");
}
console.log(`entry.png OK: 1024x1024, ${image.length} bytes -> ${target}`);
