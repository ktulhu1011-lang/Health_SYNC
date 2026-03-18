import React, { useState, useEffect } from 'react'
import { heart } from '../api'
import { format, subDays, addDays } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend
} from 'chart.js'
import HourlyHeartChart from '../components/HourlyHeartChart'
import HeartZones from '../components/HeartZones'
import WorkoutCards from '../components/WorkoutCards'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function HeartRate() {
  const [selectedDate, setSelectedDate] = useState(format(subDays(new Date(), 1), 'yyyy-MM-dd'))
  const [intraday, setIntraday] = useState([])
  const [activities, setActivities] = useState([])
  const [trend, setTrend] = useState([])
  const [trendDays, setTrendDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [recentActivities, setRecentActivities] = useState([])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      heart.intraday(selectedDate).then(r => setIntraday(r.data)),
      heart.activities(selectedDate).then(r => setActivities(r.data)),
    ]).finally(() => setLoading(false))
  }, [selectedDate])

  useEffect(() => {
    heart.recentActivities(14).then(r => setRecentActivities(r.data))
  }, [])

  useEffect(() => {
    heart.trend(trendDays).then(r => setTrend(r.data))
  }, [trendDays])

  function prevDay() {
    setSelectedDate(d => format(subDays(new Date(d + 'T12:00'), 1), 'yyyy-MM-dd'))
  }
  function nextDay() {
    const next = addDays(new Date(selectedDate + 'T12:00'), 1)
    if (next <= new Date()) {
      setSelectedDate(format(next, 'yyyy-MM-dd'))
    }
  }

  // Trend chart data
  const trendData = {
    labels: trend.map(r => format(new Date(r.date + 'T12:00'), 'd MMM', { locale: ru })),
    datasets: [
      {
        label: 'Пульс покоя',
        data: trend.map(r => r.resting_hr),
        backgroundColor: 'rgba(239,68,68,0.7)',
        borderRadius: 3,
      },
      {
        label: 'Средний пульс',
        data: trend.map(r => r.avg_hr),
        backgroundColor: 'rgba(59,130,246,0.5)',
        borderRadius: 3,
      },
    ]
  }

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#9ca3af', font: { size: 12 } }
      }
    },
    scales: {
      x: { ticks: { color: '#6b7280', font: { size: 11 }, maxTicksLimit: 15 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#6b7280', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'BPM', color: '#6b7280' } }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">💗 Пульс</h1>
      </div>

      {/* Date navigation */}
      <div className="flex items-center gap-3">
        <button onClick={prevDay} className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors">←</button>
        <input
          type="date"
          value={selectedDate}
          max={format(new Date(), 'yyyy-MM-dd')}
          onChange={e => setSelectedDate(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 text-sm"
        />
        <button onClick={nextDay} className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors">→</button>
        <span className="text-gray-400 text-sm">
          {format(new Date(selectedDate + 'T12:00'), 'EEEE, d MMMM', { locale: ru })}
        </span>
      </div>

      {loading ? (
        <div className="text-gray-400 py-8 text-center">Загрузка...</div>
      ) : (
        <>
          {/* Widget 1 — Hourly chart */}
          <HourlyHeartChart data={intraday} activities={activities} />

          {/* Widget 2 & 3 */}
          <div className="grid md:grid-cols-2 gap-4">
            <HeartZones intradayData={intraday} />
            <WorkoutCards activities={activities} />
          </div>
        </>
      )}

      {/* Recent workouts across all days */}
      {recentActivities.length > 0 && (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">🏋️ Последние тренировки (14 дней)</h3>
          <div className="space-y-2">
            {recentActivities.map(act => {
              const ICONS = { running:'🏃', cycling:'🚴', swimming:'🏊', strength_training:'🏋️', yoga:'🧘', walking:'🚶', hiking:'🥾', cardio:'💪', hiit:'⚡', paddelball:'🏓' }
              const icon = ICONS[act.activity_type] || '🏅'
              const dur = act.duration_sec ? (act.duration_sec >= 3600 ? `${Math.floor(act.duration_sec/3600)}ч ${Math.floor((act.duration_sec%3600)/60)}мин` : `${Math.floor(act.duration_sec/60)} мин`) : '—'
              const dist = act.distance_meters >= 1000 ? `${(act.distance_meters/1000).toFixed(1)} км` : act.distance_meters > 0 ? `${Math.round(act.distance_meters)} м` : null
              return (
                <div key={act.id} className="flex items-center justify-between rounded-lg bg-gray-800/50 px-3 py-2 border border-gray-700/50">
                  <div className="flex items-center gap-2 min-w-0">
                    <span>{icon}</span>
                    <span className="text-sm text-gray-200 capitalize truncate">{act.activity_type?.replace(/_/g,' ') || 'Тренировка'}</span>
                    <span className="text-xs text-gray-500">{format(new Date(act.date + 'T12:00'), 'd MMM', { locale: ru })}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400 shrink-0">
                    {act.avg_hr && <span>💗{act.avg_hr}</span>}
                    {act.calories && <span>🔥{act.calories}</span>}
                    {dist && <span>📏{dist}</span>}
                    <span className="text-gray-500">{dur}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Widget 4 — Trend */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">📊 Тренд пульса</h3>
          <div className="flex gap-2">
            {[30, 60, 90].map(d => (
              <button
                key={d}
                onClick={() => setTrendDays(d)}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  trendDays === d
                    ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                    : 'border-gray-700 text-gray-400 hover:border-gray-600'
                }`}
              >
                {d} дн
              </button>
            ))}
          </div>
        </div>
        <div className="h-48">
          {trend.length > 0 ? (
            <Bar data={trendData} options={trendOptions} />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">Нет данных</div>
          )}
        </div>
      </div>
    </div>
  )
}
