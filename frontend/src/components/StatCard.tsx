import clsx from "clsx"
import type { LucideIcon } from "lucide-react"

interface Props {
  title: string
  value: string | number
  icon: LucideIcon
  color?: "blue" | "green" | "amber" | "red" | "purple"
  subtitle?: string
}

const colorMap = {
  blue:   { bg: "bg-primary-50",   icon: "bg-primary-700  text-white",  text: "text-primary-700"  },
  green:  { bg: "bg-success-light", icon: "bg-success      text-white",  text: "text-success"      },
  amber:  { bg: "bg-warning-light", icon: "bg-warning      text-white",  text: "text-warning"      },
  red:    { bg: "bg-danger-light",  icon: "bg-danger       text-white",  text: "text-danger"       },
  purple: { bg: "bg-info-light",    icon: "bg-info         text-white",  text: "text-info"         },
}

export default function StatCard({ title, value, icon: Icon, color = "blue", subtitle }: Props) {
  const c = colorMap[color]
  return (
    <div className={clsx("rounded-xl p-5 flex items-center gap-4", c.bg)}>
      <div className={clsx("w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0", c.icon)}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className={clsx("text-2xl font-bold", c.text)}>{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}
