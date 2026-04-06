import React, { useEffect, useState } from 'react'
import { metrics } from '../api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Line, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler)

function SleepScore({ score }) {
  const color = score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400'
  return (
    <div className="text-center">
      <div className={`text-5xl font-bold ${color}`}>{score ?? '—'}</div>
      <div className="text-gray-500 text-sm mt-1">Sleep score</div>
    </div>
  )
}

export default function Sleep() {
  const [data, setData] = useState([])
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    metrics.daily(days).then(r => setData(r.data.reverse())).finally(() => setLoading(false))
  }, [days])

  if (loading) return <div className="text-gray-400 py-12 text-center">Загрузка...</div>

  const labels = data.map(r => format(new Date(r.date + 'T12:00'), 'd MMM', { locale: ru }))

  const scoreData = {
    labels,
    datasets: [{
      label: 'Sleep score',
      data: data.map(r => r.sleep_score),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
    }]
  }

  const phasesData = {
    labels,
    datasets: [
      {
        label: 'Глубокий',
        data: data.map(r => r.deep_sleep_sec ? Math.round(r.deep_sleep_sec / 60) : null),
        backgroundColor: 'rgba(99,102,241,0.8)',
        borderRadius: 3,
      },
      {
        label: 'REM',
        data: data.map(r => r.rem_sleep_sec ? Math.round(r.rem_sleep_sec / 60) : null),
        backgroundColor: 'rgba(168,85,247,0.8)',
        borderRadius: 3,
      },
      {
        label: 'Лёгкий',
        data: data.map(r => r.light_sleep_sec ? Math.round(r.light_sleep_sec / 60) : null),
        backgroundColor: 'rgba(148,163,184,0.5)',
        borderRadius: 3,
      },
      {
        label: 'Бодрствование',
        data: data.map(r => r.awake_sec ? Math.round(r.awake_sec / 60) : null),
        backgroundColor: 'rgba(251,146,60,0.8)',
        borderRadius: 3,
      },
    ]
  }

  const lineOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#6b7280', font: { size: 11 }, maxTicksLimit: 15 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#6b7280', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
  }

  const barOpts = {
    ...lineOpts,
    plugins: { legend: { labels: { color: '#9ca3af', font: { size: 12 } } } },
    scales: {
      ...lineOpts.scales,
      y: { ...lineOpts.scales.y, stacked: true, title: { display: true, text: 'мин', color: '#6b7280' } },
      x: { ...lineOpts.scales.x, stacked: true },
    }
  }

  const latest = data[data.length - 1]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">💤 Сон</h1>
        <div className="flex gap-2">
          {[14, 30, 60, 90].map(d => (
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

      {/* Latest night summary */}
      {latest && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="col-span-1 rounded-xl border border-blue-500/30 bg-blue-500/5 p-4 flex items-center justify-center">
            <SleepScore score={latest.sleep_score} />
          </div>
          {[
            { icon: '🔵', label: 'Глубокий', val: latest.deep_sleep_sec ? `${Math.round(latest.deep_sleep_sec / 60)} мин` : '—' },
            { icon: '🟣', label: 'REM', val: latest.rem_sleep_sec ? `${Math.round(latest.rem_sleep_sec / 60)} мин` : '—' },
            { icon: '🟠', label: 'Бодрствование', val: latest.awake_sec ? `${Math.round(latest.awake_sec / 60)} мин` : '—' },
            { icon: '❤️', label: 'HRV средний', val: latest.hrv_last_night_avg ? `${latest.hrv_last_night_avg} мс` : '—' },
            { icon: '💗', label: 'Пульс покоя', val: latest.resting_hr ? `${latest.resting_hr} BPM` : '—' },
          ].map(item => (
            <div key={item.label} className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
              <div className="text-gray-400 text-sm mb-1">{item.icon} {item.label}</div>
              <div className="text-white font-semibold">{item.val}</div>
            </div>
          ))}
        </div>
      )}

      {/* Sleep score chart */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">📈 Sleep score по дням</h3>
        <div className="h-48">
          <Line data={scoreData} options={lineOpts} />
        </div>
      </div>

      {/* Phases chart */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">🌙 Фазы сна</h3>
        <div className="h-48">
          <Bar data={phasesData} options={barOpts} />
        </div>
      </div>

      {/* HRV trend */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">❤️ HRV средний по ночам</h3>
          {latest && latest.hrv_last_night_avg && (
            <div className="flex items-center gap-3 text-xs">
              <span className={`px-2 py-1 rounded-full font-medium ${
                latest.hrv_status === 'BALANCED' ? 'bg-green-500/20 text-green-400' :
                latest.hrv_status === 'UNBALANCED' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {latest.hrv_status === 'BALANCED' ? '✓ Сбалансирован' :
                 latest.hrv_status === 'UNBALANCED' ? '⚠ Несбалансирован' :
                 latest.hrv_status || '—'}
              </span>
              {latest.hrv_baseline_low && latest.hrv_baseline_high && (
                <span className="text-gray-400">
                  Норма: {latest.hrv_baseline_low}–{latest.hrv_baseline_high} мс
                </span>
              )}
            </div>
          )}
        </div>
        <div className="h-48">
          <Line
            data={{
              labels,
              datasets: [
                {
                  label: 'HRV средний',
                  data: data.map(r => r.hrv_last_night_avg),
                  borderColor: '#a855f7',
                  backgroundColor: 'rgba(168,85,247,0.1)',
                  fill: true,
                  tension: 0.3,
                  pointRadius: 3,
                },
                ...(latest?.hrv_baseline_low && latest?.hrv_baseline_high ? [{
                  label: 'Норма (нижняя)',
                  data: data.map(() => latest.hrv_baseline_low),
                  borderColor: 'rgba(34,197,94,0.4)',
                  borderDash: [4, 4],
                  borderWidth: 1,
                  pointRadius: 0,
                  fill: false,
                }, {
                  label: 'Норма (верхняя)',
                  data: data.map(() => latest.hrv_baseline_high),
                  borderColor: 'rgba(34,197,94,0.4)',
                  borderDash: [4, 4],
                  borderWidth: 1,
                  pointRadius: 0,
                  fill: '-1',
                  backgroundColor: 'rgba(34,197,94,0.05)',
                }] : [])
              ]
            }}
            options={lineOpts}
          />
        </div>
      </div>

      {/* Sleep table */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-x-auto">
        <h3 className="text-sm font-semibold text-gray-300 p-4 border-b border-gray-800">📋 История сна</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              {['Дата', 'Score', 'Глубокий', 'REM', 'Лёгкий', 'Бодрствование', 'HRV avg', 'HRV статус', 'Пульс покоя'].map(h => (
                <th key={h} className="text-left p-3 text-gray-400 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...data].reverse().map(r => (
              <tr key={r.date} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="p-3 text-gray-300">{format(new Date(r.date + 'T12:00'), 'd MMM', { locale: ru })}</td>
                <td className="p-3">
                  <span className={`font-semibold ${r.sleep_score >= 80 ? 'text-green-400' : r.sleep_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {r.sleep_score ?? '—'}
                  </span>
                </td>
                <td className="p-3 text-gray-300">{r.deep_sleep_sec ? `${Math.round(r.deep_sleep_sec / 60)} мин` : '—'}</td>
                <td className="p-3 text-gray-300">{r.rem_sleep_sec ? `${Math.round(r.rem_sleep_sec / 60)} мин` : '—'}</td>
                <td className="p-3 text-gray-300">{r.light_sleep_sec ? `${Math.round(r.light_sleep_sec / 60)} мин` : '—'}</td>
                <td className="p-3 text-orange-300">{r.awake_sec ? `${Math.round(r.awake_sec / 60)} мин` : '—'}</td>
                <td className="p-3 text-gray-300">{r.hrv_last_night_avg ? `${r.hrv_last_night_avg} мс` : '—'}</td>
                <td className="p-3">
                  {r.hrv_status ? (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      r.hrv_status === 'BALANCED' ? 'bg-green-500/20 text-green-400' :
                      r.hrv_status === 'UNBALANCED' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {r.hrv_status === 'BALANCED' ? 'Норма' : r.hrv_status === 'UNBALANCED' ? 'Несбаланс.' : r.hrv_status}
                    </span>
                  ) : '—'}
                </td>
                <td className="p-3 text-gray-300">{r.resting_hr ? `${r.resting_hr} BPM` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
