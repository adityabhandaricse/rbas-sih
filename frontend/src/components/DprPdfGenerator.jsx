import { useState } from "react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export default function DprPdfGenerator({ report }) {
  const [downloading, setDownloading] = useState(false);

  if (!report) return null;

  const village = report.village || report.village_name || "Enterprise";
  const block = report.block || report.block_name || "Block";
  const district = report.district || report.district_name || "District";
  const state = report.state || "India";
  const category = report.business_category || report.category || "Rural Enterprise";

  const totalCost = Number(report.total_project_cost || 0);
  const debtAmount = Number(report.loan_amount || 0);
  const marginEquity = Number(report.margin_capital || 0);
  const emi = Number(report.monthly_emi || 0);
  const interestRate = report.interest_rate_pa || 8.0;
  const tenureYears = report.tenure_years || 5;
  const moratorium = report.moratorium_months || 6;
  const schedule = report.amortization_schedule || [];
  const compCount = report.competitor_count ?? report.competitor_count_10km ?? 0;
  const saturation = report.saturation_level || "MODERATE";

  const sanctionSummary =
    report.bank_dpr_summary ||
    report.dpr_ready_summary ||
    `Proposed micro-enterprise for ${category} at ${village}, Block ${block}, District ${district} has a validated capital outlay of Rs. ${totalCost.toLocaleString(
      "en-IN"
    )}. Supported by promoter margin equity of Rs. ${marginEquity.toLocaleString(
      "en-IN"
    )} (10%) and recommended institutional debt of Rs. ${debtAmount.toLocaleString(
      "en-IN"
    )} (90%) under ${report.scheme_name || "Rural Priority Micro-Credit (SCA)"}. With a ${moratorium}-month moratorium, debt service coverage remains viable.`;

  const handleDownload = () => {
    try {
      setDownloading(true);

      const doc = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      // --- Header Brand Banner ---
      doc.setFillColor(31, 77, 60); // #1F4D3C (forest green)
      doc.rect(0, 0, 210, 24, "F");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(15);
      doc.setTextColor(255, 255, 255);
      doc.text("RBAS DETAILED PROJECT REPORT (DPR)", 14, 12);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(212, 166, 42); // #D4A62A (wheat gold)
      doc.text(
        `Priority Sector Rural Micro-Enterprise Feasibility Assessment | Date: ${new Date().toLocaleDateString("en-IN")}`,
        14,
        18
      );

      // --- Section 1: Enterprise Profile ---
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(31, 77, 60);
      doc.text("1. ENTERPRISE & GEOGRAPHIC PROFILE", 14, 32);

      autoTable(doc, {
        startY: 35,
        head: [["Profile Parameter", "Assessment Specification"]],
        body: [
          ["Proposed Sector / Activity", category],
          ["Location Hierarchy", `${village}, Block: ${block}, District: ${district}, ${state}`],
          ["10km Radial Saturation", `${compCount} Registered Outlets | Saturation Level: ${saturation}`],
          ["Scheme Delivery Model", report.scheme_name || "Rural Priority Micro-Credit (SCA 90:10 Structure)"],
        ],
        theme: "striped",
        headStyles: { fillColor: [31, 77, 60], textColor: [255, 255, 255], fontStyle: "bold", fontSize: 8 },
        bodyStyles: { fontSize: 8, cellPadding: 2 },
        margin: { left: 14, right: 14 },
      });

      // --- Section 2: Capital Outlay & Financing Means ---
      const nextY1 = doc.lastAutoTable.finalY + 8;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(31, 77, 60);
      doc.text("2. CAPITAL OUTLAY & MEANS OF FINANCING", 14, nextY1);

      autoTable(doc, {
        startY: nextY1 + 3,
        head: [["Capital Head", "Ratio (%)", "Financing Terms", "Amount (INR)"]],
        body: [
          ["Promoter Margin Contribution (Equity)", "10.0%", "Borrower Own Capital", `Rs. ${marginEquity.toLocaleString("en-IN")}`],
          ["Institutional Debt (SCA Term Loan)", "90.0%", `@ ${interestRate}% p.a. Concessional Rate`, `Rs. ${debtAmount.toLocaleString("en-IN")}`],
          ["Total Validated Project Outlay", "100.0%", "Fixed Capital + Working Outlay", `Rs. ${totalCost.toLocaleString("en-IN")}`],
          ["Monthly Debt Servicing (EMI)", "-", `${tenureYears} Years (${moratorium}M Moratorium)`, `Rs. ${emi.toLocaleString("en-IN")} / Month`],
        ],
        theme: "grid",
        headStyles: { fillColor: [18, 48, 40], textColor: [255, 255, 255], fontStyle: "bold", fontSize: 8 },
        bodyStyles: { fontSize: 8, cellPadding: 2 },
        margin: { left: 14, right: 14 },
      });

      // --- Section 3: Amortization Schedule ---
      let nextY2 = doc.lastAutoTable.finalY + 8;
      if (schedule.length > 0) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.setTextColor(31, 77, 60);
        doc.text("3. DEBT AMORTIZATION & REPAYMENT TRAJECTORY", 14, nextY2);

        const scheduleRows = schedule.map((row) => [
          row.year || row.period,
          `Rs. ${Number(row.opening_balance || 0).toLocaleString("en-IN")}`,
          `Rs. ${Number(row.principal || 0).toLocaleString("en-IN")}`,
          `Rs. ${Number(row.interest || 0).toLocaleString("en-IN")}`,
          `Rs. ${Number(row.closing_balance || 0).toLocaleString("en-IN")}`,
        ]);

        autoTable(doc, {
          startY: nextY2 + 3,
          head: [["Repayment Period", "Opening Debt", "Principal Paid", "Interest Serviced", "Closing Debt"]],
          body: scheduleRows,
          theme: "striped",
          headStyles: { fillColor: [40, 80, 65], textColor: [255, 255, 255], fontStyle: "bold", fontSize: 7.5 },
          bodyStyles: { fontSize: 7.5, cellPadding: 1.8 },
          margin: { left: 14, right: 14 },
        });

        nextY2 = doc.lastAutoTable.finalY + 8;
      }

      // --- Section 4: Appraisal Note ---
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(31, 77, 60);
      doc.text("4. INSTITUTIONAL LOAN APPRAISAL SUMMARY", 14, nextY2);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(50, 50, 50);
      const splitText = doc.splitTextToSize(sanctionSummary, 182);
      doc.text(splitText, 14, nextY2 + 5);

      // --- Section 5: Signatures ---
      const signY = nextY2 + 5 + splitText.length * 4 + 12;
      if (signY < 275) {
        doc.setDrawColor(180, 180, 180);
        doc.line(14, signY, 70, signY);
        doc.line(140, signY, 196, signY);

        doc.setFontSize(7.5);
        doc.setTextColor(100, 100, 100);
        doc.text("Applicant / Beneficiary Signature", 14, signY + 4);
        doc.text("Sanctioning Officer / SCA Appraiser", 140, signY + 4);
      }

      // Trigger instant direct download
      doc.save(`RBAS_DPR_${village.replace(/[^a-zA-Z0-9]/g, "_")}.pdf`);
    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("Failed to export DPR PDF. Please check the browser console.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-4 pt-2">
      {/* Download Action Button */}
      <button
        type="button"
        onClick={handleDownload}
        disabled={downloading}
        className="inline-flex items-center gap-2 bg-[#1F4D3C] hover:bg-[#123028] text-white font-bold px-6 py-2.5 rounded-lg text-sm transition shadow-sm disabled:opacity-50"
      >
        <span>📄</span>
        {downloading ? "Compiling Document..." : "Download Bank-Ready DPR (.pdf)"}
      </button>

      {/* Structured DPR Preview Card (Web UI Display) */}
      <div className="bg-white border border-[#d9d0b8] rounded-xl p-6 text-[#22261f] font-sans space-y-6 shadow-sm">
        <div className="border-b-2 border-[#1F4D3C] pb-3 flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold text-[#1F4D3C] uppercase tracking-wide">
              RBAS Detailed Project Report (DPR)
            </h3>
            <p className="text-xs text-[#a9820f] font-semibold">
              Priority Sector Rural Micro-Enterprise Feasibility Assessment
            </p>
          </div>
          <div className="text-right text-[11px] text-gray-500 font-mono">
            <div>Date: {new Date().toLocaleDateString("en-IN")}</div>
            <div>Ref: GS-{Math.floor(100000 + Math.random() * 900000)}</div>
          </div>
        </div>

        {/* 1. General Profile */}
        <section className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F4D3C] border-b border-gray-200 pb-1">
            1. Enterprise & Geographic Profile
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Proposed Sector:</span>{" "}
              <strong className="text-gray-800">{category}</strong>
            </div>
            <div>
              <span className="text-gray-500">Location:</span>{" "}
              <strong className="text-gray-800">
                {village}, {block}, {district}, {state}
              </strong>
            </div>
            <div>
              <span className="text-gray-500">10km Radial Competition:</span>{" "}
              <strong className="text-gray-800">{compCount} Outlets</strong>
            </div>
            <div>
              <span className="text-gray-500">Market Saturation:</span>{" "}
              <strong className="text-gray-800 uppercase">{saturation}</strong>
            </div>
          </div>
        </section>

        {/* 2. Capital Structuring Breakdown */}
        <section className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F4D3C] border-b border-gray-200 pb-1">
            2. Project Cost & Means of Financing
          </h4>
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-[#f7f3e8] text-gray-700 font-semibold border-b border-gray-300">
                <th className="py-2 px-3">Capital Outlay Component</th>
                <th className="py-2 px-3 text-right">Ratio</th>
                <th className="py-2 px-3 text-right">Amount (INR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 font-mono text-[11px]">
              <tr>
                <td className="py-2 px-3 font-sans">Promoter Margin Contribution (Equity)</td>
                <td className="py-2 px-3 text-right">10.0%</td>
                <td className="py-2 px-3 text-right">₹{marginEquity.toLocaleString("en-IN")}</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-sans">Recommended Institutional Term Loan (SCA Debt)</td>
                <td className="py-2 px-3 text-right">90.0%</td>
                <td className="py-2 px-3 text-right font-bold text-[#1F4D3C]">₹{debtAmount.toLocaleString("en-IN")}</td>
              </tr>
              <tr className="bg-gray-50 font-bold">
                <td className="py-2 px-3 font-sans">Total Validated Project Outlay</td>
                <td className="py-2 px-3 text-right">100.0%</td>
                <td className="py-2 px-3 text-right">₹{totalCost.toLocaleString("en-IN")}</td>
              </tr>
            </tbody>
          </table>

          <div className="grid grid-cols-3 gap-2 bg-[#f7f3e8] p-3 rounded-lg text-xs mt-2">
            <div>
              <span className="text-gray-500 block text-[10px] uppercase">Interest Rate:</span>
              <strong className="font-mono">{interestRate}% p.a.</strong>
            </div>
            <div>
              <span className="text-gray-500 block text-[10px] uppercase">Tenure & Moratorium:</span>
              <strong className="font-mono">{tenureYears} Years ({moratorium}M grace)</strong>
            </div>
            <div>
              <span className="text-gray-500 block text-[10px] uppercase">Monthly Repayment (EMI):</span>
              <strong className="font-mono text-[#1F4D3C]">₹{emi.toLocaleString("en-IN")}</strong>
            </div>
          </div>
        </section>

        {/* 3. Amortization Schedule */}
        {schedule.length > 0 && (
          <section className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F4D3C] border-b border-gray-200 pb-1">
              3. Debt Amortization & Repayment Trajectory
            </h4>
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-gray-100 text-gray-700 font-semibold border-b border-gray-300">
                  <th className="py-1.5 px-2">Period</th>
                  <th className="py-1.5 px-2 text-right">Opening Debt</th>
                  <th className="py-1.5 px-2 text-right">Principal Repaid</th>
                  <th className="py-1.5 px-2 text-right">Interest Serviced</th>
                  <th className="py-1.5 px-2 text-right">Closing Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 font-mono text-[11px]">
                {schedule.map((row, idx) => (
                  <tr key={idx}>
                    <td className="py-1.5 px-2 font-sans font-medium">{row.year}</td>
                    <td className="py-1.5 px-2 text-right">₹{Number(row.opening_balance).toLocaleString("en-IN")}</td>
                    <td className="py-1.5 px-2 text-right">₹{Number(row.principal).toLocaleString("en-IN")}</td>
                    <td className="py-1.5 px-2 text-right">₹{Number(row.interest).toLocaleString("en-IN")}</td>
                    <td className="py-1.5 px-2 text-right font-bold text-[#1F4D3C]">
                      ₹{Number(row.closing_balance).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* 4. Bank Appraisal & Sanction Summary */}
        <section className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F4D3C] border-b border-gray-200 pb-1">
            4. Institutional Loan Appraisal Summary
          </h4>
          <p className="text-xs leading-relaxed text-gray-700 whitespace-pre-line text-justify">
            {sanctionSummary}
          </p>
        </section>
      </div>
    </div>
  );
}