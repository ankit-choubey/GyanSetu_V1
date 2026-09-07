import React, { Suspense } from "react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<div className="py-8 text-center text-xs text-slate-400">Loading authentication...</div>}>
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}

