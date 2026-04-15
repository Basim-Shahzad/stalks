import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

const uploadFile = async (file: File) => {
   const formData = new FormData();
   formData.append("file", file);

   const res = await axios.post("http://localhost:5000/transactions", formData);

   return res.data;
};

export const useTransactionsFromPDF = () => {
   const queryClient = useQueryClient();

   return useMutation({
      mutationFn: uploadFile,
      onSuccess: () => {
         queryClient.invalidateQueries({ queryKey: ["transactions"] });
      },
   });
};
