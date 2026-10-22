"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import { GoogleIcon } from "./GoogleIcon";
import styles from "./Login.module.css";
import Divider from "./Divider";
import { useState } from "react";
import { useAuth } from "../api";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";

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
      onError: (error) => {
         const status = isAxiosError(error) ? error.response?.status : undefined;
         toast.error(status === 401 ? "Invalid email or password" : "Could not log in. Please try again.");
      },
   });

   return (
      <div className="bg-background h-screen relative">
         <nav className="flex items-center gap-1.5 px-6 py-3">
            <Image src="/logo.png" alt="Stalks Logo" width={48} height={48} className="select-none" />
            <h1 className="text-[33px] font-medium tracking-tight text-foreground antialiased select-none">Stalks</h1>
         </nav>

         {/* Background atmosphere - using CSS module for complex gradients */}
         <div className={styles.heroGlow} />

         <div className="flex items-center justify-center mt-20">
            <div className="flex flex-col items-center justify-center w-full max-w-md px-4">
               <h1 className="text-3xl flex justify-center font-semibold text-foreground text-center">Log in to Stalks</h1>

               <div className="flex mt-8 w-full justify-center">
                  <Button className="w-full mt-2" variant="secondary">
                     <GoogleIcon />
                     Sign in with Google
                  </Button>
               </div>

               <Divider />

               <form
                  className="w-full flex flex-col gap-2.5"
                  onSubmit={(e) => {
                     e.preventDefault();
                     login({ email, password });
                  }}
               >
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-muted-foreground">Email</Label>
                     <Input
                        className="w-full text-foreground bg-primary/5 outline-none ring-0 border border-primary/20"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-muted-foreground">Password</Label>
                     <Input
                        className="w-full text-foreground bg-primary/5 outline-none ring-0 border border-primary/20"
                        placeholder="••••••••"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                     />
                  </div>

                  <Link href="/forgot-password" className="text-center text-sm text-primary mt-1 hover:underline">
                     Forgot password?
                  </Link>
                  <Button
                     className="w-full mt-3"
                     variant="secondary"
                     type="submit"
                     disabled={isPending}
                  >
                     {isPending ? "Logging in..." : "Log in"}
                  </Button>
               </form>
            </div>
         </div>
      </div>
   );
};

export default LoginPage;
