export interface StockRow {
   Date: string;
   Company: string;
   Symbol: string;
   Buy: string;
   Rate: string;
   Commission: string;
   Taxes: string;
   Charges: string;
   "Total Amount": string;
   Sector: string;
}

export interface StockByApi {
   symbol: string; // The stock ticker (e.g., "AHCL")
   price: number; // Current trading price
   change: number; // Absolute price change
   changePercent: number; // Percentage change (represented as a decimal)
   high: number; // Daily high price
   low: number; // Daily low price
   volume: number; // Total number of shares traded
   value: number; // Total monetary value of trades
   trades: number; // Total number of transactions
   timestamp: number; // Unix timestamp (seconds)
   market: string; // Market segment (e.g., "REG" for Regular)
   st: string; // Stock status (e.g., "SUS" for Suspended)
   ask: number; // Best selling price
   askVol: number; // Quantity available at ask price
   bid: number; // Best buying price
   bidVol: number; // Quantity available at bid price
}