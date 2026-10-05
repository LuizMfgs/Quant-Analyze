export const pct = (v: number, digits = 1, signed = false) =>
  `${signed && v > 0 ? "+" : ""}${(v * 100).toFixed(digits)}%`;

export const usd = (v: number, digits = 2) =>
  v.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

export const num = (v: number, digits = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const shortDate = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
};
