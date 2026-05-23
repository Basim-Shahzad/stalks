"use client";

import { Button, Input, Label } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import { GoogleIcon } from "@/components/GoogleIcon";
import styles from "../../styles/Login.module.css";
import Divider from "@/components/Divider";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

const LoginPage = () => {
   const router = useRouter();
   const [email, setEmail] = useState<string>("");
   const [password, setPassword] = useState<string>("");

   const { mutate: login, isPending } = useMutation({
      mutationFn: (data: { email: string; password: string }) => useAuth.login(data),
      mutationKey: ["login"],
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

         <div className="flex items-center justify-center mt-20">
            <div className="flex flex-col items-center justify-center w-full max-w-md px-4">
               <h1 className="text-3xl flex justify-center font-semibold text-white text-center">Log in to Stalks</h1>

               <div className="flex mt-8 w-full justify-center">
                  <Button className="w-full mt-2" variant="tertiary">
                     <GoogleIcon />
                     Sign in with Google
                  </Button>
               </div>

               <Divider />

               <div className="w-full flex flex-col gap-2.5">
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-white/60">Email</Label>
                     <Input
                        className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-white/60">Password</Label>
                     <Input
                        className="w-full text-white bg-[#22D07A]/5 outline-none ring-0 border border-[#22D07A]/20"
                        placeholder="••••••••"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                     />
                  </div>
                  <Link href="/forgot-password" className="text-center text-sm text-[#22D07A] mt-1 hover:underline">
                     Forgot password?
                  </Link>
                  <Button
                     className="w-full mt-3"
                     variant="tertiary"
                     type="submit"
                     isPending={isPending}
                     onPress={() => login({ email, password })}>
                     {isPending ? "Logging in..." : "Log in"}
                  </Button>
               </div>
            </div>
         </div>
      </div>
   );
};

export default LoginPage;
