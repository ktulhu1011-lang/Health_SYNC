import React from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

const ZONE_COLORS = {
  1: 'rgba(59,130,246,0.15)',   // blue — rest
  2: 'rgba(34,197,94,0.15)',    // green — fat burn
  3: 'rgba(234,179,8,0.15)',    // yellow — aerobic
  4: 'rgba(249,115,22,0.15)',   // orange — anaerobic
  5: 'rgba(239,68,68,0.15)',    // red — max
}

function getZone(bpm, maxHR = 190) {
  const pct = (bpm / maxHR) * 100
  if (pct < 50) return 1
  if (pct < 60) return 2
  if (pct < 70) return 3
  if (pct < 85) return 4
  return 5
}

export default function HourlyHeartChart({ data = [], activities = [] }) {
  if (!data.length) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-center text-gray-500">
        Нет данных почасового пульса за этот день
      </div>
    )
  }

  const labels = data.map(p => {
    const d = new Date(p.timestamp)
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  })
  const bpms = data.map(p => p.bpm)

  // Segment colors by zone
  const pointColors = bpms.map(bpm => {
    const z = getZone(bpm)
    return ['', '#3b82f6', '#22c55e', '#eab308', '#f97316', '#ef4444'][z]
  })

  const chartData = {
    labels,
    datasets: [{
      label: 'Пульс (BPM)',
      data: bpms,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.1)',
      pointBackgroundColor: pointColors,
      pointRadius: 2,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      fill: true,
      tension: 0.3,
    }]
  }

  // Activity markers as vertical annotations
  const activityAnnotations = activities.reduce((acc, act) => {
    if (!act.date) return acc
    acc[`act_${act.id}`] = {
      type: 'line',
      xMin: 0,
      xMax: 0,
      borderColor: 'rgba(168,85,247,0.8)',
      borderWidth: 2,
      label: {
        content: act.activity_type || 'Тренировка',
        enabled: true,
      }
    }
    return acc
  }, {})

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => `${ctx.parsed.y} BPM`,
          afterLabel: ctx => {
            const z = getZone(ctx.parsed.y)
            return `Зона ${z}`
          }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#6b7280', maxTicksLimit: 24, font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        ticks: { color: '#6b7280', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.05)' },
        min: Math.max(0, Math.min(...bpms) - 10),
        title: { display: true, text: 'BPM', color: '#6b7280' }
      }
    }
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">📈 Пульс по часам</h3>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
      <div className="flex gap-4 mt-3 flex-wrap">
        {[
          { z: 1, label: 'Покой', color: '#3b82f6' },
          { z: 2, label: 'Жиросжигание', color: '#22c55e' },
          { z: 3, label: 'Аэробная', color: '#eab308' },
          { z: 4, label: 'Анаэробная', color: '#f97316' },
          { z: 5, label: 'Максимум', color: '#ef4444' },
        ].map(({ z, label, color }) => (
          <div key={z} className="flex items-center gap-1.5 text-xs text-gray-400">
            <div className="w-3 h-3 rounded-full" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
