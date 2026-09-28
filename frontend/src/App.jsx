import { useState, useEffect, useCallback, useRef } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LanguageProvider, useLanguage } from "./context/LanguageContext";
import FinancialCalculatorWidget from "./components/FinancialCalculatorWidget";
import InteractiveMap from "./components/InteractiveMap";
import AdvisoryReportView from "./components/AdvisoryReportView";
import DprPdfGenerator from "./components/DprPdfGenerator";
import { competitorsDensity, generateFeasibility } from "./api/client";
import FutureScopePage from './components/FutureScopePage';

const queryClient = new QueryClient();

const CATEGORIES = [
  { code: "DAIRY", label: "Dairy / Milk products" },
  { code: "GROCERY", label: "Grocery / General store" },
  { code: "TAILOR", label: "Tailoring / Boutique" },
  { code: "POULTRY", label: "Poultry farming" },
  { code: "BAKERY", label: "Bakery / Snacks" },
  { code: "HANDICRAFT", label: "Handicraft / Weaving" },
  { code: "SALON", label: "Salon / Beauty parlour" },
  { code: "ELECTRONICS", label: "Mobile & electronics repair" },
  { code: "HARDWARE", label: "Hardware / Building materials" },
];

const NOMINATIM_BASE = "https://nominatim.openstreetmap.org";
const GEO_HEADERS = { "User-Agent": "GramSetu-Enterprise-App/2.0" };

// Dynamic Forward Geocoding: Searches nationwide without state restrictions
async function fetchCoordsFromAddress({ village, block, district, state }) {
  const queries = [
    [village, block, district, state, "India"].filter(Boolean).join(", "),
    [village, district, state, "India"].filter(Boolean).join(", "),
    [block, district, state, "India"].filter(Boolean).join(", "),
    [district, state, "India"].filter(Boolean).join(", ")
  ];

  for (const query of queries) {
    if (!query.replace("India", "").trim()) continue;
    try {
      const res = await fetch(
        `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(query)}&limit=1&addressdetails=1`,
        { headers: GEO_HEADERS }
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const addr = data[0].address || {};
        return {
          lat: parseFloat(data[0].lat),
          lon: parseFloat(data[0].lon),
          displayName: data[0].display_name,
          state: addr.state || "",
          district: addr.state_district || addr.district || "",
          block: addr.county || addr.subdistrict || "",
          village: addr.village || addr.hamlet || addr.town || addr.city || ""
        };
      }
    } catch (err) {
      console.warn(`Query attempt failed for "${query}":`, err);
    }
  }

  return null;
}

// Dynamic Reverse Geocoding: Extracts village, block, district, and state from GPS coords
async function fetchAddressFromCoords(lat, lon) {
  try {
    const res = await fetch(
      `${NOMINATIM_BASE}/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14&addressdetails=1`,
      { headers: GEO_HEADERS }
    );
    const data = await res.json();
    const addr = data.address || {};

    return {
      village: addr.village || addr.hamlet || addr.suburb || addr.town || addr.city || "",
      block: addr.county || addr.subdistrict || "",
      district: addr.state_district || addr.district || addr.city || "",
      state: addr.state || "",
      displayName: data.display_name || ""
    };
  } catch (err) {
    console.error("Reverse geocoding failed:", err);
    return null;
  }
}

