
const supportedExchanges = ["PSX"] as const;
const supportedCurrencies = ["PKR"] as const;
const supportedBrokers = ["AKD", "MMK"] as const;

export interface Portfolio {
   id: string;
   exchange: typeof supportedExchanges[number];
   currency: typeof supportedCurrencies[number];
   name: string;
   description: string;
   broker: typeof supportedBrokers[number];
   createdAt: string;
   updatedAt: string;
}

export type PortfolioList = Portfolio[];

export type PortfolioHolding = {
   symbol: string;
   company: string;
   sector: string;
   quantity: string;
   avgCost: string;
   totalInvested: string;
   totalFees: string;
   currentPrice: string;
   ldcp: string;
   dayChange: string;
   dayChange_pct: string;
   direction: string;
   marketValue: string;
   costBasis: string;
   unrealisedPnl: string;
   unrealisedPnlPct: string;
   realisedPnl: string;
   totalPnl: string;
}

export type PortfolioHoldingsSummary = {
   totalInvested: string;
   totalMarketValue: string;
   totalCostBasis: string;
   totalFees: string;
   totalUnrealisedPnl: string;
   totalRealisedPnl: string;
   totalPnl: string;
   totalPnlPct: string;
   holdingsCount: number;
}

export interface PortfolioHoldingsResponse {
   holdings: PortfolioHolding[];
   summary: PortfolioHoldingsSummary;
}
   