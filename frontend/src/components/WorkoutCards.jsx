import React from 'react'

const ACTIVITY_ICONS = {
  running: '🏃',
  cycling: '🚴',
  swimming: '🏊',
  strength_training: '🏋️',
  yoga: '🧘',
  walking: '🚶',
  hiking: '🥾',
  cardio: '💪',
}

function formatDuration(sec) {
  if (!sec) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (h > 0) return `${h}ч ${m}мин`
  return `${m} мин`
}

function formatDistance(meters) {
  if (!meters) return null
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} км`
  return `${Math.round(meters)} м`
}

export default function WorkoutCards({ activities = [] }) {
  if (!activities.length) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-center text-gray-500">
        Тренировок за этот день нет
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">🏋️ Тренировки</h3>
      <div className="space-y-3">
        {activities.map(act => {
          const icon = ACTIVITY_ICONS[act.activity_type] || '🏅'
          const zones = act.hr_zones_json || []
          return (
            <div key={act.id} className="rounded-lg bg-gray-800/50 p-3 border border-gray-700/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{icon}</span>
                  <span className="text-sm font-medium text-gray-200 capitalize">
                    {act.activity_type?.replace(/_/g, ' ') || 'Тренировка'}
                  </span>
                </div>
                <span className="text-xs text-gray-500">{formatDuration(act.duration_sec)}</span>
              </div>
              <div className="flex gap-4 text-xs text-gray-400 flex-wrap">
                {act.avg_hr && <span>💗 Ср: {act.avg_hr} BPM</span>}
                {act.max_hr && <span>🔴 Макс: {act.max_hr} BPM</span>}
                {act.calories && <span>🔥 {act.calories} ккал</span>}
                {formatDistance(act.distance_meters) && <span>📏 {formatDistance(act.distance_meters)}</span>}
              </div>
              {zones.length > 0 && (
                <div className="mt-2 flex gap-1">
                  {zones.map((z, i) => {
                    const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-orange-500', 'bg-red-500']
                    const secs = z.secsInZone || z.seconds || 0
                    if (!secs) return null
                    return (
                      <div
                        key={i}
                        className={`h-1 rounded-full ${colors[i] || 'bg-gray-500'}`}
                        style={{ flex: secs }}
                        title={`Зона ${i + 1}: ${Math.round(secs / 60)} мин`}
                      />
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