function Wizard() {
  const { language, setLanguage, listen } = useLanguage();
  const [form, setForm] = useState({
    village: "",
    block: "",
    district: "",
    state: "",
    category: "GROCERY",
    margin: 50000,
  });

  const [center, setCenter] = useState({ lat: 20.5937, lon: 78.9629 });
  const [resolvedLocationName, setResolvedLocationName] = useState("");
  const [competitors, setCompetitors] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);

  const activeCoordsRef = useRef(center);
  useEffect(() => {
    activeCoordsRef.current = center;
  }, [center]);

  // 1. Forward geocode with debouncing
  const updateCoordinates = useCallback(async (locationData) => {
    if (!locationData.village && !locationData.district && !locationData.block) return;
    setIsLocating(true);
    const resolved = await fetchCoordsFromAddress(locationData);
    if (resolved) {
      const newCoords = { lat: resolved.lat, lon: resolved.lon };
      setCenter(newCoords);
      activeCoordsRef.current = newCoords;
      setResolvedLocationName(resolved.displayName);
      if (resolved.state && !locationData.state) {
        setForm((prev) => ({ ...prev, state: resolved.state }));
      }
    }
    setIsLocating(false);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      updateCoordinates(form);
    }, 700);
    return () => clearTimeout(timer);
  }, [form.village, form.block, form.district, form.state, updateCoordinates]);

  // 2. Browser GPS detection
  const handleFetchCurrentGPS = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        const newCoords = { lat, lon };
        setCenter(newCoords);
        activeCoordsRef.current = newCoords;

        const details = await fetchAddressFromCoords(lat, lon);
        if (details) {
          setForm((prev) => ({
            ...prev,
            village: details.village || prev.village,
            block: details.block || prev.block,
            district: details.district || prev.district,
            state: details.state || prev.state,
          }));
          setResolvedLocationName(details.displayName);
        }
        setIsLocating(false);
      },
      (error) => {
        console.warn("GPS error:", error.message);
        alert("Unable to fetch your location. Please enter your location manually.");
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleStructureChange = (structure) => {
    if (structure?.margin_capital) {
      setForm((prev) => ({ ...prev, margin: structure.margin_capital }));
    }
  };

  // 3. Dynamic Submission with Merged Numerical/Statistical Payload Extraction
  const handleGenerate = async () => {
    if (!form.village && !form.district) {
      alert("Please provide at least a Village or District name.");
      return;
    }

    setLoading(true);
    try {
      let targetLat = activeCoordsRef.current.lat;
      let targetLon = activeCoordsRef.current.lon;

      try {
        const directResolution = await fetchCoordsFromAddress(form);
        if (directResolution) {
          targetLat = directResolution.lat;
          targetLon = directResolution.lon;
          setCenter({ lat: targetLat, lon: targetLon });
          setResolvedLocationName(directResolution.displayName);
        }
      } catch (geoErr) {
        console.warn("Geocoding failed, proceeding with active coordinates:", geoErr);
      }

      // 1. Fetch live competitors from OpenStreetMap Overpass
      let competitorPool = [];
      let competitorCount = 0;
      let saturationLevel = "MODERATE";

      try {
        const density = await competitorsDensity({
          latitude: targetLat,
          longitude: targetLon,
          category: form.category,
          business_type: form.category,
          radius_km: 10,
        });
        competitorPool = density?.competitors || [];
        competitorCount = density?.competitor_count ?? competitorPool.length;
        saturationLevel = density?.saturation_level || "MODERATE";
        setCompetitors(competitorPool);
      } catch (densityErr) {
        console.warn("Overpass API query failed, proceeding with fallback density:", densityErr);
      }

      // 2. Generate Feasibility Analysis
      const result = await generateFeasibility({
        village: form.village || "Local Area",
        block: form.block || form.village || "Local Block",
        district: form.district || form.state || "Local District",
        state: form.state || "",
        latitude: targetLat,
        longitude: targetLon,
        margin_capital: form.margin,
        business_category: form.category,
        category_code: form.category,
        competitor_count: competitorCount,
        saturation_level: saturationLevel,
        language,
      });

      // Extract and merge all numerical, geographic, and qualitative advisory layers
      const aiReport = result?.report || result?.data?.report || {};
      const finData = result?.finance || result?.financial_structure || {};
      const geoData = result?.geography || result?.geo_context || {};

      const mergedReport = {
        ...aiReport,
        // Deterministic Financials (with fallback math if missing from payload)
        margin_capital: finData.margin_capital ?? aiReport.margin_capital ?? form.margin,
        total_project_cost: finData.total_project_cost ?? aiReport.total_project_cost ?? (form.margin / 0.10),
        loan_amount: finData.loan_amount ?? aiReport.loan_amount ?? ((form.margin / 0.10) * 0.90),
        monthly_emi: finData.monthly_emi ?? aiReport.monthly_emi ?? 0,
        interest_rate_pa: finData.interest_rate_pa ?? aiReport.interest_rate_pa ?? 8.0,
        tenure_years: finData.tenure_years ?? aiReport.tenure_years ?? 5,
        moratorium_months: finData.moratorium_months ?? aiReport.moratorium_months ?? 6,
        scheme_name: finData.scheme_name || aiReport.scheme_name || "Rural Priority Micro-Credit (SCA)",

        // Geographic & Competitive Metrics
        competitor_count: geoData.competitor_count ?? aiReport.competitor_count ?? competitorCount,
        competitor_count_10km: geoData.competitor_count_10km ?? aiReport.competitor_count_10km ?? competitorCount,
        saturation_level: geoData.saturation_level || aiReport.saturation_level || saturationLevel,
        village: geoData.village || form.village || "Local Area",
        block: geoData.block || form.block || "Local Block",
        district: geoData.district || form.district || "Local District",
        state: geoData.state || form.state || "",
      };

      setReport(mergedReport);
    } catch (e) {
      console.error("[handleGenerate Error]:", e);
      alert(e.response?.data?.message || e.message || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-5 py-10 space-y-6 font-body">
      <header className="topbar">
        <div className="brand">
          <img src="https://i.postimg.cc/rmFsbCGX/RBAS-logo.jpg" alt="Logo" className="logo-img"></img>
          <h1 className="name" data-i18n="brand_name">Rural Business Advisory System</h1>
        </div>
        
        {/* Router link removed from here */}
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          
          <select id="langSelect"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="bn">বাংলা</option>
            <option value="mr">मराठी</option>
            <option value="ta">தமிழ்</option>
            <option value="te">తెలుగు</option>
          </select>
        </div>
      </header>
      <section className="hero">
  <div className="hero-inner">
    <h1 data-i18n="hero_title">Turn a small margin into a bankable business plan.</h1>
    <p data-i18n="hero_sub">Enter your available capital and location — get a deterministic loan structure, a live map of nearby competitors from OpenStreetMap, and a feasibility report you can carry to a bank.</p>
  </div>
</section>

      <section className="bg-white border border-paper-dk rounded-xl p-6 space-y-4 shadow-sm">
        <div className="panel">
    <h2><span className="step-num">1</span><span data-i18n="wizard_title">Business Enquiry</span></h2>
    <div className="sub" data-i18n="wizard_sub">Tell us where and what you want to start — the math and the map do the rest.</div>
          
          <button
            type="button"
            onClick={handleFetchCurrentGPS}
            disabled={isLocating}
            className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#edf5ef] text-[#245237] border border-[#a7d3b5] px-3 py-1.5 rounded-lg hover:bg-[#d8ebd9] transition disabled:opacity-50"
          >
            <span>📍</span>
            {isLocating ? "Resolving location…" : "Use My Current Location"}
          </button>
        </div>

        <div className="grid3">
          <Field
            label="Village / Town"
            value={form.village}
            onChange={(v) => setForm((prev) => ({ ...prev, village: v }))}
          />
          <Field
            label="Block "
            value={form.block}
            onChange={(v) => setForm((prev) => ({ ...prev, block: v }))}
          />
          <Field
            label="District"            
            value={form.district}
            onChange={(v) => setForm((prev) => ({ ...prev, district: v }))}
          />
          <Field
            label="State"            
            value={form.state}
            onChange={(v) => setForm((prev) => ({ ...prev, state: v }))}
          />
        </div>

        {resolvedLocationName ? (
          <div className="text-[11px] text-gray-600 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 truncate">
            <span className="font-bold text-gray-700">Resolved Location: </span>
            {resolvedLocationName}
          </div>
        ) : (
          <div className="text-[11px] text-gray-400 bg-gray-50 px-3 py-2 rounded-lg border border-dashed border-gray-200">
            Type any village/town and district above, or click "Use My Current Location".
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide mb-1">Business Category</label>
          <select
            id ="inCategory"
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            {CATEGORIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            type="button"
            onClick={() =>
              listen((text) => {
                setForm((prev) => ({ ...prev, village: text }));
              })
            }
            className="text-xs border border-paper-dk hover:bg-gray-50 rounded-full px-4 py-2 transition"
          >
            🎙 Speak village name
          </button>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading || isLocating}
            className="bg-wheat-dk hover:opacity-90 text-white font-bold px-6 py-2.5 rounded-lg transition ml-auto disabled:opacity-50"
          >
            {loading ? "Generating Feasibility Report…" : "Generate feasibility report"}
          </button>
        </div>
      </section>

      <FinancialCalculatorWidget onStructureChange={handleStructureChange} />

      <section className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm">
        <div className="panel">
        <h2><span className="step-num">3</span><span data-i18n="wizard_title">Hyper-local competitor map</span></h2>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500 font-mono">
            Lat: {center.lat.toFixed(4)}, Lon: {center.lon.toFixed(4)}
          </span>
        </div></div>
        <InteractiveMap center={center} competitors={competitors} />
      </section>

      {report && (
        <div id="report-section" className="space-y-6 pt-2">
          {/* Statistical Metrics Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-paper border border-paper-dk rounded-xl p-4 shadow-sm">
              <div className="text-[11px] font-bold text-[#7a7460] uppercase tracking-wider">Total Outlay</div>
              <div className="font-mono text-xl font-bold text-forest-dk mt-1">
                ₹{Number(report.total_project_cost || 0).toLocaleString("en-IN")}
              </div>
              <div className="text-[10px] text-gray-500 mt-0.5">100% Capital Outlay</div>
            </div>

            <div className="bg-paper border border-paper-dk rounded-xl p-4 shadow-sm">
              <div className="text-[11px] font-bold text-[#7a7460] uppercase tracking-wider">SCA Debt (90%)</div>
              <div className="font-mono text-xl font-bold text-forest-dk mt-1">
                ₹{Number(report.loan_amount || 0).toLocaleString("en-IN")}
              </div>
              <div className="text-[10px] text-gray-500 mt-0.5">{report.interest_rate_pa || 8}% p.a. • {report.tenure_years || 5}Y</div>
            </div>

            <div className="bg-paper border border-paper-dk rounded-xl p-4 shadow-sm">
              <div className="text-[11px] font-bold text-[#7a7460] uppercase tracking-wider">Promoter Margin (10%)</div>
              <div className="font-mono text-xl font-bold text-forest-dk mt-1">
                ₹{Number(report.margin_capital || 0).toLocaleString("en-IN")}
              </div>
              <div className="text-[10px] text-gray-500 mt-0.5">Equity Contribution</div>
            </div>

            <div className="bg-paper border border-paper-dk rounded-xl p-4 shadow-sm">
              <div className="text-[11px] font-bold text-[#7a7460] uppercase tracking-wider">Monthly Repayment</div>
              <div className="font-mono text-xl font-bold text-forest-dk mt-1">
                ₹{Number(report.monthly_emi || 0).toLocaleString("en-IN")}
              </div>
              <div className="text-[10px] text-gray-500 mt-0.5">{report.moratorium_months || 6}M Moratorium</div>
            </div>
          </div>

          {/* Market Saturation Context */}
          <div className="flex items-center justify-between bg-white border border-paper-dk rounded-xl p-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-700">10km Radial Competition:</span>
              <span className="font-mono font-bold bg-[#efe8d6] px-2 py-0.5 rounded text-forest-dk">
                {report.competitor_count ?? competitors.length} Identified POIs
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-700">Saturation Index:</span>
              <span className={`px-2 py-0.5 rounded font-bold uppercase ${
                report.saturation_level === "LOW" ? "bg-green-100 text-green-800" :
                report.saturation_level === "HIGH" ? "bg-red-100 text-red-800" :
                "bg-amber-100 text-amber-800"
              }`}>
                {report.saturation_level || "MODERATE"}
              </span>
            </div>
          </div>

          {/* Qualitative Advisory & SWOT Matrix */}
          <AdvisoryReportView report={report} />

          {/* Bank-Ready Detailed Project Report */}
          <section className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm space-y-3">
            <h2 className="font-display text-lg">Bank-ready DPR Summary</h2>
            <p className="text-sm text-gray-700 leading-relaxed">
              {report.bank_dpr_summary}
            </p>
            <DprPdfGenerator report={report} />
          </section>
        </div>
      )}

      {/* Ekdom niche Future Scope add kora holo */}
      <div className="mt-12 border-t border-gray-200 pt-8 w-full">
          <FutureScopePage />
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder = "" }) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wide mb-1">{label}</label>
      <input
        className="w-full border border-paper-dk rounded-md px-3 py-2 bg-paper text-sm"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

// Router bad dewa holo
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <Wizard />
      </LanguageProvider>
    </QueryClientProvider>
  );
}