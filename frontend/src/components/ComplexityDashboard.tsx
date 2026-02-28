"use client";

import React from "react";

interface ComplexityData {
  total_files: number;
  total_lines: number;
  avg_lines_per_file: number;
  language_distribution: { language: string; lines: number; percentage: number }[];
  top_modules: string[];
  framework_categories: Record<string, string[]>;
  dependency_stats: { total: number; runtime: number; dev: number };
  codebase_size: string;
}

const LANG_COLORS: Record<string, string> = {
  Python: "#3776AB",
  JavaScript: "#F7DF1E",
  TypeScript: "#3178C6",
  Java: "#ED8B00",
  Go: "#00ADD8",
  Rust: "#DEA584",
  "C++": "#00599C",
  "C#": "#239120",
  Ruby: "#CC342D",
  PHP: "#777BB4",
  HTML: "#E34F26",
  CSS: "#1572B6",
  Markdown: "#083f7a",
  YAML: "#CB171E",
  JSON: "#292929",
  Shell: "#89e051",
  Dockerfile: "#2496ED",
};

export default function ComplexityDashboard({
  data,
}: {
  data: ComplexityData;
}) {
  const maxLines = Math.max(...data.language_distribution.map((l) => l.lines), 1);

  return (
    <div className="space-y-8">
      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Total Files",
            value: data.total_files.toLocaleString(),
            icon: "📁",
          },
          {
            label: "Total Lines",
            value: data.total_lines.toLocaleString(),
            icon: "📝",
          },
          {
            label: "Avg Lines/File",
            value: data.avg_lines_per_file.toString(),
            icon: "📊",
          },
          { label: "Codebase Size", value: data.codebase_size, icon: "📦" },
        ].map((s, i) => (
          <div
            key={i}
            className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-xl p-4 text-center hover:border-white/20 transition-all group"
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">
              {s.icon}
            </div>
            <div className="text-2xl font-black text-white">{s.value}</div>
            <div className="text-white/40 text-xs mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Language Chart */}
      <div>
        <h4 className="text-white/60 text-sm font-semibold uppercase tracking-wider mb-4">
          Language Distribution
        </h4>

        {/* Stacked bar */}
        <div className="h-6 rounded-full overflow-hidden flex mb-4 border border-white/10">
          {data.language_distribution.map((l, i) => (
            <div
              key={i}
              style={{
                width: `${l.percentage}%`,
                backgroundColor: LANG_COLORS[l.language] || "#555",
              }}
              className="h-full transition-all hover:brightness-125"
              title={`${l.language}: ${l.percentage}%`}
            />
          ))}
        </div>

        {/* Bars */}
        <div className="space-y-2">
          {data.language_distribution.map((l, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-24 text-right text-sm text-white/60 font-mono truncate">
                {l.language}
              </div>
              <div className="flex-1 h-5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${(l.lines / maxLines) * 100}%`,
                    backgroundColor: LANG_COLORS[l.language] || "#555",
                    boxShadow: `0 0 10px ${LANG_COLORS[l.language] || "#555"}60`,
                  }}
                />
              </div>
              <div className="w-20 text-right text-xs text-white/40 font-mono">
                {l.lines.toLocaleString()} <span className="text-white/20">lines</span>
              </div>
              <div className="w-14 text-right text-xs text-white/50 font-semibold">
                {l.percentage}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dependency Stats */}
      <div>
        <h4 className="text-white/60 text-sm font-semibold uppercase tracking-wider mb-4">
          Dependencies
        </h4>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              label: "Total",
              value: data.dependency_stats.total,
              color: "#8B5CF6",
            },
            {
              label: "Runtime",
              value: data.dependency_stats.runtime,
              color: "#06B6D4",
            },
            {
              label: "Dev",
              value: data.dependency_stats.dev,
              color: "#F59E0B",
            },
          ].map((d, i) => (
            <div
              key={i}
              className="text-center p-4 rounded-xl border border-white/10 bg-white/5"
            >
              <div
                className="text-3xl font-black"
                style={{
                  color: d.color,
                  textShadow: `0 0 15px ${d.color}50`,
                }}
              >
                {d.value}
              </div>
              <div className="text-white/40 text-xs mt-1">{d.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Modules */}
      {data.top_modules.length > 0 && (
        <div>
          <h4 className="text-white/60 text-sm font-semibold uppercase tracking-wider mb-3">
            Top Modules
          </h4>
          <div className="flex flex-wrap gap-2">
            {data.top_modules.map((m, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-white/70 text-sm font-mono hover:bg-white/10 transition-all"
              >
                📂 {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Framework Categories */}
      {Object.keys(data.framework_categories).length > 0 && (
        <div>
          <h4 className="text-white/60 text-sm font-semibold uppercase tracking-wider mb-3">
            Framework Ecosystem
          </h4>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(data.framework_categories).map(([cat, fws], i) => (
              <div
                key={i}
                className="bg-white/5 border border-white/10 rounded-xl p-3"
              >
                <div className="text-white/50 text-xs uppercase mb-2">
                  {cat}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {fws.map((fw, j) => (
                    <span
                      key={j}
                      className="px-2 py-0.5 bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-500/20 rounded text-white/80 text-xs"
                    >
                      {fw}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
