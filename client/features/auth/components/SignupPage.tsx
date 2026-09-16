"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";
import Image from "next/image";
import styles from "./Signup.module.css";
import Divider from "./Divider";
import { GoogleIcon } from "./GoogleIcon";
import { useAuth } from "../api";
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
         router.push("/portfolios");
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

         <div className="flex items-center justify-center">
            <div className="mt-6 flex flex-col items-center w-full max-w-xl shadow-2xl bg-card/25 z-50 min-h-[37rem] rounded-4xl p-12">
               <h1 className="text-3xl flex justify-center font-semibold text-foreground text-center">
                  Start tracking your <br />
                  first portfolio in minutes.
               </h1>

               <div className="flex min-w-full mt-8">
                  <Button className="w-full" variant="secondary">
                     <GoogleIcon />
                     Sign in with Google
                  </Button>
               </div>

               <Divider />

               <div className="flex flex-col gap-2.5 w-full">
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-muted-foreground">Username</Label>
                     <Input
                        className="w-full text-foreground bg-primary/5 outline-none ring-0 border border-primary/20"
                        type="text"
                        onChange={(e) => setName(e.target.value)}
                        value={name}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-muted-foreground">Email</Label>
                     <Input
                        className="w-full text-foreground bg-primary/5 outline-none ring-0 border border-primary/20"
                        type="email"
                        onChange={(e) => setEmail(e.target.value)}
                        value={email}
                        required
                     />
                  </div>
                  <div className="flex flex-col gap-1 w-full">
                     <Label className="text-sm text-muted-foreground">Password</Label>
                     <Input
                        className="w-full text-foreground bg-primary/5 outline-none ring-0 border border-primary/20"
                        type="password"
                        onChange={(e) => setPassword(e.target.value)}
                        value={password}
                        required
                     />
                  </div>
               </div>

               <Button
                  className="w-full mt-6"
                  variant="secondary"
                  type="submit"
                  disabled={isPending}
                  onClick={() => signup({ name, email, password, isActive: true })}>
                  Sign up
               </Button>

               <Link href="/login" className="text-center text-sm text-primary mt-4 hover:underline">
                  Already have an account? Log in
               </Link>
            </div>
         </div>
      </div>
   );
};

export default Signup;
