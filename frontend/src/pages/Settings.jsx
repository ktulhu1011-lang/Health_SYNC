import React, { useEffect, useState, useContext } from 'react'
import { insights, metrics, exportData } from '../api'
import { AuthContext } from '../App'

const SUPPLEMENT_GROUPS = {
  antistress: {
    label: '🧘 Антистресс',
    items: [
      { key: 'ashwagandha', label: 'Ashwagandha (KSM-66)' },
      { key: 'magnesium', label: 'Magnesium Glycinate' },
      { key: 'theanine', label: 'L-Theanine' },
      { key: 'rhodiola', label: 'Rhodiola Rosea' },
      { key: 'gaba', label: 'GABA' },
      { key: 'b_complex', label: 'Vitamin B-Complex' },
    ]
  },
  antioxidants: {
    label: '🛡 Антиоксиданты',
    items: [
      { key: 'vitamin_c', label: 'Vitamin C' },
      { key: 'vitamin_e', label: 'Vitamin E' },
      { key: 'ala', label: 'Alpha Lipoic Acid' },
      { key: 'coq10', label: 'CoQ10' },
      { key: 'resveratrol', label: 'Resveratrol' },
      { key: 'nac', label: 'NAC' },
    ]
  },
  basic: {
    label: '⚡ Базовые',
    items: [
      { key: 'vitamin_d3k2', label: 'Vitamin D3 + K2' },
      { key: 'omega3', label: 'Omega-3' },
      { key: 'zinc', label: 'Zinc' },
    ]
  },
}

export default function Settings() {
  const { user } = useContext(AuthContext)
  const [settings, setSettings] = useState({})
  const [activeSupplements, setActiveSupplements] = useState(new Set())
  const [garminEmail, setGarminEmail] = useState('')
  const [garminPassword, setGarminPassword] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportDays, setExportDays] = useState(365)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    insights.getSettings().then(r => {
      setSettings(r.data)
      const active = r.data.active_supplements
      if (active && active.length > 0) {
        setActiveSupplements(new Set(active))
      } else {
        // Default: all active
        const all = new Set()
        Object.values(SUPPLEMENT_GROUPS).forEach(g => g.items.forEach(i => all.add(i.key)))
        setActiveSupplements(all)
      }
    })
  }, [])

  function toggleSupplement(key) {
    setActiveSupplements(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function saveSettings() {
    setSaving(true)
    setMessage('')
    setError('')
    try {
      await insights.updateSettings({
        active_supplements: [...activeSupplements],
        morning_reminder_enabled: settings.morning_reminder_enabled,
        morning_reminder_time: settings.morning_reminder_time,
      })
      setMessage('✅ Настройки сохранены')
    } catch {
      setError('Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  async function syncNow() {
    setSyncing(true)
    setMessage('')
    setError('')
    try {
      const r = await metrics.syncNow()
      setMessage(`✅ Синхронизировано! Получено ${r.data.metrics_fetched} метрик`)
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка синхронизации')
    } finally {
      setSyncing(false)
    }
  }

  async function saveGarmin() {
    if (!garminEmail || !garminPassword) return
    setSaving(true)
    try {
      await metrics.saveGarminCredentials(garminEmail, garminPassword)
      setGarminEmail('')
      setGarminPassword('')
      setMessage('✅ Данные Garmin сохранены')
    } catch {
      setError('Ошибка сохранения данных Garmin')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-white">⚙️ Настройки</h1>

      {message && (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-green-400 text-sm">{message}</div>
      )}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-red-400 text-sm">{error}</div>
      )}

      {/* Garmin Sync */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h2 className="font-semibold text-gray-200 mb-4">🏃 Garmin Connect</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={garminEmail}
              onChange={e => setGarminEmail(e.target.value)}
              placeholder="email@garmin.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Пароль</label>
            <input
              type="password"
              value={garminPassword}
              onChange={e => setGarminPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={saveGarmin}
              disabled={saving || !garminEmail || !garminPassword}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Сохранить
            </button>
            <button
              onClick={syncNow}
              disabled={syncing}
              className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {syncing ? '⏳ Синхронизирую...' : '🔄 Синхронизировать сейчас'}
            </button>
          </div>
        </div>
      </div>

      {/* Morning reminder */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h2 className="font-semibold text-gray-200 mb-4">🌅 Утреннее напоминание</h2>
        <label className="flex items-center gap-3 cursor-pointer">
          <div
            onClick={() => setSettings(s => ({ ...s, morning_reminder_enabled: !s.morning_reminder_enabled }))}
            className={`w-10 h-6 rounded-full transition-colors ${
              settings.morning_reminder_enabled ? 'bg-blue-600' : 'bg-gray-700'
            } relative`}
          >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${
              settings.morning_reminder_enabled ? 'left-5' : 'left-1'
            }`} />
          </div>
          <span className="text-sm text-gray-300">Отправлять сводку сна из Garmin по утрам</span>
        </label>
        {settings.morning_reminder_enabled && (
          <div className="mt-3">
            <label className="block text-sm text-gray-400 mb-1">Время</label>
            <input
              type="time"
              value={settings.morning_reminder_time || '08:00'}
              onChange={e => setSettings(s => ({ ...s, morning_reminder_time: e.target.value }))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
        )}
      </div>

      {/* Supplements */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h2 className="font-semibold text-gray-200 mb-1">💊 Активные добавки</h2>
        <p className="text-gray-500 text-xs mb-4">Только выбранные будут показаны в /log → Добавки</p>
        <div className="space-y-5">
          {Object.entries(SUPPLEMENT_GROUPS).map(([groupKey, group]) => (
            <div key={groupKey}>
              <div className="text-sm font-semibold text-gray-300 mb-2">{group.label}</div>
              <div className="grid grid-cols-2 gap-2">
                {group.items.map(item => (
                  <label key={item.key} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={activeSupplements.has(item.key)}
                      onChange={() => toggleSupplement(item.key)}
                      className="w-4 h-4 rounded accent-blue-500"
                    />
                    <span className="text-sm text-gray-300">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Export */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h2 className="font-semibold text-gray-200 mb-1">📥 Экспорт данных</h2>
        <p className="text-gray-500 text-xs mb-4">Скачать все данные (Garmin + привычки) одной таблицей CSV</p>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex gap-1">
            {[90, 180, 365, 730].map(d => (
              <button
                key={d}
                onClick={() => setExportDays(d)}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  exportDays === d
                    ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                    : 'border-gray-700 text-gray-400 hover:border-gray-600'
                }`}
              >
                {d >= 365 ? `${d / 365} год${d > 365 ? 'а' : ''}` : `${d} дн`}
              </button>
            ))}
          </div>
          <button
            onClick={async () => {
              setExporting(true)
              try {
                await exportData.downloadCsv(exportDays)
              } catch {
                setError('Ошибка экспорта')
              } finally {
                setExporting(false)
              }
            }}
            disabled={exporting}
            className="bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {exporting ? '⏳ Скачиваю...' : '⬇️ Скачать CSV'}
          </button>
        </div>
      </div>

      <button
        onClick={saveSettings}
        disabled={saving}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2.5 rounded-lg font-medium transition-colors"
      >
        {saving ? 'Сохранение...' : '💾 Сохранить настройки'}
      </button>
    </div>
  )
}
