'use client'

import React, { useState, useEffect } from 'react'

interface Settings {
  ai_provider: string
  ai_model: string
  api_key: string
}

interface OpenRouterModel {
  id: string
  name: string
  context_length?: number
  pricing?: {
    prompt: string
    completion: string
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    ai_provider: 'openai',
    ai_model: 'gpt-4o',
    api_key: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [loadingModels, setLoadingModels] = useState(false)
  const [message, setMessage] = useState('')
  const [openRouterModels, setOpenRouterModels] = useState<OpenRouterModel[]>([])

  // Static models for other providers
  const staticModels = {
    openai: [
      { value: 'gpt-4o', label: 'GPT-4o' },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
      { value: 'gpt-4', label: 'GPT-4' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
    ],
    anthropic: [
      { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
      { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
      { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' }
    ],
    azure: [
      { value: 'gpt-4', label: 'GPT-4 (Azure)' },
      { value: 'gpt-4-32k', label: 'GPT-4 32K (Azure)' },
      { value: 'gpt-35-turbo', label: 'GPT-3.5 Turbo (Azure)' }
    ]
  }

  useEffect(() => {
    loadSettings()
  }, [])

  useEffect(() => {
    if (settings.ai_provider === 'openrouter') {
      loadOpenRouterModels()
    }
  }, [settings.ai_provider])

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:8007/settings')
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      setMessage('Failed to load settings')
      setTimeout(() => setMessage(''), 3000)
    }
  }

  const loadOpenRouterModels = async () => {
    setLoadingModels(true)
    try {
      const response = await fetch('http://localhost:8007/openrouter/models')
      if (response.ok) {
        const models = await response.json()
        setOpenRouterModels(models)
      } else {
        setMessage('Failed to load OpenRouter models')
        setTimeout(() => setMessage(''), 3000)
      }
    } catch (error) {
      console.error('Failed to load OpenRouter models:', error)
      setMessage('Failed to load OpenRouter models')
      setTimeout(() => setMessage(''), 3000)
    } finally {
      setLoadingModels(false)
    }
  }

  const saveSettings = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const response = await fetch('http://localhost:8007/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      })

      if (response.ok) {
        setMessage('Settings saved successfully!')
      } else {
        setMessage('Failed to save settings. Please try again.')
      }
      setTimeout(() => setMessage(''), 3000)
    } catch (error) {
      console.error('Save settings error:', error)
      setMessage('Failed to save settings. Please try again.')
      setTimeout(() => setMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleProviderChange = (provider: string) => {
    let defaultModel = 'gpt-4o'
    if (provider === 'anthropic') defaultModel = 'claude-3-5-sonnet-20241022'
    if (provider === 'azure') defaultModel = 'gpt-4'
    if (provider === 'openrouter') defaultModel = 'anthropic/claude-3.5-sonnet'
    
    setSettings({
      ...settings,
      ai_provider: provider,
      ai_model: defaultModel
    })
  }

  const renderModelOptions = () => {
    if (settings.ai_provider === 'openrouter') {
      if (loadingModels) {
        return <option value="">Loading models...</option>
      }
      
      return openRouterModels.map((model) => (
        <option key={model.id} value={model.id}>
          {model.name} {model.context_length ? `(${model.context_length}k)` : ''}
        </option>
      ))
    }

    const models = staticModels[settings.ai_provider as keyof typeof staticModels] || []
    return models.map((model) => (
      <option key={model.value} value={model.value}>
        {model.label}
      </option>
    ))
  }

  const getApiKeyPlaceholder = () => {
    switch (settings.ai_provider) {
      case 'openai':
        return 'sk-...'
      case 'anthropic':
        return 'sk-ant-...'
      case 'azure':
        return 'Azure API Key'
      case 'openrouter':
        return 'sk-or-...'
      default:
        return 'Enter your API key'
    }
  }

  const getProviderDescription = () => {
    switch (settings.ai_provider) {
      case 'openai':
        return 'Use OpenAI models like GPT-4o and GPT-4 Turbo'
      case 'anthropic':
        return 'Use Anthropic Claude models for advanced reasoning'
      case 'azure':
        return 'Use Azure OpenAI Service for enterprise deployments'
      case 'openrouter':
        return `Access 160+ AI models through OpenRouter gateway (${openRouterModels.length} models loaded)`
      default:
        return ''
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🚀 AI Provider Settings</h1>
        <p className="text-gray-600">Configure your AI provider and model preferences for enterprise code generation</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-lg p-8">
        <form onSubmit={saveSettings} className="space-y-8">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">AI Provider</label>
            <select
              value={settings.ai_provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-lg"
            >
              <option value="openai">🤖 OpenAI</option>
              <option value="anthropic">🧠 Anthropic</option>
              <option value="azure">☁️ Azure OpenAI</option>
              <option value="openrouter">🌐 OpenRouter (160+ Models)</option>
            </select>
            <p className="text-sm text-gray-600 mt-2 font-medium">{getProviderDescription()}</p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              AI Model
              {settings.ai_provider === 'openrouter' && openRouterModels.length > 0 && (
                <span className="text-green-600 text-xs ml-2 font-bold">
                  ({openRouterModels.length} models available)
                </span>
              )}
            </label>
            <select
              value={settings.ai_model}
              onChange={(e) => setSettings({...settings, ai_model: e.target.value})}
              disabled={loadingModels}
              className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 bg-white text-lg"
            >
              {renderModelOptions()}
            </select>
            {settings.ai_provider === 'openrouter' && (
              <p className="text-sm text-gray-600 mt-2 font-medium">
                {loadingModels ? '⏳ Loading available models...' : `✅ ${openRouterModels.length} models loaded from OpenRouter API`}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">API Key</label>
            <input
              type="password"
              value={settings.api_key}
              onChange={(e) => setSettings({...settings, api_key: e.target.value})}
              placeholder={getApiKeyPlaceholder()}
              className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
              required
            />
            <p className="text-sm text-gray-600 mt-2 font-medium">
              🔒 Your API key is encrypted and stored securely in enterprise environment
            </p>
          </div>

          <div className="flex items-center justify-between pt-6 border-t-2 border-gray-200">
            <div className="text-sm text-gray-600 font-medium">
              📝 Changes will apply to new code generation requests
            </div>
            <button
              type="submit"
              disabled={loading || loadingModels}
              className="bg-blue-600 text-white py-3 px-8 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 text-lg font-semibold shadow-lg"
            >
              {loading && (
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              {loading ? '💾 Saving...' : '💾 Save Settings'}
            </button>
          </div>
        </form>

        {message && (
          <div className={`mt-6 p-4 rounded-lg border-2 ${
            message.includes('success') 
              ? 'bg-green-50 text-green-800 border-green-200' 
              : 'bg-red-50 text-red-800 border-red-200'
          }`}>
            <div className="flex items-center gap-3 text-lg font-semibold">
              {message.includes('success') ? (
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              )}
              {message}
            </div>
          </div>
        )}
      </div>

      {settings.ai_provider === 'openrouter' && openRouterModels.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-2xl font-bold mb-6">🌟 Available OpenRouter Models</h3>
          <div className="max-h-80 overflow-y-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {openRouterModels.slice(0, 30).map((model) => (
                <div
                  key={model.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                    settings.ai_model === model.id
                      ? 'border-blue-500 bg-blue-50 shadow-lg'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSettings({ ...settings, ai_model: model.id })}
                >
                  <div className="font-semibold text-sm text-gray-800">{model.name}</div>
                  {model.context_length && (
                    <div className="text-xs text-gray-600 mt-1">
                      📊 Context: {model.context_length}k tokens
                    </div>
                  )}
                  {model.pricing && (
                    <div className="text-xs text-gray-500 mt-1">
                      💰 ${model.pricing.prompt}/${model.pricing.completion} per 1M tokens
                    </div>
                  )}
                </div>
              ))}
            </div>
            {openRouterModels.length > 30 && (
              <div className="text-center mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="text-lg font-semibold text-gray-700">
                  🚀 ... and {openRouterModels.length - 30} more models available in dropdown
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Total OpenRouter models loaded: {openRouterModels.length}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
