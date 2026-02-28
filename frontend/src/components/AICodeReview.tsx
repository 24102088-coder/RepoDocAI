"use client";

import React from "react";

interface Props {
  review: string;
}

export default function AICodeReview({ review }: Props) {
  // Parse sections with scores
  const sections = review.split("---REVIEW_BREAK---").filter((s) => s.trim());

  // Try to extract score from each section
  const parseSection = (text: string) => {
    const lines = text.trim().split("\n");
    let title = "Review";
    let score: number | null = null;

    for (const line of lines) {
      // Match **Security** (8/10) or similar
      const titleMatch = line.match(/\*\*(.+?)\*\*.*?(\d+)\s*\/\s*10/);
      if (titleMatch) {
        title = titleMatch[1];
        score = parseInt(titleMatch[2]);
        break;
      }
      // Match # heading
      const headingMatch = line.match(/^#+\s*(.+)/);
      if (headingMatch && !title) {
        title = headingMatch[1].replace(/\*\*/g, "");
      }
      // Match standalone score
      const scoreMatch = line.match(/Score.*?(\d+)\s*\/\s*10/i);
      if (scoreMatch) {
        score = parseInt(scoreMatch[1]);
      }
    }

    return { title, score, content: text.trim() };
  };

  const parsed = sections.map(parseSection);

  const getScoreColor = (score: number | null) => {
    if (score === null) return "#888";
    if (score >= 8) return "#22c55e";
    if (score >= 6) return "#eab308";
    if (score >= 4) return "#f97316";
    return "#ef4444";
  };

  const getScoreEmoji = (score: number | null) => {
    if (score === null) return "📋";
    if (score >= 9) return "🏆";
    if (score >= 7) return "✅";
    if (score >= 5) return "⚠️";
    return "🚨";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="text-3xl">🤖</div>
        <div>
          <h3 className="text-white font-bold text-lg">
            AI-Powered Code Review
          </h3>
          <p className="text-white/40 text-sm">
            Automated analysis by AMD-accelerated LLM
          </p>
        </div>
      </div>

      {/* Score Cards */}
      {parsed.length > 1 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          {parsed
            .filter((p) => p.score !== null)
            .slice(0, 5)
            .map((p, i) => (
              <div
                key={i}
                className="text-center p-3 bg-white/5 border border-white/10 rounded-xl"
              >
                <div className="text-lg mb-1">{getScoreEmoji(p.score)}</div>
                <div
                  className="text-2xl font-black"
                  style={{
                    color: getScoreColor(p.score),
                    textShadow: `0 0 15px ${getScoreColor(p.score)}50`,
                  }}
                >
                  {p.score}/10
                </div>
                <div className="text-white/40 text-xs mt-1 truncate">
                  {p.title}
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Full Review */}
      <div className="space-y-4">
        {parsed.map((section, i) => (
          <details
            key={i}
            className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden"
            open={i === 0}
          >
            <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-all">
              <div className="flex items-center gap-3">
                <span>{getScoreEmoji(section.score)}</span>
                <span className="text-white font-semibold">{section.title}</span>
                {section.score !== null && (
                  <span
                    className="px-2 py-0.5 rounded text-xs font-bold"
                    style={{
                      color: getScoreColor(section.score),
                      backgroundColor: `${getScoreColor(section.score)}20`,
                    }}
                  >
                    {section.score}/10
                  </span>
                )}
              </div>
              <svg
                className="w-5 h-5 text-white/30 transition-transform group-open:rotate-180"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </summary>
            <div className="px-4 pb-4 text-white/70 text-sm leading-relaxed whitespace-pre-wrap doc-content">
              {section.content}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
