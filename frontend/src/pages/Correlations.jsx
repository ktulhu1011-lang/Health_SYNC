import React, { useEffect, useState } from 'react'
import { metrics } from '../api'
import { Scatter } from 'react-chartjs-2'
import {
  Chart as ChartJS, LinearScale, PointElement, Tooltip, Legend
} from 'chart.js'
import CorrelationTable from '../components/CorrelationTable'

ChartJS.register(LinearScale, PointElement, Tooltip, Legend)

const METRIC_LABELS = {
  sleep_score: '💤 Sleep score',
  hrv_last_night_avg: '❤️ HRV',
  resting_hr: '💗 Пульс покоя',
  avg_stress: '😤 Стресс',
  body_battery_charged: '🔋 Body Battery',
  awake_sec: '🟠 Бодрствование',
}

export default function Correlations() {
  const [data, setData] = useState([])
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    metrics.correlations(days).then(r => setData(r.data)).finally(() => setLoading(false))
  }, [days])

  if (loading) return <div className="text-gray-400 py-12 text-center">Загрузка...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">📊 Корреляции</h1>
          <p className="text-gray-500 text-sm mt-1">Как привычки влияют на биометрику</p>
        </div>
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

      {data.length < 5 ? (
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-6 text-center">
          <div className="text-yellow-400 text-lg mb-2">📊</div>
          <p className="text-yellow-300 font-medium">Недостаточно данных</p>
          <p className="text-gray-400 text-sm mt-1">Нужно минимум 14 дней совместных данных привычек и Garmin</p>
        </div>
      ) : (
        <CorrelationTable data={data} />
      )}
    </div>
  )
}
