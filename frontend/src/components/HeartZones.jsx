import React from 'react'

const ZONES = [
  { id: 1, label: 'Зона 1 — Покой', desc: '< 50% макс', color: 'bg-blue-500', textColor: 'text-blue-400' },
  { id: 2, label: 'Зона 2 — Жиросжигание', desc: '50–60%', color: 'bg-green-500', textColor: 'text-green-400' },
  { id: 3, label: 'Зона 3 — Аэробная', desc: '60–70%', color: 'bg-yellow-500', textColor: 'text-yellow-400' },
  { id: 4, label: 'Зона 4 — Анаэробная', desc: '70–85%', color: 'bg-orange-500', textColor: 'text-orange-400' },
  { id: 5, label: 'Зона 5 — Максимум', desc: '85–100%', color: 'bg-red-500', textColor: 'text-red-400' },
]

export default function HeartZones({ hrZones = null, intradayData = [] }) {
  // Calculate zone times from intraday data if hrZones not provided
  let zoneTimes = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
  let totalMinutes = 0

  if (hrZones) {
    hrZones.forEach(z => {
      const zoneId = z.zoneNumber || z.zone
      if (zoneId >= 1 && zoneId <= 5) {
        const mins = Math.round((z.secsInZone || z.seconds || 0) / 60)
        zoneTimes[zoneId] = mins
        totalMinutes += mins
      }
    })
  } else if (intradayData.length > 0) {
    intradayData.forEach(p => {
      const pct = (p.bpm / 190) * 100
      let zone = 1
      if (pct >= 85) zone = 5
      else if (pct >= 70) zone = 4
      else if (pct >= 60) zone = 3
      else if (pct >= 50) zone = 2
      zoneTimes[zone] += 0.25  // ~15 min intervals
      totalMinutes += 0.25
    })
    Object.keys(zoneTimes).forEach(k => {
      zoneTimes[k] = Math.round(zoneTimes[k])
    })
    totalMinutes = Math.round(totalMinutes)
  }

  if (totalMinutes === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-center text-gray-500">
        Нет данных зон пульса
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">🎯 Зоны пульса за день</h3>
      <div className="space-y-3">
        {ZONES.map(zone => {
          const mins = zoneTimes[zone.id] || 0
          const pct = totalMinutes > 0 ? (mins / totalMinutes) * 100 : 0
          return (
            <div key={zone.id}>
              <div className="flex justify-between text-xs mb-1">
                <span className={zone.textColor}>{zone.label}</span>
                <span className="text-gray-400">{mins} мин ({pct.toFixed(0)}%)</span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${zone.color} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-gray-500 mt-3">Всего: {totalMinutes} мин</p>
    </div>
  )
}
