export function getPriceChange(minBuy: number, currentPrice: number): string {
   if (minBuy === 0) return "0%"; // Avoid blowing up the universe

   const difference = ((currentPrice - minBuy) / minBuy) * 100;

   return difference.toFixed(2) + "%";
}

export function isSellTime(buyPrice: number, currentPrice: number): boolean {
   if (buyPrice * 1.3 >= currentPrice) {
      return true
   }
   return false
}