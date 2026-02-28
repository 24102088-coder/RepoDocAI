"use client";

import StarfieldBackground from "@/components/StarfieldBackground";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <StarfieldBackground />
      <div className="relative z-10">{children}</div>
    </>
  );
}
