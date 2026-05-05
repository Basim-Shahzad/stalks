import React from "react";
import { Drawer, Input } from "@heroui/react";
import { useSettings } from "../hooks/useSettings";

const Settings = ({ opened, close }: any) => {
   const { increaseByPercInSell, setIncreaseByPercInSell } = useSettings();

   return (
      <Drawer isOpen={opened} onOpenChange={close} size="md" placement="right">
         <Drawer.Content className="bg-[#f9f9f9]">
            <Drawer.Header className="border-b border-gray-200 mb-5 pb-[15px]">
               <span style={{ fontSize: "1.25rem", letterSpacing: "1px", fontWeight: 600 }}>SETTINGS</span>
            </Drawer.Header>

            <Drawer.Body>
               <div className="flex flex-col gap-6">
                  <div className="bg-white border border-gray-200 p-4 rounded-xl shadow-sm">
                     <Input
                        type="number"
                        label="Sell Threshold Increase"
                        labelPlacement="outside"
                        placeholder="0.00"
                        description="The minimum % gain required to suggest a sell"
                        value={increaseByPercInSell.toString()}
                        onValueChange={(val) => setIncreaseByPercInSell(Number(val))}
                        step={0.01}
                        min={0}
                        max={100}
                        variant="flat"
                        endContent={
                           <div className="pointer-events-none flex items-center">
                              <span className="text-default-400 text-small">%</span>
                           </div>
                        }
                     />
                  </div>
               </div>
            </Drawer.Body>
         </Drawer.Content>
      </Drawer>
   );
};

export default Settings;
