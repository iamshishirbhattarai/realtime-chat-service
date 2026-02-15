import AuthLayout from "@/src/features/auth/ui/AuthLayout";
import React from "react";

const Layout = ({ children }: { children: React.ReactNode }) => {
  return <AuthLayout>{children}</AuthLayout>;
};

export default Layout;
