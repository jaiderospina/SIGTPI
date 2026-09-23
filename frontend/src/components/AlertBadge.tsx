import clsx from "clsx"

const cfg: Record<string, { label: string; cls: string }> = {
  "1": { label: "Info",    cls: "bg-blue-100 text-blue-700"   },
  "2": { label: "Aviso",   cls: "bg-warning-light text-warning" },
  "3": { label: "Riesgo",  cls: "bg-orange-100 text-orange-700" },
  "4": { label: "Crítico", cls: "bg-danger-light text-danger"  },
}

export default function AlertBadge({ level }: { level: string }) {
  const { label, cls } = cfg[level] ?? { label: level, cls: "bg-gray-100 text-gray-600" }
  return <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full", cls)}>N{level} {label}</span>
}
