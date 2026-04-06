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
  const [question, setQuestion] = useState('')
  const [askDays, setAskDays] = useState(30)
  const [asking, setAsking] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [askError, setAskError] = useState('')

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

  async function handleAsk() {
    if (!question.trim()) return
    setAsking(true)
    setAskError('')
    setAnswer(null)
    try {
      const r = await insights.ask(question.trim(), askDays)
      setAnswer(r.data)
    } catch (e) {
      setAskError(e.response?.data?.detail || 'Ошибка запроса')
    } finally {
      setAsking(false)
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

      {/* AI Q&A Block */}
      <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">💬</span>
          <h2 className="text-white font-semibold">Спросить AI</h2>
          <span className="text-xs text-gray-500">— ответит на основе твоих данных здоровья</span>
        </div>
        <div className="flex gap-2 items-start">
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk() } }}
            placeholder={'Например: "Как кофе влияет на мой сон?" или "В какие дни у меня лучший HRV?"'}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
            rows={2}
          />
          <div className="flex flex-col gap-2 shrink-0">
            <select
              value={askDays}
              onChange={e => setAskDays(Number(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none cursor-pointer"
            >
              {[7, 14, 30, 60, 90].map(d => <option key={d} value={d}>{d} дн.</option>)}
            </select>
            <button
              onClick={handleAsk}
              disabled={asking || !question.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
            >
              {asking ? '⏳' : 'Спросить'}
            </button>
          </div>
        </div>
        {askError && <p className="text-red-400 text-sm">{askError}</p>}
        {asking && (
          <div className="flex items-center gap-2 text-indigo-400 text-sm">
            <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            AI анализирует твои данные...
          </div>
        )}
        {answer && (
          <div className="mt-1 p-4 bg-gray-900/60 rounded-lg border border-indigo-500/20 space-y-2">
            <p className="text-xs text-indigo-400 font-medium">💬 {answer.question}
              <span className="text-gray-500 font-normal ml-2">— за {answer.days} дн.</span>
            </p>
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">{answer.answer}</p>
            <button
              onClick={() => { setAnswer(null); setQuestion('') }}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            >
              Очистить
            </button>
          </div>
        )}
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
