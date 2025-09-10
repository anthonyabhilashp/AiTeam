# 🌐 AI Software Generator - Frontend Service

Enterprise Next.js application for the AI Software Generator platform.

## 🚀 Features

- **🔐 Enterprise Authentication** - Keycloak integration with JWT tokens
- **🤖 AI Project Generation** - Interactive interface for software generation
- **📊 Real-time Workflow** - Visual workflow tracking and status updates
- **📁 Project Management** - View and manage generated projects
- **📋 Audit Dashboard** - Compliance and audit logging interface
- **🎨 Professional UI** - Enterprise-grade design with Tailwind CSS

## 🛠️ Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **ReactFlow** - Interactive workflow visualization

## 🏃‍♂️ Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- API Gateway running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Or use the startup script
./start.sh
```

The frontend will be available at: **http://localhost:3000**

### Environment Variables

```bash
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
```

## 📱 Application Structure

```
app/
├── layout.tsx              # Root layout
├── page.tsx                # Main application entry
├── globals.css             # Global styles
└── components/
    ├── AuthProvider.tsx    # Authentication context
    ├── LoginForm.tsx       # Login interface
    ├── Dashboard.tsx       # Main dashboard
    ├── ProjectGenerator.tsx # AI generation interface
    ├── ProjectList.tsx     # Project management
    └── WorkflowVisualization.tsx # Workflow tracker
```

## 🔑 Authentication Flow

1. **Login** → Keycloak authentication
2. **JWT Token** → Stored in localStorage
3. **API Calls** → Token included in Authorization header
4. **Auto-logout** → On token expiration

## 🎯 Key Components

### Project Generator
- Input requirements in natural language
- Select priority levels
- Real-time generation status
- Results display with project details

### Workflow Visualization
- Step-by-step process tracking
- Real-time status updates
- Progress indicators
- Enterprise audit trail

### Dashboard
- Multi-tab interface
- User information display
- Role-based access control
- Responsive design

## 🔌 API Integration

The frontend integrates with these backend services:

- **API Gateway** (port 8000) - Main entry point
- **Auth Service** - User authentication
- **Orchestrator** - Project management
- **Audit Service** - Compliance logging

## 🎨 UI/UX Features

- **Enterprise Theme** - Professional gradient design
- **Responsive Layout** - Mobile-friendly interface
- **Loading States** - Smooth user experience
- **Error Handling** - Graceful error display
- **Accessibility** - WCAG compliant design

## 🚀 Production Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📋 Todo / Roadmap

- [ ] Real-time WebSocket updates
- [ ] Advanced project filtering
- [ ] Code repository integration
- [ ] Export functionality
- [ ] Advanced audit visualizations
- [ ] Mobile app support

## 🏢 Enterprise Features

- **Multi-tenant Support** - Tenant isolation
- **RBAC Integration** - Role-based permissions
- **Audit Compliance** - SOC 2, GDPR ready
- **Security Headers** - Enterprise security standards
- **API Rate Limiting** - Abuse prevention
- **Error Boundaries** - Graceful error handling

---

**Part of the AI Software Generator Enterprise Platform**
