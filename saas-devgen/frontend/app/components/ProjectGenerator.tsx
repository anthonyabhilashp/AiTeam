'use client'

import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9090'

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
  progress?: {
    stage: string
    percentage: number
    message: string
  }
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
    code_files?: { [filename: string]: string }
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

interface ProgressUpdate {
  stage: string
  percentage: number
  message: string
}

interface CodeFile {
  name: string
  content: string
}

export default function ProjectGenerator() {
  const [requirement, setRequirement] = useState('')
  const [priority, setPriority] = useState('medium')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<ProjectGenerationResult | null>(null)
  const [requirementDetails, setRequirementDetails] = useState<RequirementDetails | null>(null)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState<ProgressUpdate | null>(null)
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(null)
  const [showCodeViewer, setShowCodeViewer] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [codeFiles, setCodeFiles] = useState<CodeFile[]>([])
  const pollInterval = useRef<NodeJS.Timeout | null>(null)

  const exampleRequirements = [
    'Build a simple blog website with user registration, login, and the ability to create, edit, and delete blog posts.',
    'Create a REST API for a task management system with user authentication, project creation, task assignment, and deadline tracking.',
    'Build a real-time chat application with rooms, private messaging, and file sharing capabilities.',
    'Create an e-commerce API with product catalog, shopping cart, payment integration, and order management.',
    'Build a customer relationship management (CRM) system with contact management, sales pipeline, and reporting features.'
  ]

  const pollProgress = async (projectId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${API_GATEWAY_URL}/api/v1/projects/${projectId}/progress`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      
      const progressData = response.data
      setProgress(progressData)
      
      if (progressData.percentage >= 100 || progressData.stage === 'completed') {
        // Fetch final result
        const resultResponse = await axios.get(
          `${API_GATEWAY_URL}/api/v1/projects/${projectId}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        setResult(resultResponse.data)
        setIsGenerating(false)
        if (pollInterval.current) {
          clearInterval(pollInterval.current)
        }
      }
    } catch (err) {
      console.error('Progress polling error:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)
    setError('')
    setResult(null)
    setRequirementDetails(null)
    setProgress({ stage: 'initializing', percentage: 0, message: 'Starting project generation...' })

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

      const initialResult = response.data
      setResult(initialResult)
      
      // Start progress polling
      if (initialResult.project_id) {
        pollInterval.current = setInterval(() => {
          pollProgress(initialResult.project_id)
        }, 2000) // Poll every 2 seconds
      }
      
      // Fetch the requirement details to show tasks
      if (initialResult.requirement_id) {
        const reqResponse = await axios.get(
          `${API_GATEWAY_URL}/api/v1/requirements/${initialResult.requirement_id}`,
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
      setError(err.response?.data?.detail || 'Service communication failed')
      setIsGenerating(false)
    }
  }

  const downloadProject = async () => {
    if (!result?.generation_result?.code_files) return
    
    // Create a zip file with all generated code
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()
    
    Object.entries(result.generation_result.code_files).forEach(([filename, content]) => {
      zip.file(filename, content)
    })
    
    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `generated-project-${result.project_id}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const viewCode = async () => {
    if (!result?.generation_result?.code_files) {
      setError('No generated code files available to view')
      return
    }

    // Convert code files to CodeFile array
    const files: CodeFile[] = Object.entries(result.generation_result.code_files).map(([name, content]) => ({
      name,
      content: content as string
    }))
    
    setCodeFiles(files)
    setShowCodeViewer(true)
    if (files.length > 0) {
      setSelectedFile(files[0])
    }
  }

  const downloadCode = async () => {
    if (!result?.generation_result?.code_files) {
      setError('No generated code files available to download')
      return
    }

    // Create a zip file with all generated code
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()
    
    Object.entries(result.generation_result.code_files).forEach(([filename, content]) => {
      zip.file(filename, content)
    })
    
    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectName || 'generated-project'}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const setExampleRequirement = (example: string) => {
    setRequirement(example)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollInterval.current) {
        clearInterval(pollInterval.current)
      }
    }
  }, [])

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
            <label htmlFor="projectName" className="block text-sm font-medium text-gray-700 mb-2">
              📝 Project Name *
            </label>
            <input
              type="text"
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter your project name (e.g., Customer Management System)"
              required
            />
          </div>

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

      {/* Progress Display */}
      {isGenerating && progress && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <div className="flex-shrink-0">
              <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-lg font-semibold text-blue-900">
                🤖 Generating Your Software
              </h3>
              <p className="text-blue-700">{progress.message}</p>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-blue-700">
                {progress.stage}
              </span>
              <span className="text-sm text-blue-600">
                {progress.percentage}%
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>
          </div>
          
          {/* Progress Stages */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className={`p-3 rounded-lg text-center ${
              progress.stage === 'Product Manager' || progress.percentage > 30 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              <div className="font-medium">📋 Product Manager</div>
              <div className="text-xs">Analyzing requirements</div>
            </div>
            <div className={`p-3 rounded-lg text-center ${
              progress.stage === 'Architect' || progress.percentage > 60
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              <div className="font-medium">🏗️ Architect</div>
              <div className="text-xs">Designing system</div>
            </div>
            <div className={`p-3 rounded-lg text-center ${
              progress.stage === 'Engineer' || progress.percentage > 90
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              <div className="font-medium">💻 Engineer</div>
              <div className="text-xs">Writing code</div>
            </div>
          </div>
        </div>
      )}

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
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-lg font-semibold text-green-900">
                🎉 Software Generated Successfully!
              </h3>
              <p className="text-green-700 mt-1">Your enterprise software has been generated and is ready for deployment.</p>
              
              <div className="mt-4 space-y-4">
                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={viewCode}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    👁️ View Code
                  </button>
                  <button
                    onClick={downloadCode}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    � Download ZIP
                  </button>
                  <button
                    onClick={() => {
                      setResult(null);
                      setProjectName('');
                      setRequirement('');
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    🆕 New Project
                  </button>
                </div>

                {/* Result Summary */}
                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-semibold text-gray-900 mb-2">Generation Summary:</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div><strong>Project ID:</strong> {result.project_id}</div>
                    <div><strong>Status:</strong> <span className="text-green-600 font-medium">{result.status}</span></div>
                    <div><strong>Files Generated:</strong> {codeFiles.length} files</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Code Viewer Modal */}
      {showCodeViewer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                📁 Generated Code - {projectName}
              </h3>
              <button
                onClick={() => setShowCodeViewer(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 flex overflow-hidden">
              {/* File Tree */}
              <div className="w-1/3 border-r p-4 overflow-y-auto">
                <h4 className="font-medium text-gray-900 mb-3">📂 Project Files</h4>
                <div className="space-y-1">
                  {codeFiles.map((file, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedFile(file)}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${
                        selectedFile?.name === file.name
                          ? 'bg-blue-100 text-blue-800'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className="mr-2">
                          {file.name.endsWith('.py') ? '🐍' : 
                           file.name.endsWith('.md') ? '📖' : 
                           file.name.endsWith('.txt') ? '📄' : 
                           file.name.endsWith('.json') ? '⚙️' : '📄'}
                        </span>
                        <span className="truncate">{file.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Code Content */}
              <div className="flex-1 p-4 overflow-y-auto">
                {selectedFile ? (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">
                        {selectedFile.name}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {selectedFile.content.length} characters
                      </span>
                    </div>
                    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <code>{selectedFile.content}</code>
                    </pre>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p>Select a file to view its content</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="border-t p-4 flex justify-end">
              <button
                onClick={downloadCode}
                className="mr-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
              >
                📥 Download All
              </button>
              <button
                onClick={() => setShowCodeViewer(false)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Close
              </button>
            </div>
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
