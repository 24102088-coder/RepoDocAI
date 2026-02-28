"use client";

import { useEffect, useRef, useId } from "react";

interface Props {
  chart: string;
}

export default function MermaidDiagram({ chart }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const id = useId().replace(/:/g, "m");

  useEffect(() => {
    if (!ref.current || !chart) return;

    let cancelled = false;

    (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
          fontFamily: "Inter, system-ui, sans-serif",
        });

        if (cancelled) return;

        const { svg } = await mermaid.render(`mermaid-${id}`, chart);
        if (ref.current && !cancelled) {
          ref.current.innerHTML = svg;
        }
      } catch (err) {
        console.error("Mermaid render error:", err);
        if (ref.current && !cancelled) {
          ref.current.innerHTML = `<pre class="text-red-500 text-sm">Diagram render error. Source:\n${chart}</pre>`;
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  return <div ref={ref} className="mermaid-container overflow-x-auto" />;
}
