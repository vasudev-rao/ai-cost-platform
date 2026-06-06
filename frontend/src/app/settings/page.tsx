"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <AppShell title="Settings">
      <Card>
        <CardContent className="py-16 text-center text-muted-foreground text-sm">
          Settings management coming soon. Use the API endpoints directly for now.
        </CardContent>
      </Card>
    </AppShell>
  );
}
