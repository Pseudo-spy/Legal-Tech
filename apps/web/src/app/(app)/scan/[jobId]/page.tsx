"use client";

import { useParams } from "next/navigation";

export default function ScanPage() {
  const params = useParams();
  const jobId = params?.jobId as string;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h1 className="text-2xl font-bold text-zinc-900 mb-4">Scan Results</h1>
      <p className="text-zinc-600">Job ID: {jobId}</p>
    </div>
  );
}