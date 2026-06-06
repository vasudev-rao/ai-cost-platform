"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";

export default function ProjectsPage() {
  return (
    <AppShell title="Projects">
      <Card>
        <CardContent className="py-16 text-center text-muted-foreground text-sm">
          Projects management coming soon. Use the API endpoints directly for now.
        </CardContent>
      </Card>
    </AppShell>
  );
}
