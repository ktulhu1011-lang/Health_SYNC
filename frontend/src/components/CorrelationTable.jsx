import React, { useState } from 'react'

const METRIC_LABELS = {
  sleep_score: '💤 Sleep score',
  hrv_last_night_avg: '❤️ HRV',
  resting_hr: '💗 Пульс покоя',
  avg_stress: '😤 Стресс',
  body_battery_charged: '🔋 Body Battery',
}

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
  subjective_stress: '😤 Стресс субъект.',
  nutrition_quality: '🥗 Качество еды',
  late_eating: '🌙 Позд. еда',
  pre_sleep_eating: '🕐 Еда за 2ч до сна',
  had_workout: '🏋️ Тренировка',
  // Supplements
  supp_magnesium: '💊 Магний',
  supp_vitamin_d: '💊 Витамин D',
  supp_vitamin_c: '💊 Витамин C',
  supp_zinc: '💊 Цинк',
  supp_omega3: '💊 Омега-3',
  supp_ashwagandha: '🌿 Ашваганда',
  supp_theanine: '🌿 Теанин',
  supp_melatonin: '🌙 Мелатонин',
  supp_5htp: '🌿 5-HTP',
  supp_glycine: '💊 Глицин',
  supp_coq10: '💊 CoQ10',
  supp_b_complex: '💊 B-комплекс',
}

function deltaColor(delta, metric) {
  if (!delta && delta !== 0) return 'text-gray-500'
  // For resting_hr and stress: negative delta is GOOD
  const invertedMetrics = ['resting_hr', 'avg_stress']
  const good = invertedMetrics.includes(metric) ? delta < 0 : delta > 0
  if (Math.abs(delta) < 1) return 'text-gray-400'
  return good ? 'text-green-400' : 'text-red-400'
}

function DeltaBadge({ delta, metric }) {
  if (delta === null || delta === undefined) return <span className="text-gray-600">—</span>
  const cls = deltaColor(delta, metric)
  const sign = delta > 0 ? '+' : ''
  return <span className={`font-semibold ${cls}`}>{sign}{delta.toFixed(1)}</span>
}

export default function CorrelationTable({ data = [] }) {
  const [sortMetric, setSortMetric] = useState('sleep_score')

  if (!data.length) {
    return (
      <div className="rounded-xl border border-gray-800 p-6 text-center text-gray-500">
        Недостаточно данных для корреляций. Нужно минимум 14 дней.
      </div>
    )
  }

  // Group by habit
  const byHabit = {}
  data.forEach(row => {
    if (!byHabit[row.habit_key]) byHabit[row.habit_key] = {}
    byHabit[row.habit_key][row.metric] = row
  })

  const metrics = ['sleep_score', 'hrv_last_night_avg', 'resting_hr', 'avg_stress', 'body_battery_charged']

  const sortedHabits = Object.keys(byHabit).sort((a, b) => {
    const da = byHabit[a][sortMetric]?.delta || 0
    const db = byHabit[b][sortMetric]?.delta || 0
    const invert = ['resting_hr', 'avg_stress'].includes(sortMetric)
    return invert ? da - db : db - da
  })

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-x-auto">
      <div className="p-4 border-b border-gray-800 flex gap-2 flex-wrap">
        <span className="text-xs text-gray-400 mr-2 self-center">Сортировать по:</span>
        {metrics.map(m => (
          <button
            key={m}
            onClick={() => setSortMetric(m)}
            className={`text-xs px-2 py-1 rounded-full border transition-colors ${
              sortMetric === m
                ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                : 'border-gray-700 text-gray-400 hover:border-gray-600'
            }`}
          >
            {METRIC_LABELS[m] || m}
          </button>
        ))}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left p-3 text-gray-400 font-medium">Привычка</th>
            {metrics.map(m => (
              <th key={m} className="text-center p-3 text-gray-400 font-medium">
                {METRIC_LABELS[m] || m}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedHabits.map(habit => (
            <tr key={habit} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
              <td className="p-3 text-gray-200">
                {HABIT_LABELS[habit] || habit}
              </td>
              {metrics.map(metric => {
                const row = byHabit[habit][metric]
                return (
                  <td key={metric} className="p-3 text-center">
                    {row ? (
                      <div>
                        <DeltaBadge delta={row.delta} metric={metric} />
                        <div className="text-xs text-gray-500 mt-0.5">
                          {row.avg_with?.toFixed(1)} vs {row.avg_without?.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-600">n={row.days_with}</div>
                      </div>
                    ) : (
                      <span className="text-gray-700">—</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="p-3 text-xs text-gray-500 border-t border-gray-800">
        Дельта = среднее "с привычкой" − "без привычки". Зелёный = хорошо, красный = плохо.
      </div>
    </div>
  )
}
