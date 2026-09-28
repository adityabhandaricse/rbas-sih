import { useState, useMemo, useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { structureLoan } from "../api/client";
import { useQuery } from "@tanstack/react-query";

const COLORS = ["#D4A62A", "#1F4D3C"];

// Deterministic instant local fallback calculator (90:10 SCA model)
function computeLocalLoan(marginVal) {
  const totalCost = Math.round(marginVal / 0.10);
  const loanAmt = Math.round(totalCost * 0.90);
  const rate = 8.0;
  const tenureYears = 5;

  const r = rate / 100 / 12;
  const n = tenureYears * 12;
  const emi =
    r > 0 && n > 0
      ? Math.round((loanAmt * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1))
      : Math.round(loanAmt / n);

  // Generate a matching 5-year repayment schedule
  const schedule = [];
  let balance = loanAmt;
  const yearlyPayment = emi * 12;

  for (let yr = 1; yr <= tenureYears; yr++) {
    const interest = Math.round(balance * (rate / 100));
    let principal = Math.round(yearlyPayment - interest);
    if (principal > balance || yr === tenureYears) {
      principal = balance;
      balance = 0;
    } else {
      balance = Math.round(balance - principal);
    }
    schedule.push({
      year: `Year ${yr}`,
      period: `Yr ${yr}`,
      principal,
      interest,
      closing_balance: balance,
    });
  }

  return {
    margin_capital: marginVal,
    total_project_cost: totalCost,
    loan_amount: loanAmt,
    monthly_emi: emi,
    interest_rate_pa: rate,
    tenure_years: tenureYears,
    moratorium_months: 6,
    amortization_schedule: schedule,
    scheme_name: "Rural Priority Micro-Credit (SCA)",
  };
}

export default function FinancialCalculatorWidget({ onStructureChange }) {
  const [margin, setMargin] = useState(100000);

  // Instant local calculation ensures zero UI lag
  const localLoan = useMemo(() => computeLocalLoan(margin), [margin]);

  // Network query for backend-validated loan structuring
  const { data: serverLoan, isFetching } = useQuery({
    queryKey: ["structure-loan", margin],
    queryFn: () => structureLoan(margin),
    staleTime: 60000,
  });

  // Prefer server data if available, otherwise fall back to instant local math
  const loan = serverLoan || localLoan;

  // Modern React Query pattern to notify parent component safely
  useEffect(() => {
    if (loan && typeof onStructureChange === "function") {
      onStructureChange(loan);
    }
  }, [loan, onStructureChange]);

  const pieData = useMemo(
    () => [
      { name: "Your margin (10%)", value: Number(loan.margin_capital || margin) },
      { name: "Bank loan (90%)", value: Number(loan.loan_amount || loan.margin_capital * 9) },
    ],
    [loan, margin]
  );

  // Normalize amortization data keys to handle both backend and local formats
  const chartSchedule = useMemo(() => {
    const raw = loan.amortization_schedule || [];
    return raw.map((item, idx) => ({
      period: item.period || item.year || (item.quarter ? `Q${item.quarter}` : `Yr ${idx + 1}`),
      principal: Number(item.principal || 0),
      interest: Number(item.interest || 0),
    }));
  }, [loan.amortization_schedule]);

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm space-y-4">
      <div class="panel">
        <h2><span class="step-num">2</span><span data-i18n="wizard_title">Financial Structure</span></h2></div>
      <div className="flex items-center justify-between">
        <label className="block text-xs font-semibold uppercase tracking-wide text-forest-dk">
          Available Margin Capital — ₹{margin.toLocaleString("en-IN")}
        </label>
        {isFetching ? (
          <span className="text-[10px] text-gray-500 font-mono">Syncing...</span>
        ) : (
          <span className="text-[10px] text-forest-dk font-mono font-semibold bg-[#efe8d6] px-2 py-0.5 rounded">
            90:10 SCA Structuring
          </span>
        )}
      </div>

      <input
        type="range"
        min={10000}
        max={500000}
        step={5000}
        value={margin}
        onChange={(e) => setMargin(Number(e.target.value))}
        className="w-full accent-wheat-dk cursor-pointer"
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
        <Stat
          label="Project Cost"
          value={`₹${Number(loan.total_project_cost || 0).toLocaleString("en-IN")}`}
        />
        <Stat
          label="Loan Amount (90%)"
          value={`₹${Number(loan.loan_amount || 0).toLocaleString("en-IN")}`}
        />
        <Stat
          label="Monthly EMI"
          value={`₹${Number(loan.monthly_emi || 0).toLocaleString("en-IN")}`}
        />
        <Stat
          label="Terms"
          value={`${loan.interest_rate_pa || 8}% • ${loan.tenure_years || 5} yrs`}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6 pt-4 border-t border-paper-dk">
        {/* Cost Allocation Pie */}
        <div className="h-56">
          <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2 text-center">
            Capital Ratio (Debt vs Equity)
          </h4>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={4}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(val) => [`₹${Number(val).toLocaleString("en-IN")}`, "Amount"]}
              />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Repayment Trajectory Bar Chart */}
        <div className="h-56">
          <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2 text-center">
            Repayment Trajectory (Principal vs Interest)
          </h4>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartSchedule} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <XAxis dataKey="period" fontSize={11} stroke="#6b7280" />
              <YAxis
                fontSize={10}
                stroke="#6b7280"
                tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
              />
              <Tooltip
                formatter={(val) => [`₹${Number(val).toLocaleString("en-IN")}`, ""]}
              />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Bar dataKey="principal" stackId="a" fill="#1F4D3C" name="Principal Paid" />
              <Bar dataKey="interest" stackId="a" fill="#D4A62A" name="Interest Serviced" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-paper border border-paper-dk rounded-lg p-3">
      <div className="text-[11px] uppercase tracking-wide text-soil/70 font-semibold">{label}</div>
      <div className="font-mono text-base font-bold text-forest-dk mt-1">{value}</div>
    </div>
  );
}