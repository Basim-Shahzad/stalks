export interface User {
   id: string;
   name: string;
   email: string;
   isActive: boolean;
   createdAt: string;
   updatedAt: string;
}

export interface Tokens {
   accessToken: string;
   refreshToken: string;
   tokenType: string;
}