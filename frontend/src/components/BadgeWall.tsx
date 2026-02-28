"use client";

import React from "react";

interface BadgeInfo {
  label: string;
  message: string;
  color: string;
  markdown: string;
}

export default function BadgeWall({ badges }: { badges: BadgeInfo[] }) {
  return (
    <div className="space-y-6">
      {/* Visual Badges */}
      <div className="flex flex-wrap gap-3 justify-center">
        {badges.map((b, i) => (
          <div
            key={i}
            className="inline-flex items-stretch rounded-md overflow-hidden text-sm font-semibold shadow-lg hover:scale-105 transition-transform cursor-default"
            style={{
              boxShadow: `0 0 15px rgba(${parseInt(
                b.color.slice(0, 2),
                16
              ) || 100}, ${parseInt(b.color.slice(2, 4), 16) || 100}, ${
                parseInt(b.color.slice(4, 6), 16) || 100
              }, 0.3)`,
            }}
          >
            <span className="px-3 py-1.5 bg-gray-800 text-white/70">
              {b.label}
            </span>
            <span
              className="px-3 py-1.5 text-white"
              style={{ backgroundColor: `#${b.color}` }}
            >
              {b.message}
            </span>
          </div>
        ))}
      </div>

      {/* Copyable Markdown */}
      <div className="space-y-2">
        <h4 className="text-white/50 text-sm font-semibold uppercase tracking-wider">
          Copy Badge Markdown
        </h4>
        <div className="bg-black/40 rounded-xl border border-white/10 p-4 font-mono text-xs text-green-400/80 space-y-1 max-h-60 overflow-y-auto">
          {badges.map((b, i) => (
            <div key={i} className="hover:text-green-300 transition-colors">
              {b.markdown}
            </div>
          ))}
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(
              badges.map((b) => b.markdown).join("\n")
            );
          }}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white/70 text-sm transition-all"
        >
          Copy All Badges
        </button>
      </div>
    </div>
  );
}
