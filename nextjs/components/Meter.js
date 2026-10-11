// A thin progress bar: marigold ("hot") from 80% full. `value` is between 0 and 1.
export default function Meter({ value, large = false }) {
  const pct = Math.max(0, Math.min(1, value || 0));
  return (
    <span className={"meter" + (large ? " lg" : "") + (pct >= 0.8 ? " hot" : "")}>
      <span style={{ width: Math.round(pct * 100) + "%" }}></span>
    </span>
  );
}
