'use client'

export default function ProjectList({ projects = [] }: { projects: any[] }) {
  if (projects.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <div className="text-6xl mb-4">📁</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Projects Yet</h3>
        <p className="text-gray-600 mb-6">
          You haven't generated any software projects yet. Head over to the Generator tab to create your first AI-powered application.
        </p>
        <div className="text-left max-w-md mx-auto">
          <h4 className="font-semibold text-gray-900 mb-3">📊 Coming Soon:</h4>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-center">
              <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
              Project status tracking
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
              Generated code repository access
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></span>
              Execution logs and results
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
              Project collaboration features
            </li>
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">📁 My Projects</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="font-semibold text-gray-900 mb-2">{project.name}</h3>
            <p className="text-gray-600 text-sm mb-4">{project.description}</p>
            <div className="flex items-center justify-between">
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                {project.status}
              </span>
              <span className="text-xs text-gray-500">{project.created_at}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
