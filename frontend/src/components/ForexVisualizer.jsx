import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card";
import { Select } from "./ui/Select";
import { Button } from "./ui/Button";
import { Alert } from "./ui/Alert";

const CURRENCY_OPTIONS = [
  { value: "USD", label: "USD - US Dollar" },
  { value: "EUR", label: "EUR - Euro" },
  { value: "GBP", label: "GBP - British Pound" },
  { value: "INR", label: "INR - Indian Rupee" },
  { value: "JPY", label: "JPY - Japanese Yen" },
  { value: "AUD", label: "AUD - Australian Dollar" },
  { value: "CAD", label: "CAD - Canadian Dollar" },
  { value: "CHF", label: "CHF - Swiss Franc" },
  { value: "CNY", label: "CNY - Chinese Yuan" },
  { value: "NZD", label: "NZD - New Zealand Dollar" },
];

const PERIOD_OPTIONS = [
  { value: "1W", label: "1 Week" },
  { value: "1M", label: "1 Month" },
  { value: "3M", label: "3 Months" },
  { value: "6M", label: "6 Months" },
  { value: "1Y", label: "1 Year" },
];

export const ForexVisualizer = () => {
  const [fromCurrency, setFromCurrency] = useState("USD");
  const [toCurrency, setToCurrency] = useState("EUR");
  const [period, setPeriod] = useState("1W");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState([]);

  const fetchData = async () => {
    if (fromCurrency === toCurrency) {
      setError("To and From currencies cannot be the same");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:5000/api/forex-data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ from: fromCurrency, to: toCurrency, period }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError("Failed to fetch forex data. Please try again later.");
      console.error("Error fetching forex data:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <h1 className="text-4xl font-bold text-center">Forex Visualization</h1>

        <Card>
          <CardHeader>
            <CardTitle>Currency Selection</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Select
                label="From Currency:"
                value={fromCurrency}
                onChange={setFromCurrency}
                options={CURRENCY_OPTIONS}
                disabled={loading}
              />

              <Select
                label="To Currency:"
                value={toCurrency}
                onChange={setToCurrency}
                options={CURRENCY_OPTIONS}
                disabled={loading}
              />

              <Select
                label="Period:"
                value={period}
                onChange={setPeriod}
                options={PERIOD_OPTIONS}
                disabled={loading}
              />
            </div>

            <Button
              className="w-full mt-6"
              onClick={fetchData}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2" />
                  Loading...
                </>
              ) : (
                "Fetch and Render"
              )}
            </Button>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="ml-2">{error}</span>
          </Alert>
        )}

        <Card>
          <CardContent className="pt-6">
            <div className="relative h-[400px]">
              {loading && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center flex-col gap-4 z-50 rounded-lg">
                  <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
                  <p className="text-sm text-muted-foreground">
                    Loading data...
                  </p>
                </div>
              )}

              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis
                  domain={[
                      (dataMin) => Math.floor(dataMin * 0.995),
                      (dataMax) => Math.ceil(dataMax * 1.005),
                  ]}
                    tickFormatter={(value) => value.toFixed(2)}
                />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="exchange_rate"
                    stroke="#3498db"
                    strokeWidth={2}
                    dot={false}
                    name={`${fromCurrency} to ${toCurrency}`}
                  />
                </LineChart>
              </ResponsiveContainer>

            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
