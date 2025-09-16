'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from './AuthProvider'
import ProjectGenerator from './ProjectGenerator'
import ProjectList from './ProjectList'
import WorkflowVisualization from './WorkflowVisualization'
import SettingsPage from './SettingsPage'

interface DashboardProps {
  onLogout: () => void
}

function Dashboard({ onLogout }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('generator')
  const [projects, setProjects] = useState([])
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    onLogout()
  }

  const tabs = [
    { id: 'generator', label: '🚀 Generate Software', icon: '🤖' },
    { id: 'projects', label: '📁 My Projects', icon: '📊' },
    { id: 'workflow', label: '⚡ Workflow', icon: '🔄' },
    { id: 'settings', label: '⚙️ Settings', icon: '🔧' },
    { id: 'audit', label: '📋 Audit Logs', icon: '🔍' }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🤖 AI Software Generator
              </h1>
              <span className="ml-4 px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                Enterprise
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{user?.username}</span>
                <span className="mx-2">•</span>
                <span>Tenant: {user?.tenant_id}</span>
              </div>
              <button
                onClick={handleLogout}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'generator' && <ProjectGenerator />}
        {activeTab === 'projects' && <ProjectList projects={projects} />}
        {activeTab === 'workflow' && <WorkflowVisualization />}
        {activeTab === 'settings' && <SettingsPage />}
        {activeTab === 'audit' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">📋 Audit Logs</h2>
            <div className="text-gray-600">
              <p>Audit logging implementation coming soon...</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Dashboard
