"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Zap } from "lucide-react";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo1234");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.auth.login(email, password);
      const { access_token } = res.data;
      // Decode JWT to get user info (simplified)
      const payload = JSON.parse(atob(access_token.split(".")[1]));
      setAuth(
        { id: payload.sub, email, full_name: "Demo User", role: payload.role || "developer", organization_id: payload.org },
        access_token,
        payload.org || "00000000-0000-0000-0000-000000000001"
      );
      router.push("/dashboard");
    } catch {
      toast.error("Invalid credentials. Use demo@example.com / demo1234");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 shadow-lg">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI Cost Intelligence</h1>
          <p className="mt-1 text-sm text-gray-500">Sign in to your platform</p>
        </div>

        <div className="rounded-2xl border bg-white p-8 shadow-xl">
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@company.com" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <div className="mt-6 rounded-lg bg-blue-50 p-3 text-xs text-blue-700">
            <strong>Demo credentials:</strong><br />
            Email: demo@example.com | Password: demo1234
          </div>
        </div>
      </div>
    </div>
  );
}
