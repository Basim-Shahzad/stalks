import { createContext, type ReactNode, type Dispatch, type SetStateAction, useState } from "react";

interface SettingsContextType {
   increaseByPercInSell: number;
   setIncreaseByPercInSell: Dispatch<SetStateAction<number>>;
}

export const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
   const [increaseByPercInSell, setIncreaseByPercInSell] = useState<number>(1.3);

   return (
      <SettingsContext.Provider
         value={{
            increaseByPercInSell,
            setIncreaseByPercInSell,
         }}>
         {children}
      </SettingsContext.Provider>
   );
};
