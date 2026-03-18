import React, { useEffect, useState } from 'react'
import { habits } from '../api'
import { format, subDays, eachDayOfInterval } from 'date-fns'
import { ru } from 'date-fns/locale'

const HABIT_LABELS = {
  smoking: '🚬 Курение',
  alcohol: '🍷 Алкоголь',
  sweets: '🍭 Сладкое',
  fastfood: '🍔 Фастфуд',
  screen_bedtime: '📱 Экран',
  coffee: '☕ Кофе',
  water: '💧 Вода',
  meditation: '🧘 Медитация',
  walk: '🚶 Прогулка',
  feeling: '😊 Самочувствие',
  subjective_stress: '😤 Стресс',
  nutrition_quality: '🥗 Качество еды',
  late_eating: '🌙 Позд. еда',
}

export default function Habits() {
  const [heatmapData, setHeatmapData] = useState({})
  const [historyData, setHistoryData] = useState([])
  const [days, setDays] = useState(90)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      habits.heatmap(days).then(r => setHeatmapData(r.data)),
      habits.history(days).then(r => setHistoryData(r.data)),
    ]).finally(() => setLoading(false))
  }, [days])

  if (loading) return <div className="text-gray-400 py-12 text-center">Загрузка...</div>

  const today = new Date()
  const startDate = subDays(today, days - 1)
  const allDays = eachDayOfInterval({ start: startDate, end: today })

  // Get all habit keys from data
  const allKeys = new Set()
  Object.values(heatmapData).forEach(dayHabits => {
    dayHabits.forEach(h => allKeys.add(h.habit_key))
  })

  function hasHabit(dateStr, key) {
    const dayHabits = heatmapData[dateStr] || []
    return dayHabits.some(h => h.habit_key === key)
  }

  // Group history by date
  const historyByDate = historyData.reduce((acc, h) => {
    const d = h.date
    if (!acc[d]) acc[d] = []
    acc[d].push(h)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">📋 Привычки</h1>
        <div className="flex gap-2">
          {[30, 60, 90].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                days === d ? 'border-blue-500 bg-blue-500/20 text-blue-400' : 'border-gray-700 text-gray-400'
              }`}
            >
              {d} дн
            </button>
          ))}
        </div>
      </div>

      {/* Heatmap */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 overflow-x-auto">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">🗓 Тепловая карта</h3>
        {allKeys.size === 0 ? (
          <div className="text-gray-500 text-sm">Нет данных</div>
        ) : (
          <div className="space-y-2">
            {[...allKeys].map(key => (
              <div key={key} className="flex items-center gap-2">
                <div className="w-32 text-xs text-gray-400 shrink-0 truncate">
                  {HABIT_LABELS[key] || key}
                </div>
                <div className="flex gap-0.5 flex-wrap">
                  {allDays.map(day => {
                    const dateStr = format(day, 'yyyy-MM-dd')
                    const has = hasHabit(dateStr, key)
                    return (
                      <div
                        key={dateStr}
                        title={`${format(day, 'd MMM', { locale: ru })}: ${has ? 'есть' : 'нет'}`}
                        className={`w-3 h-3 rounded-sm transition-colors ${
                          has ? 'bg-blue-500' : 'bg-gray-800'
                        }`}
                      />
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History table */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
        <h3 className="text-sm font-semibold text-gray-300 p-4 border-b border-gray-800">📜 История записей</h3>
        {Object.keys(historyByDate).length === 0 ? (
          <div className="p-6 text-center text-gray-500">Нет записей</div>
        ) : (
          <div className="divide-y divide-gray-800">
            {Object.entries(historyByDate)
              .sort(([a], [b]) => b.localeCompare(a))
              .slice(0, 30)
              .map(([date, logs]) => (
                <div key={date} className="p-4">
                  <div className="text-sm font-semibold text-gray-300 mb-2">
                    {format(new Date(date + 'T12:00'), 'EEEE, d MMMM', { locale: ru })}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {logs.map(log => (
                      <div key={log.id} className="bg-gray-800 rounded-lg px-2 py-1 text-xs">
                        <span className="text-gray-400">{HABIT_LABELS[log.habit_key] || log.habit_key}:</span>{' '}
                        <span className="text-gray-200">
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
    </div>
  )
}
