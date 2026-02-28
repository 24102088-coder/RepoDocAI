"use client";

interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-1.5">
        <span>Progress</span>
        <span>{progress}%</span>
      </div>
      <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-amd-red to-orange-500 transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
