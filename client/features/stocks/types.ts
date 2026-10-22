// {
//   "exchange": "string",
//   "symbol": "string",
//   "rows": 0,
//   "data": [
//     {
//       "date": "2026-09-18",
//       "open": 0,
//       "high": 0,
//       "low": 0,
//       "close": 0,
//       "volume": 0
//     }
//   ]

export interface MarketDataResponse {
   exchange: string;
   symbol: string;
   rows: number;
   data: Data[];
}

interface Data {
   date: string;
   open: number;
   high: number;
   low: number;
   close: number;
   volume: number;
}
