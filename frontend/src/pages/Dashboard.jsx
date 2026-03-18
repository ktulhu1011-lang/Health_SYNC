import React, { useEffect, useState } from 'react'
import { metrics, habits, insights } from '../api'
import { format, subDays } from 'date-fns'
import { ru } from 'date-fns/locale'

function MetricCard({ label, value, unit, color = 'blue', icon }) {
  const colors = {
    blue: 'border-blue-500/30 bg-blue-500/5',
    green: 'border-green-500/30 bg-green-500/5',
    purple: 'border-purple-500/30 bg-purple-500/5',
    orange: 'border-orange-500/30 bg-orange-500/5',
    red: 'border-red-500/30 bg-red-500/5',
  }
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">{icon} {label}</div>
      <div className="text-2xl font-bold text-white">
        {value !== null && value !== undefined ? value : <span className="text-gray-600">—</span>}
        {value !== null && value !== undefined && unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [garmin, setGarmin] = useState(null)
  const [todayHabits, setTodayHabits] = useState([])
  const [lastInsight, setLastInsight] = useState(null)
  const [loading, setLoading] = useState(true)

  const yesterday = format(subDays(new Date(), 1), 'yyyy-MM-dd')

  useEffect(() => {
    Promise.all([
      metrics.dailyByDate(yesterday).then(r => setGarmin(r.data)).catch(() => {}),
      habits.today().then(r => setTodayHabits(r.data)).catch(() => {}),
      insights.list(1).then(r => setLastInsight(r.data[0] || null)).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-400 py-12 text-center">Загрузка...</div>

  const habitsGrouped = todayHabits.reduce((acc, h) => {
    if (!acc[h.category]) acc[h.category] = []
    acc[h.category].push(h)
    return acc
  }, {})

  const categoryLabels = {
    bad_habits: '🚬 Вредные привычки',
    supplements: '💊 Добавки',
    nutrition: '🥗 Питание',
    water: '💧 Вода',
    wellbeing: '🧘 Самочувствие',
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Сводка</h1>
        <p className="text-gray-500 text-sm mt-1">
          {format(new Date(), 'd MMMM yyyy', { locale: ru })}
        </p>
      </div>

      {/* Garmin Metrics */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          📡 Garmin — {format(subDays(new Date(), 1), 'd MMMM', { locale: ru })}
        </h2>
        {garmin ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <MetricCard icon="💤" label="Sleep score" value={garmin.sleep_score} color="blue" />
            <MetricCard icon="💗" label="Пульс покоя" value={garmin.resting_hr} unit="BPM" color="red" />
            <MetricCard icon="❤️" label="HRV средний" value={garmin.hrv_last_night_avg ? `${garmin.hrv_last_night_avg} мс` : null} color="purple" />
            <MetricCard icon="😌" label="Стресс" value={garmin.avg_stress} color="orange" />
            <MetricCard icon="🔋" label="Body Battery" value={garmin.body_battery_charged} color="green" />
          </div>
        ) : (
          <div className="rounded-xl border border-gray-800 p-4 text-gray-500 text-sm">
            Данные Garmin ещё не синхронизированы.
            Синхронизация происходит ночью в 03:00, или выполни её вручную в разделе «Настройки».
          </div>
        )}
      </div>

      {/* Sleep Details */}
      {garmin && (garmin.deep_sleep_sec || garmin.rem_sleep_sec) && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">💤 Фазы сна</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard icon="🔵" label="Глубокий" value={garmin.deep_sleep_sec ? Math.round(garmin.deep_sleep_sec / 60) : null} unit="мин" color="blue" />
            <MetricCard icon="🟣" label="REM" value={garmin.rem_sleep_sec ? Math.round(garmin.rem_sleep_sec / 60) : null} unit="мин" color="purple" />
            <MetricCard icon="⚪" label="Лёгкий" value={garmin.light_sleep_sec ? Math.round(garmin.light_sleep_sec / 60) : null} unit="мин" color="blue" />
            <MetricCard icon="❤️" label="HRV статус" value={garmin.hrv_status} color={garmin.hrv_status === 'BALANCED' ? 'green' : 'orange'} />
          </div>
        </div>
      )}

      {/* Today's habits */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          📋 Привычки сегодня
        </h2>
        {Object.keys(habitsGrouped).length === 0 ? (
          <div className="rounded-xl border border-gray-800 p-4 text-gray-500 text-sm">
            Данные ещё не внесены. Используй /log в Telegram.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(habitsGrouped).map(([cat, logs]) => (
              <div key={cat} className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">
                  {categoryLabels[cat] || cat}
                </h3>
                <div className="space-y-1">
                  {logs.map(log => (
                    <div key={log.id} className="flex justify-between text-sm">
                      <span className="text-gray-400">{log.habit_key}</span>
                      <span className="text-gray-200 font-medium">
                        {typeof log.value === 'object' ? JSON.stringify(log.value) : String(log.value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Last AI insight */}
      {lastInsight && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">🤖 Последний AI-инсайт</h2>
          <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-5">
            <div className="flex justify-between items-start mb-3">
              <span className="text-xs text-purple-400 uppercase tracking-wider">
                {lastInsight.trigger_type === 'weekly' ? '📅 Еженедельный' :
                 lastInsight.trigger_type === 'on_demand' ? '🖱 По запросу' : '⚡ Триггерный'}
              </span>
              <span className="text-xs text-gray-500">
                {format(new Date(lastInsight.generated_at), 'd MMM HH:mm', { locale: ru })}
              </span>
            </div>
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {lastInsight.insight_text}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
