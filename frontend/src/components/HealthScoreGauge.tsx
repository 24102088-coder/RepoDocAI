"use client";

import React from "react";

interface HealthData {
  score: number;
  grade: string;
  max_score: number;
  details: {
    check: string;
    passed: boolean;
    message: string;
    weight: number;
  }[];
  summary: string;
}

export default function HealthScoreGauge({ data }: { data: HealthData }) {
  const gradeColors: Record<string, string> = {
    "A+": "#00ff88",
    A: "#22c55e",
    B: "#84cc16",
    C: "#eab308",
    D: "#f97316",
    F: "#ef4444",
  };

  const color = gradeColors[data.grade] || "#888";
  const circumference = 2 * Math.PI * 80;
  const offset = circumference - (data.score / 100) * circumference;

  return (
    <div className="space-y-6">
      {/* SVG Gauge */}
      <div className="flex justify-center">
        <div className="relative w-52 h-52">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
            {/* Track */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="16"
            />
            {/* Progress */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke={color}
              strokeWidth="16"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-[2s] ease-out"
              style={{
                filter: `drop-shadow(0 0 12px ${color})`,
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-5xl font-black"
              style={{ color, textShadow: `0 0 20px ${color}50` }}
            >
              {data.grade}
            </span>
            <span className="text-sm text-white/50 mt-1">
              {data.score}/100
            </span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <p className="text-center text-white/70 text-sm italic">{data.summary}</p>

      {/* Details */}
      <div className="grid gap-2">
        {data.details.map((d, i) => (
          <div
            key={i}
            className="flex items-center justify-between bg-white/5 rounded-lg px-4 py-2.5 border border-white/5 hover:border-white/10 transition-all"
          >
            <div className="flex items-center gap-3">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  d.passed
                    ? "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]"
                    : "bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.5)]"
                }`}
              />
              <span className="text-white/80 text-sm font-medium">
                {d.check}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-white/40 text-xs">{d.message}</span>
              <span className="text-white/30 text-xs font-mono">
                +{d.weight}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
