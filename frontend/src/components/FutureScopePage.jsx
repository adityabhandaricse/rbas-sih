import React from 'react';
import { Mic, Landmark, LineChart, Shield } from 'lucide-react';

const FutureScopePage = () => {
  const roadmapItems = [
    {
      icon: <Mic className="w-4 h-4 text-purple-500" />,
      title: "Vernacular Voice & Dialect AI",
      description: "Integrating speech-to-text in regional Indian languages and local dialects to make business advisory accessible to non-literate rural entrepreneurs."
    },
    {
      icon: <Landmark className="w-4 h-4 text-purple-700" />,
      title: "Direct SCA & Bank Portal Integration",
      description: "Direct API submission of the generated DPR to PMEGP, Mudra, and State Channelising Agency (SCA) portals for instant loan sanction processing."
    },
    {
      icon: <LineChart className="w-4 h-4 text-indigo-400" />,
      title: "Live Mandi & Price Feeds",
      description: "Incorporating real-time commodity prices and seasonal agricultural trend forecasting from e-NAM to dynamically optimize pricing strategies."
    },
    {
      icon: <Shield className="w-4 h-4 text-yellow-500" />,
      title: "SHG & Supply Chain Aggregation",
      description: "Linking micro-enterprises with local Self-Help Groups (SHGs) and wholesale distributors to reduce logistics costs via group purchasing power."
    }
  ];

  return (
    <div className="w-full font-sans flex justify-center">
      
      
      <div className="w-full bg-[#fdfdf9] border border-gray-100 rounded-xl p-8 shadow-sm">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3 mb-1">
            <span className="bg-[#D4A62A] text-yellow-800 text-xs px-2 py-0.5 rounded-sm">4</span>
            Future Scope & Roadmap
          </h2>
          <p className="text-gray-500 text-sm">
            Planned enhancements to expand AI capabilities, API integrations, and ecosystem connectivity.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roadmapItems.map((item, index) => (
            <div key={index} className="bg-[#f7f6f0] p-5 rounded-lg border border-transparent hover:border-gray-200 transition-colors">
              <h3 className="text-[15px] font-semibold text-gray-800 flex items-center gap-2 mb-2">
                {item.icon}
                {item.title}
              </h3>
              <p className="text-gray-600 text-[13px] leading-relaxed">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default FutureScopePage;