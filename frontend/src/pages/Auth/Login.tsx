import { Button, Input, Label } from "@heroui/react";
import { Link } from "react-router-dom";
import { FcGoogle } from "react-icons/fc";

const Divider = () => {
   return (
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 w-full py-4">
         <div className="h-[1px] bg-gray-300/10"></div>
         <span className="text-[#22D07A] font-semibold text-sm uppercase tracking-wider">OR</span>
         <div className="h-[1px] bg-gray-300/10"></div>
      </div>
   );
};

const LoginPage = () => {
   return (
      <>
         <style>{`
             /* ── background atmosphere ── */
            .hero-glow {
              position: absolute;
              inset: 0;
              pointer-events: none;
              z-index: 0;
            }
            .hero-glow::before {
              content: '';
              position: absolute;
              top: 0%;
              left: 50%;
              transform: translateX(-50%);
              width: 900px;
              height: 600px;
              background: radial-gradient(ellipse at center,
                rgba(34,208,122,0.08) 60%,
                rgba(59,130,26,0.05) 10%,
                transparent 70%);
              filter: blur(60px);
            }
            .hero-glow::after {
              content: '';
              position: absolute;
              bottom: 0;
              left: 0;
              right: 0;
              height: 40%;
              background: linear-gradient(to top, var(--bg), transparent);
            }
             `}</style>
         <div className="bg-black h-screen">
            <nav className="flex items-center gap-1.5 px-6 py-3">
               <img src="logo.png" className="w-12 select-none" />
               <h1 className="text-[33px] font-medium tracking-tight text-white antialiased select-none">Stalks</h1>
            </nav>
            <div className="hero-glow" />
            <div className="flex items-center justify-center">
               <div className="flex flex-col items-center justify-center w-1/3">
                  <h1 className="text-3xl flex justify-center font-semibold text-white text-center">Log in to Stalks</h1>

                  <div className="flex mt-8 w-full justify-center">
                     <Button className="w-full mt-2" variant="tertiary">
                        <FcGoogle className="w-5 h-5" />
                        Sign in with Google
                     </Button>
                  </div>

                  <Divider />
                  <div className="w-full flex flex-col gap-2.5">
                     <div className="flex flex-col gap-1 w-full">
                        <Label className="text-sm text-white/60">Email</Label>
                        <Input
                           className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                           placeholder="jane@example.com"
                           type="email"
                        />
                     </div>
                     <div className="flex flex-col gap-1 w-full">
                        <Label className="text-sm text-white/60">Password</Label>
                        <Input
                           className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                           placeholder="••••••••"
                           type="password"
                        />
                     </div>
                     <Link to="" className="text-center text-sm text-[#22D07A] mt-1 hover:underline">
                        Forgot password?
                     </Link>
                     <Button className="w-full mt-3" variant="tertiary">
                        Log in
                     </Button>
                  </div>
               </div>
            </div>
         </div>
      </>
   );
};

export default LoginPage;
