import { Input, Label, Button } from "@heroui/react";
import { Modal, ModalHeader, ModalBody, ModalContainer, ModalFooter, ModalTrigger, ModalBackdrop } from "@heroui/react";
import { Settings as SettingsIcon } from "lucide-react";
import { useSettings } from "../hooks/useSettings";

const Settings = () => {
   const { increaseByPercInSell, setIncreaseByPercInSell } = useSettings();

   // Handle the change using the standard React ChangeEvent
   const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      const numValue = parseFloat(val);

      // Update the state with the number, or 0 if the input is cleared
      if (!isNaN(numValue)) {
         setIncreaseByPercInSell(numValue);
      } else if (val === "") {
         setIncreaseByPercInSell(0);
      }
   };

   return (
      <Modal>
         <ModalTrigger>
            <Button variant="ghost">
               <SettingsIcon className="w-6 h-6" />
            </Button>
         </ModalTrigger>

         <ModalBackdrop className="bg-[#f9f9f9]">
            <ModalContainer size="cover">
               <Modal.Dialog>
                  <ModalHeader className="border-b border-gray-200 mb-5 pb-[15px]">
                     <span style={{ fontSize: "1.25rem", letterSpacing: "1px", fontWeight: 600 }}>SETTINGS</span>
                  </ModalHeader>

                  <ModalBody>
                     <div className="flex flex-col gap-6">
                        <div className="bg-white border border-gray-200 p-4 rounded-xl shadow-sm">
                           <Label className="mr-2">Sell Threshold Increase (%) </Label>
                           <Input
                              type="number"
                              placeholder="0.00"
                              variant="secondary"
                              value={increaseByPercInSell}
                              onChange={handleChange}
                              step={0.01}
                              min={0}
                              max={100}
                           />
                           <p className="text-xs text-gray-500 mt-2">
                              The minimum % gain required to suggest a sell
                           </p>
                        </div>
                     </div>
                  </ModalBody>
                  <ModalFooter>
                     <Button slot="close" variant="secondary">
                        Close
                     </Button>
                  </ModalFooter>
               </Modal.Dialog>
            </ModalContainer>
         </ModalBackdrop>
      </Modal>
   );
};

export default Settings