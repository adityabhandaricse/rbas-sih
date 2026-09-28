const QUADRANTS = [
  { key: "swot_strengths", title: "Strengths", cls: "bg-green-50" },
  { key: "swot_weaknesses", title: "Weaknesses", cls: "bg-orange-50" },
  { key: "swot_opportunities", title: "Opportunities", cls: "bg-blue-50" },
  { key: "swot_threats", title: "Threats", cls: "bg-amber-50" },
];

export default function SwotMatrix({ report }) {
  if (!report) return null;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {QUADRANTS.map(({ key, title, cls }) => (
        <div key={key} className={`rounded-lg border border-paper-dk p-4 ${cls}`}>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">{title}</h4>
          <ul className="list-disc pl-5 text-sm leading-relaxed space-y-1">
            {(report[key] || []).map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        </div>
      ))}
    </div>
  );
}
