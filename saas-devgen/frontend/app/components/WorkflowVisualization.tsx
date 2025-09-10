'use client'

export default function WorkflowVisualization() {
  const workflowSteps = [
    { 
      id: 1, 
      title: "📝 Requirement Analysis", 
      description: "AI PM analyzes and breaks down requirements",
      status: "completed",
      duration: "30s"
    },
    { 
      id: 2, 
      title: "🤖 Code Generation", 
      description: "AI Engineer generates production-ready code",
      status: "processing",
      duration: "2-5 min"
    },
    { 
      id: 3, 
      title: "🧪 Testing & Validation", 
      description: "Secure sandbox execution and testing",
      status: "pending",
      duration: "1-2 min"
    },
    { 
      id: 4, 
      title: "📦 Package & Deploy", 
      description: "Code packaging and deployment preparation",
      status: "pending",
      duration: "1 min"
    },
    { 
      id: 5, 
      title: "📊 Audit & Compliance", 
      description: "Generate compliance reports and audit logs",
      status: "pending",
      duration: "15s"
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200'
      case 'processing': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'pending': return 'bg-gray-100 text-gray-600 border-gray-200'
      default: return 'bg-gray-100 text-gray-600 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅'
      case 'processing': return '⚡'
      case 'pending': return '⏳'
      default: return '⏳'
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">⚡ AI Workflow Visualization</h2>
        <p className="text-gray-600 mb-6">
          Real-time visualization of the AI-powered software generation process
        </p>

        <div className="space-y-4">
          {workflowSteps.map((step, index) => (
            <div key={step.id} className="relative">
              {/* Connector Line */}
              {index < workflowSteps.length - 1 && (
                <div className="absolute left-6 top-16 w-0.5 h-8 bg-gray-300"></div>
              )}
              
              {/* Step Card */}
              <div className={`border-2 rounded-lg p-4 ${getStatusColor(step.status)}`}>
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-xl border-2 border-current">
                      {getStatusIcon(step.status)}
                    </div>
                  </div>
                  <div className="flex-grow">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-lg">{step.title}</h3>
                      <span className="text-sm font-medium px-2 py-1 bg-white rounded-full">
                        ~{step.duration}
                      </span>
                    </div>
                    <p className="text-sm mt-1 opacity-80">{step.description}</p>
                    
                    {step.status === 'processing' && (
                      <div className="mt-3">
                        <div className="w-full bg-white rounded-full h-2">
                          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                        </div>
                        <p className="text-xs mt-1">Processing...</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">🔄 Workflow Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
              <span className="text-sm">Real-time status updates</span>
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
              <span className="text-sm">Parallel AI agent execution</span>
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
              <span className="text-sm">Automated rollback on failures</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center">
              <span className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></span>
              <span className="text-sm">Enterprise audit logging</span>
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-red-400 rounded-full mr-3"></span>
              <span className="text-sm">Security scanning at each step</span>
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-indigo-400 rounded-full mr-3"></span>
              <span className="text-sm">Multi-tenant isolation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
