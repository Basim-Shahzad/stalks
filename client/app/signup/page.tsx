"use client";

import { useState } from "react";
import { Button, Input, Label } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import styles from "../../styles/Signup.module.css";
import Divider from "@/components/Divider";
import { GoogleIcon } from "@/components/GoogleIcon";
import { useAuth } from "@/hooks/useAuth";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

const Signup = () => {
   const router = useRouter();
   const [name, setName] = useState<string>("");
   const [email, setEmail] = useState<string>("");
   const [password, setPassword] = useState<string>("");

   const { mutate: signup, isPending } = useMutation({
      mutationFn: (data: { name: string; email: string; password: string; isActive: true }) => useAuth.signup(data),
      mutationKey: ["signup"],
      onSuccess: () => {
         router.push("/portfolio");
      },
   });

   return (
      <div className="bg-black h-screen relative">
         <nav className="flex items-center gap-1.5 px-6 py-3">
            <Image src="/logo.png" alt="Stalks Logo" width={48} height={48} className="select-none" />
            <h1 className="text-[33px] font-medium tracking-tight text-white antialiased select-none">Stalks</h1>
         </nav>

         {/* Background atmosphere - using CSS module for complex gradients */}
         <div className={styles.heroGlow} />

         <div className="flex items-center justify-center">
            <div className="mt-6 flex flex-col items-center w-full max-w-xl shadow-2xl bg-black/25 z-50 min-h-[37rem] rounded-4xl p-12">
               <h1 className="text-3xl flex justify-center font-semibold text-white text-center">
                  Start tracking your <br />
                  first portfolio in minutes.
               </h1>

               <div className="flex min-w-full mt-8">
                  <Button className="w-full" variant="tertiary">
                     <GoogleIcon />
                     Sign in with Google
                  </Button>
               </div>

               <Divider />

               <div className="flex flex-col gap-2.5 w-full">
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-white/60">Username</Label>
                     <Input
                        className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                        type="text"
                        onChange={(e) => setName(e.target.value)}
                        value={name}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-white/60">Email</Label>
                     <Input
                        className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                        type="email"
                        onChange={(e) => setEmail(e.target.value)}
                        value={email}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-white/60">Password</Label>
                     <Input
                        className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                        type="password"
                        onChange={(e) => setPassword(e.target.value)}
                        value={password}
                        required
                     />
                  </div>
               </div>

               <Button
                  className="w-full mt-6"
                  variant="tertiary"
                  type="submit"
                  isPending={isPending}
                  onClick={() => signup({ name, email, password, isActive: true })}>
                  Sign up
               </Button>

               <Link href="/login" className="text-center text-sm text-[#22D07A] mt-4 hover:underline">
                  Already have an account? Log in
               </Link>
            </div>
         </div>
      </div>
   );
};

export default Signup;
