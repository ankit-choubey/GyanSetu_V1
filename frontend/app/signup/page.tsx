import React, { Suspense } from "react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { SignupForm } from "@/components/auth/SignupForm";

export default function SignupPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<div className="py-8 text-center text-xs text-slate-400">Loading registration...</div>}>
        <SignupForm />
      </Suspense>
    </AuthLayout>
  );
}

