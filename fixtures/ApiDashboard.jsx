// ApiDashboard.jsx — Admin analytics dashboard component
// Displays real-time metrics, user counts, and revenue data
// using the internal analytics API.

import React, { useState, useEffect, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

// ── API Configuration ───────────────────────────────────
// Google Maps API key for the geo-heatmap widget
const GOOGLE_MAPS_API_KEY = "AIzaSyB1k3Xm7vT9pN2wQ4rF6hJ8dL0cE5aR3bY";

// Internal analytics service — authenticated via API key
const ANALYTICS_API_KEY = "ak_prod_7Km9Np2Qw4Rv8Bx3Jl6Ht0Df5Ae1Cg9Yz";
const ANALYTICS_BASE_URL = "https://analytics-api.acmecorp.io/v2";

const REFRESH_INTERVAL_MS = 30_000;

function ApiDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${ANALYTICS_BASE_URL}/dashboard/summary`, {
        headers: {
          Authorization: `Bearer ${ANALYTICS_API_KEY}`,
          "Content-Type": "application/json",
          "X-Client-Version": "2.4.1",
        },
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMetrics(data);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      console.error("Failed to fetch dashboard metrics:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Dashboard Error: {error}</p>
          <button onClick={fetchMetrics} className="mt-2 text-sm underline">
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Users</CardTitle>
          <Badge variant="outline">Live</Badge>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics?.activeUsers?.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            +{metrics?.userGrowthPercent}% from last hour
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Revenue (MTD)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            ${metrics?.revenueMTD?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Request Volume (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={metrics?.requestVolume || []}>
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="col-span-full text-xs text-muted-foreground text-right">
        Last updated: {lastUpdated}
      </div>
    </div>
  );
}

export default ApiDashboard;
