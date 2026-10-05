// Test-mode PromptPay QR code: a pattern made from a seed, always black on white (prototype: fakeQR).
// It is NOT a real QR code; the same seed always draws the same picture.
import { useMemo } from "react";

const N = 25; // 25 x 25 cells

function cellsFor(seed) {
  // FNV-1a hash of the seed, then xorshift random numbers: the same steps as the prototype
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  if (!h) h = 1;
  const rnd = () => {
    h ^= h << 13; h >>>= 0;
    h ^= h >>> 17;
    h ^= h << 5; h >>>= 0;
    return h / 4294967296;
  };
  const inFinder = (x, y) => (x < 8 && y < 8) || (x >= N - 8 && y < 8) || (x < 8 && y >= N - 8);
  const cells = [];
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      if (inFinder(x, y)) continue;
      if (rnd() < 0.47) cells.push([x, y]);
    }
  }
  return cells;
}

// The three big corner squares
function Finder({ x, y }) {
  return (
    <>
      <rect x={x} y={y} width="7" height="7" />
      <rect x={x + 1} y={y + 1} width="5" height="5" fill="#fff" />
      <rect x={x + 2} y={y + 2} width="3" height="3" />
    </>
  );
}

export default function FakeQR({ seed, small = false }) {
  const cells = useMemo(() => cellsFor(String(seed)), [seed]);
  return (
    <div className={"qr" + (small ? " small" : "")}>
      <svg viewBox={`-2 -2 ${N + 4} ${N + 4}`} role="img" aria-label="Test PromptPay QR code" shapeRendering="crispEdges">
        <rect x="-2" y="-2" width={N + 4} height={N + 4} fill="#fff" />
        <g fill="#101626">
          <Finder x={0} y={0} />
          <Finder x={N - 7} y={0} />
          <Finder x={0} y={N - 7} />
          {cells.map(([x, y]) => <rect key={x + "-" + y} x={x} y={y} width="1" height="1" />)}
        </g>
      </svg>
    </div>
  );
}
