import Image from "next/image";
import React from "react";

const AuthLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <main className="h-screen flex flex-col">
      <header className="p-4 ">
        <Image src={"/next.svg"} alt="Logo" width={100} height={100} />
      </header>
      {children}
    </main>
  );
};

export default AuthLayout;
