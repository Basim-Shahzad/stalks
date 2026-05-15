export interface Portfolio {
   id: string;
   exchange: "NYSE" | "NASDAQ" | "PSX" | "TADAWUL";
   currency: string;
   name: string;
   description: string;
   createdAt: string;
   updatedAt: string;
}

export type PortfolioList = Portfolio[];
