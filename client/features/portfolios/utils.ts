export const formatPKRFull = (value: number): string =>
   (Number(value) || 0).toLocaleString("en-PK", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   });

export const formatPKR = (val: number) => {
   const n = Number(val) || 0;
   if (n >= 1_000_000) return `PKR ${(n / 1_000_000).toFixed(2)}M`;
   if (n >= 1_000) return `PKR ${(n / 1_000).toFixed(2)}K`;
   return `PKR ${n.toFixed(2)}`;
};