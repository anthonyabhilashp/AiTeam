'use client'

import React, { useState } from 'react'
import axios from 'axios'

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000'

interface Task {
  id: number
  description: string
  status: string
  order_index: number
}

interface ProjectGenerationResult {
  project_id: string
  requirement_id: number
  status: string
  analysis?: {
    complexity: string
    task_count: number
    stack: string
  }
  generation_result?: {
    repo_url: string
    commit_id: string
    generated_files: string[]
    project_path: string
    setup_instructions: string
  }
  message?: string
}

interface RequirementDetails {
  requirement_id: number
  text: string
  status: string
  tasks: Task[]
  created_at: string
}

export default function ProjectGenerator() {
  const [requirement, setRequirement] = useState('')
  const [priority, setPriority] = useState('medium')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<ProjectGenerationResult | null>(null)
  const [requirementDetails, setRequirementDetails] = useState<RequirementDetails | null>(null)
  const [error, setError] = useState('')

  const exampleRequirements = [
    'Build a simple blog website with user registration, login, and the ability to create, edit, and delete blog posts.',
    'Create a REST API for a task management system with user authentication, project creation, task assignment, and deadline tracking.',
    'Build a real-time chat application with rooms, private messaging, and file sharing capabilities.',
    'Create an e-commerce API with product catalog, shopping cart, payment integration, and order management.',
    'Build a customer relationship management (CRM) system with contact management, sales pipeline, and reporting features.'
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)
    setError('')
    setResult(null)
    setRequirementDetails(null)

    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.post(
        `${API_GATEWAY_URL}/api/v1/projects/generate`,
        {
          requirement,
          priority,
          user_id: 'current-user'
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      setResult(response.data)
      
      // Fetch the requirement details to show tasks
      if (response.data.requirement_id) {
        const reqResponse = await axios.get(
          `${API_GATEWAY_URL}/requirements/${response.data.requirement_id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        setRequirementDetails(reqResponse.data)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate project')
    } finally {
      setIsGenerating(false)
    }
  }

  const setExampleRequirement = (example: string) => {
    setRequirement(example)
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🚀 AI Software Generator
        </h2>
        <p className="text-gray-600 mb-6">
          Describe your software requirements in plain English and let our AI generate production-ready code.
        </p>

        {/* Example Requirements */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            💡 Example Requirements
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {exampleRequirements.slice(0, 4).map((example, index) => (
              <button
                key={index}
                onClick={() => setExampleRequirement(example)}
                className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
              >
                <p className="text-sm text-gray-700 line-clamp-3">{example}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Generation Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="requirement" className="block text-sm font-medium text-gray-700 mb-2">
              📋 Software Requirement *
            </label>
            <textarea
              id="requirement"
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Describe the software you want to build in detail. Be specific about features, technology preferences, and any special requirements..."
              required
            />
          </div>

          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
              🎯 Priority Level
            </label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="low">Low - Simple application</option>
              <option value="medium">Medium - Standard business application</option>
              <option value="high">High - Complex enterprise system</option>
              <option value="critical">Critical - Mission-critical system</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isGenerating || !requirement.trim()}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isGenerating ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Software...
              </span>
            ) : (
              '🤖 Generate Software'
            )}
          </button>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">❌</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Generation Failed</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <span className="text-green-400 text-xl mr-3">✅</span>
            <h3 className="text-lg font-semibold text-green-900">
              Software Generation Successful!
            </h3>
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <h4 className="font-medium text-gray-900 mb-2">📊 Project Details</h4>
              <div className="space-y-2 text-sm">
                <p><span className="font-medium">Project ID:</span> {result.project_id}</p>
                <p><span className="font-medium">Status:</span> {result.status}</p>
                {result.analysis && (
                  <>
                    <p><span className="font-medium">Complexity:</span> {result.analysis.complexity}</p>
                    <p><span className="font-medium">Tasks Generated:</span> {result.analysis.task_count}</p>
                    <p><span className="font-medium">Technology Stack:</span> {result.analysis.stack}</p>
                  </>
                )}
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border border-green-200">
              <h4 className="font-medium text-gray-900 mb-2">⚡ Next Steps</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• AI Project Manager is analyzing your requirements</li>
                <li>• Code generation will begin automatically</li>
                <li>• Secure execution environment will test the code</li>
                <li>• Final deliverables will be prepared</li>
              </ul>
            </div>

            {/* Generated Files */}
            {result.generation_result?.generated_files && (
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <h4 className="font-medium text-gray-900 mb-2">📁 Generated Files</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {result.generation_result.generated_files.map((file, index) => (
                    <div key={index} className="flex items-center p-2 bg-gray-50 rounded text-sm">
                      <span className="mr-2">📄</span>
                      <span className="truncate">{file}</span>
                    </div>
                  ))}
                </div>
                {result.generation_result.project_path && (
                  <p className="mt-3 text-sm text-gray-600">
                    <span className="font-medium">Project Path:</span> {result.generation_result.project_path}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Task Breakdown */}
      {requirementDetails && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <span className="text-blue-400 text-xl mr-3">📋</span>
            <h3 className="text-lg font-semibold text-blue-900">
              AI-Generated Task Breakdown
            </h3>
          </div>

          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <h4 className="font-medium text-gray-900 mb-3">
              🎯 Requirement: {requirementDetails.text}
            </h4>
            <div className="space-y-3">
              {requirementDetails.tasks.map((task, index) => (
                <div key={task.id} className="flex items-start p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    {index + 1}
                  </div>
                  <div className="flex-grow">
                    <p className="text-gray-900 font-medium">{task.description}</p>
                    <div className="flex items-center mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        task.status === 'completed' ? 'bg-green-100 text-green-800' :
                        task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {task.status === 'completed' ? '✅ Completed' :
                         task.status === 'in_progress' ? '⏳ In Progress' :
                         '⏸️ Pending'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
