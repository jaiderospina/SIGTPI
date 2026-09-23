import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { notifApi } from "@/services/api"
import { Bell, Check, CheckCheck, Info, AlertTriangle, Calendar, FileText, Clock } from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"
import EmptyState from "@/components/EmptyState"

const typeIcon: Record<string, React.ElementType> = {
  assignment:   FileText,
  session:      Calendar,
  advance:      Info,
  alert:        AlertTriangle,
  evaluation:   CheckCheck,
  milestone:    Clock,
  info:         Info,
}

const typeBg: Record<string, string> = {
  assignment: "bg-blue-50 border-blue-200",
  session:    "bg-purple-50 border-purple-200",
  advance:    "bg-green-50 border-green-200",
  alert:      "bg-red-50 border-red-200",
  evaluation: "bg-orange-50 border-orange-200",
  milestone:  "bg-yellow-50 border-yellow-200",
  info:       "bg-gray-50 border-gray-200",
}

const typeIconBg: Record<string, string> = {
  assignment: "bg-blue-100 text-blue-700",
  session:    "bg-purple-100 text-purple-700",
  advance:    "bg-green-100 text-green-700",
  alert:      "bg-red-100 text-red-700",
  evaluation: "bg-orange-100 text-orange-700",
  milestone:  "bg-yellow-100 text-yellow-700",
  info:       "bg-gray-100 text-gray-600",
}

export default function Notifications() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notifApi.list({ page_size: 50 }).then(r => r.data),
    refetchInterval: 30_000,
  })

  const { data: unread } = useQuery({
    queryKey: ["notif-unread"],
    queryFn: () => notifApi.unread().then(r => r.data),
    refetchInterval: 15_000,
  })

  const markRead = useMutation({
    mutationFn: (id: string) => notifApi.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] })
      qc.invalidateQueries({ queryKey: ["notif-unread"] })
    },
  })

  const markAllRead = useMutation({
    mutationFn: async () => {
      const unreadItems = (data?.items ?? []).filter((n: any) => !n.is_read)
      await Promise.all(unreadItems.map((n: any) => notifApi.markRead(n.id)))
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] })
      qc.invalidateQueries({ queryKey: ["notif-unread"] })
    },
  })

  const items: any[] = data?.items ?? data ?? []
  const unreadCount = unread?.unread_count ?? items.filter((n:any) => !n.is_read).length

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="w-5 h-5"/>
            Notificaciones
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{items.length} en total · {unreadCount} sin leer</p>
        </div>
        {unreadCount > 0 && (
          <button onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
            className="btn-secondary text-sm flex items-center gap-2">
            <CheckCheck className="w-4 h-4"/>
            {markAllRead.isPending ? "Marcando..." : "Marcar todas como leídas"}
          </button>
        )}
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1,2,3,4].map(i => <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse"/>)}
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <EmptyState icon={Bell} title="Sin notificaciones"
          description="Aquí aparecerán los eventos importantes del sistema."/>
      )}

      <div className="space-y-2">
        {items.map((n: any) => {
          const Icon = typeIcon[n.notification_type] ?? Info
          return (
            <div key={n.id}
              className={clsx(
                "flex items-start gap-3 p-4 rounded-xl border transition-all",
                n.is_read ? "bg-white border-gray-100 opacity-70" : typeBg[n.notification_type] ?? typeBg.info
              )}>
              <div className={clsx("w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
                n.is_read ? "bg-gray-100 text-gray-400" : (typeIconBg[n.notification_type] ?? typeIconBg.info))}>
                <Icon className="w-4 h-4"/>
              </div>
              <div className="flex-1 min-w-0">
                {n.subject && (
                  <p className={clsx("text-sm font-semibold mb-0.5",
                    n.is_read ? "text-gray-500" : "text-gray-900")}>
                    {n.subject}
                  </p>
                )}
                <p className={clsx("text-sm", n.is_read ? "text-gray-400" : "text-gray-700")}>
                  {n.body ?? n.message}
                </p>
                <p className="text-xs text-gray-400 mt-1.5">
                  {format(parseISO(n.created_at ?? n.sent_at ?? new Date().toISOString()),
                    "d MMM yyyy · HH:mm", { locale: es })}
                </p>
              </div>
              {!n.is_read && (
                <button onClick={() => markRead.mutate(n.id)}
                  className="flex-shrink-0 p-1.5 text-gray-400 hover:text-green-600 hover:bg-white rounded-lg transition-colors"
                  title="Marcar como leída">
                  <Check className="w-4 h-4"/>
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
