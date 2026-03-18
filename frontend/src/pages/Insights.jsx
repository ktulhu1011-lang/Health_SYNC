import React, { useEffect, useState } from 'react'
import { insights } from '../api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const TRIGGER_LABELS = {
  weekly: '📅 Еженедельный',
  on_demand: '🖱 По запросу',
  triggered: '⚡ Триггерный',
}

const TRIGGER_COLORS = {
  weekly: 'border-blue-500/30 bg-blue-500/5',
  on_demand: 'border-purple-500/30 bg-purple-500/5',
  triggered: 'border-orange-500/30 bg-orange-500/5',
}

export default function Insights() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  function load() {
    setLoading(true)
    insights.list(50).then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    try {
      await insights.generate()
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка генерации')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🤖 AI-инсайты</h1>
          <p className="text-gray-500 text-sm mt-1">Анализ корреляций привычек с биометрикой</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {generating ? '⏳ Генерирую...' : '✨ Запросить инсайт'}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 py-12 text-center">Загрузка...</div>
      ) : data.length === 0 ? (
        <div className="rounded-xl border border-gray-800 p-8 text-center">
          <div className="text-4xl mb-3">📊</div>
          <p className="text-gray-300 font-medium">Инсайтов пока нет</p>
          <p className="text-gray-500 text-sm mt-1">Нажми «Запросить инсайт» или дождись воскресенья</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.map(insight => (
            <div key={insight.id} className={`rounded-xl border p-5 ${TRIGGER_COLORS[insight.trigger_type] || 'border-gray-800 bg-gray-900/50'}`}>
              <div className="flex justify-between items-start mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  {TRIGGER_LABELS[insight.trigger_type] || insight.trigger_type}
                </span>
                <span className="text-xs text-gray-500">
                  {format(new Date(insight.generated_at), 'd MMMM yyyy, HH:mm', { locale: ru })}
                </span>
              </div>
              <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
                {insight.insight_text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
