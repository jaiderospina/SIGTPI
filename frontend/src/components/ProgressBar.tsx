import clsx from "clsx"

interface Props { value: number; label?: string; size?: "sm" | "md" }

export default function ProgressBar({ value, label, size = "md" }: Props) {
  const pct = Math.min(Math.max(value, 0), 100)
  const color = pct >= 75 ? "bg-success" : pct >= 40 ? "bg-warning" : "bg-danger"
  return (
    <div className="w-full">
      {label && <div className="flex justify-between text-xs text-gray-500 mb-1"><span>{label}</span><span>{pct}%</span></div>}
      <div className={clsx("w-full bg-gray-200 rounded-full overflow-hidden", size === "sm" ? "h-1.5" : "h-2.5")}>
        <div className={clsx("h-full rounded-full transition-all duration-500", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
