import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn routing="hash" afterSignInUrl="/dashboard" />
    </div>
  );
}