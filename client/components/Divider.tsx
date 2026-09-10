const Divider = () => {
   return (
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 w-full py-4">
         <div className="h-px bg-border"></div>
         <span className="text-primary font-semibold text-sm uppercase tracking-wider">OR</span>
         <div className="h-px bg-border"></div>
      </div>
   );
};

export default Divider;