type HeaderProps = {
   title: string;
   right?: React.ReactNode;
};

const Header: React.FC<HeaderProps> = ({ title, right }) => {
   return (
      <header className="w-full px-8 py-4 flex items-center justify-between border-b border-b-white/5">
         <h1 className="text-xl">{title}</h1>
         {right ? right : null}
      </header>
   );
};

export default Header;
