import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api";

export default function Status() {
  const [state, setState] = useState("checking");
  const [error, setError] = useState("");

  async function check() {
    setState("checking");
    setError("");

    try {
      await api("/health");
      setState("connected");
    } catch (err) {
      setError(err.message);
      setState("failed");
    }
  }

  useEffect(() => {
    check();
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>System status</CardTitle>
          <CardDescription>Checks the API and its database.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {state === "checking" && <p className="text-muted-foreground">Checking...</p>}
          {state === "connected" && (
            <p className="text-lg font-semibold text-green-600">Connected</p>
          )}
          {state === "failed" && (
            <div>
              <p className="text-lg font-semibold text-red-600">Not connected</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          )}

          <Button variant="outline" onClick={check} disabled={state === "checking"}>
            Check again
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
