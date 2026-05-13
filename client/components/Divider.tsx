const Divider = () => {
   return (
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 w-full py-4">
         <div className="h-px bg-gray-300/10"></div>
         <span className="text-[#22D07A] font-semibold text-sm uppercase tracking-wider">OR</span>
         <div className="h-px bg-gray-300/10"></div>
      </div>
   );
};

export default Divider;