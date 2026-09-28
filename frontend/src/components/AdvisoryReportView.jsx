import SwotMatrix from "./SwotMatrix";

export default function AdvisoryReportView({ report }) {
  if (!report) return null;

  // Support both schema naming conventions
  const pricing = report.pricing_strategy || report.suggested_pricing_strategy || {};
  const schedule = report.amortization_schedule || [];
  const totalCost = Number(report.total_project_cost || 0);
  const debt = Number(report.loan_amount || 0);
  const equity = Number(report.margin_capital || 0);

  // Compute percentages for dynamic bar rendering
  const debtPct = totalCost > 0 ? Math.round((debt / totalCost) * 100) : 90;
  const equityPct = totalCost > 0 ? Math.round((equity / totalCost) * 100) : 10;

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6 space-y-6 shadow-sm">
      {/* 1. Market Reach */}
      <div>
        <h3 className="font-display text-lg text-forest-dk mb-1">Market Reach & Opportunity</h3>
        <p className="text-sm text-gray-700 leading-relaxed">{report.market_reach_summary}</p>
        
        {report.opportunity_analysis && report.opportunity_analysis.length > 0 && (
          <ul className="mt-2 list-disc pl-5 text-xs text-gray-600 space-y-1">
            {report.opportunity_analysis.map((opp, idx) => (
              <li key={idx}>{opp}</li>
            ))}
          </ul>
        )}
      </div>

      {/* 2. Visual Capital Outlay Breakdown (Pie / Ratio Bar) */}
      <div className="bg-paper border border-paper-dk rounded-xl p-5 space-y-3">
        <div className="flex justify-between items-center">
          <h4 className="font-display text-base font-semibold text-forest-dk">
            Capital Allocation & Means of Finance
          </h4>
          <span className="text-xs font-mono font-bold text-gray-600">
            Total: ₹{totalCost.toLocaleString("en-IN")}
          </span>
        </div>

        {/* Visual Segmented Outlay Bar */}
        <div className="w-full bg-[#e4decb] h-6 rounded-full overflow-hidden flex shadow-inner">
          <div
            style={{ width: `${debtPct}%` }}
            className="bg-[#1F4D3C] text-[10px] text-white flex items-center justify-center font-bold tracking-wider transition-all duration-500"
            title={`SCA Institutional Term Loan: ₹${debt.toLocaleString("en-IN")}`}
          >
            SCA Term Debt ({debtPct}%)
          </div>
          <div
            style={{ width: `${equityPct}%` }}
            className="bg-[#D4A62A] text-[10px] text-[#123028] flex items-center justify-center font-bold tracking-wider transition-all duration-500"
            title={`Promoter Margin Equity: ₹${equity.toLocaleString("en-IN")}`}
          >
            Margin ({equityPct}%)
          </div>
        </div>

        {/* Amount Legend */}
        <div className="flex justify-between items-center text-xs font-mono pt-1">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#1F4D3C] inline-block"></span>
            <span className="text-gray-700 font-semibold">
              Term Debt (90%): ₹{debt.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#D4A62A] inline-block"></span>
            <span className="text-gray-700 font-semibold">
              Promoter Equity (10%): ₹{equity.toLocaleString("en-IN")}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Qualitative SWOT Matrix */}
      <div>
        <h3 className="font-display text-lg text-forest-dk mb-2">Institutional SWOT Analysis</h3>
        <SwotMatrix report={report} />
      </div>

      {/* 4. Repayment Amortization Schedule */}
      {schedule.length > 0 && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="font-display text-lg text-forest-dk">Debt Amortization Schedule</h3>
            <span className="text-xs text-gray-500 font-mono">
              @ {report.interest_rate_pa || 8}% p.a. • {report.tenure_years || 5}Y
            </span>
          </div>

          <div className="overflow-x-auto border border-paper-dk rounded-lg">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-[#f7f3e8] text-gray-700 uppercase font-semibold border-b border-paper-dk">
                  <th className="py-2.5 px-3">Period</th>
                  <th className="py-2.5 px-3 text-right">Opening Balance</th>
                  <th className="py-2.5 px-3 text-right">Principal Repaid</th>
                  <th className="py-2.5 px-3 text-right">Interest Serviced</th>
                  <th className="py-2.5 px-3 text-right">Closing Debt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono">
                {schedule.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition">
                    <td className="py-2 px-3 font-sans font-medium text-gray-800">{row.year}</td>
                    <td className="py-2 px-3 text-right text-gray-600">
                      ₹{Number(row.opening_balance).toLocaleString("en-IN")}
                    </td>
                    <td className="py-2 px-3 text-right text-gray-600">
                      ₹{Number(row.principal).toLocaleString("en-IN")}
                    </td>
                    <td className="py-2 px-3 text-right text-gray-600">
                      ₹{Number(row.interest).toLocaleString("en-IN")}
                    </td>
                    <td className="py-2 px-3 text-right font-bold text-forest-dk">
                      ₹{Number(row.closing_balance).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. Pricing Strategy */}
      <div>
        <h3 className="font-display text-lg text-forest-dk mb-2">Suggested Pricing Strategy</h3>
        <div className="flex flex-wrap gap-2">
          {Object.keys(pricing).length > 0 ? (
            Object.entries(pricing).map(([tier, desc]) => (
              <div
                key={tier}
                className="bg-paper border border-paper-dk rounded-lg px-3 py-1.5 text-xs text-forest-dk"
              >
                <span className="font-bold uppercase tracking-wider text-forest-dk">{tier}: </span>
                <span className="text-gray-700">{desc}</span>
              </div>
            ))
          ) : (
            <p className="text-xs text-gray-500 italic">No specific tiered pricing provided.</p>
          )}
        </div>
      </div>

      {/* 6. Localized Risks */}
      <div>
        <h3 className="font-display text-lg text-forest-dk mb-1">Localized Risks & Mitigation</h3>
        <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
          {(report.localized_risks || []).map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}