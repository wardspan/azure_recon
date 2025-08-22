# 🔒 Azure Recon - Identity & Role Analysis Tool

Azure Recon is a security analysis tool focused on Azure identity and role assignment reconnaissance. It provides detailed analysis of identity permissions, role assignments, and access patterns across Azure environments using read-only permissions.

## ✨ Features

- **👥 Identity Analysis**: Comprehensive role assignment analysis by identity type (Users, Service Principals, Managed Identities, Groups)
- **📊 Interactive Dashboard**: Real-time identity metrics with visual breakdowns and statistics
- **🔐 Secure Authentication**: Azure Device Code Flow for secure tenant access
- **⏰ Authentication Monitoring**: Token expiration tracking and status alerts
- **🎯 Conditional Rendering**: Smart UI that adapts based on authentication state
- **🛡️ Read-Only Access**: No modifications to Azure configurations
- **🐳 Docker Ready**: Single-command deployment with Docker Compose
- **⚡ Real-time Updates**: Live data loading and error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   Azure APIs    │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Read-Only)   │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • Auth Status   │    │ • Graph API     │
│ • Identity Tab  │    │ • Identity Scan │    │ • ARM API       │
│ • Conditional   │    │ • Role Analysis │    │ • Identity API  │
│   Rendering     │    │ • Device Code   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Azure tenant with appropriate permissions for identity analysis
- Internet connection for Azure API access

### 1. Clone and Start

```bash
git clone https://github.com/wardspan/azure_recon.git
cd azure_recon

# Start all services
docker-compose up -d
```

### 2. Environment Configuration (Optional)

The application works out of the box with device code authentication. For custom configuration, create a `.env` file:

```bash
# Optional: Custom ports
FRONTEND_PORT=3000
BACKEND_PORT=8000

# Optional: Azure tenant ID (will be obtained during auth flow)
AZURE_TENANT_ID=your-tenant-id-here
```

### 3. Access and Monitor

```bash
# View logs
docker-compose logs -f

# Check service health
docker-compose ps

# Rebuild after code changes
docker-compose down && docker-compose up -d --build
```

### 4. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: Internal Docker network (port 8000)

## 🔐 Authentication Flow

1. Navigate to http://localhost:3000
2. Click on the "Identity" tab
3. If not authenticated, you'll see a login prompt with "Start Login" button
4. Click "Start Login" to initiate Azure Device Code flow:
   - Visit the provided URL (e.g., https://microsoft.com/devicelogin)
   - Enter the device code shown in the application
   - Sign in with your Azure account
   - Grant the requested permissions
5. Return to the application - data will load automatically after successful authentication

## 📊 Using the Identity Dashboard

### Identity Analysis Features

The Identity tab provides comprehensive role assignment analysis with the following features:

- **🔐 Authentication Status**: Real-time authentication monitoring with token expiration warnings
- **👥 Identity Categorization**: Automatic grouping by type (Users, Service Principals, Managed Identities, Groups, Unknown/Deleted)
- **📊 Visual Statistics**: Progress bars showing role assignment distribution
- **🎯 Top Role Assignments**: Most common roles per identity type
- **⚡ Real-time Loading**: Live data updates with error handling and retry mechanisms

### Application States

- **Not Authenticated**: Warning banner with "Start Login" button for device code flow
- **Loading**: Spinner with progress messages during data retrieval
- **Error**: Error display with retry functionality for failed requests
- **No Data**: Informative message when no role assignments are found
- **Data Available**: Rich visualization of role assignments with interactive cards

### Identity Types Analyzed

- **👤 Users**: Azure AD user accounts and their role assignments
- **🤖 Service Principals**: Application registrations and service accounts
- **🔧 Managed Identities**: System and user-assigned managed identities
- **👥 Groups**: Security and distribution groups with role assignments
- **❓ Unknown/Deleted**: Orphaned role assignments from deleted principals

## 🔧 API Endpoints

### Authentication

- `GET /api/auth/status` - Check authentication status with token expiration info
- `POST /api/auth/device-code` - Initiate Azure device code authentication flow

### Identity Analysis

- `GET /api/scan/identity` - Get detailed role assignment analysis (requires authentication)
  - Returns structured data grouped by identity type
  - Includes principal IDs, role names, scopes, and assignment details

### Response Models

**AuthStatus**

```json
{
  "authenticated": true,
  "tenant_id": "your-tenant-id",
  "expires_in_minutes": 45
}
```

**IdentityScanResult**

```json
{
  "users": [{"principal_id": "...", "roles": [...], "type": "User"}],
  "service_principals": [...],
  "managed_identities": [...],
  "groups": [...],
  "unknown_or_deleted": [...]
}
```

## 🛠️ Development

### Local Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend development
cd frontend
npm install
npm run dev
```

### Project Structure

```
azure_recon/
├── backend/                 # FastAPI application
│   ├── main.py             # Main application with auth and identity endpoints
│   ├── models.py           # Pydantic models for API responses
│   ├── role_analysis.py    # Azure role assignment analysis logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript application
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── EnhancedIdentityBreakdown.tsx  # Main identity component
│   │   │   └── IdentityBreakdown.tsx         # Legacy component
│   │   ├── pages/
│   │   │   └── Dashboard.tsx    # Main dashboard with tabs
│   │   └── services/
│   │       └── api.ts           # API client and TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml      # Container orchestration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
└── .gitignore
```

## 🔒 Security Considerations

### Permissions Required

- **Reader** role at subscription level for role assignment analysis
- **Directory Reader** role for Azure AD identity information
- **User.Read** Microsoft Graph permission for user details

### Data Handling

- Read-only access to Azure resources (no modifications)
- Authentication tokens stored temporarily during session
- All data processed locally within Docker containers
- No persistent storage of Azure data

### Network Security

- All Azure API calls use HTTPS
- Frontend served over HTTP (add reverse proxy for production HTTPS)
- Backend API accessible only within Docker network
- Device code authentication flow for secure access

## 🐳 Production Deployment

### Docker Compose Production

```bash
# Production deployment
docker-compose up -d --build

# Monitor logs
docker-compose logs -f

# Health check
docker-compose ps
```

### Environment Variables for Production

```bash
# Optional: Custom ports
FRONTEND_PORT=80
BACKEND_PORT=8000

# Optional: Azure configuration
AZURE_TENANT_ID=your-tenant-id

# Optional: Custom Docker settings
COMPOSE_PROJECT_NAME=azure_recon
```

### Reverse Proxy Configuration (nginx)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 Troubleshooting

### Common Issues

**Authentication Fails**

```bash
# Check Azure permissions
az role assignment list --assignee your-user-id

# Verify backend logs for auth errors
docker-compose logs backend
```

**Identity Scan Errors**

```bash
# Check subscription access
az account show

# Review detailed backend logs
docker-compose logs -f backend
```

**Frontend Not Loading**

```bash
# Check container status
docker-compose ps

# Verify port availability
netstat -an | grep 3000

# Check frontend build logs
docker-compose logs frontend
```

**Role Assignment Issues**

```bash
# Verify Azure permissions
az role assignment list --all --query "[?principalId=='<your-user-id>']"

# Check for API throttling or rate limiting
docker-compose logs backend | grep -i "error\|exception"
```

### Health Checks

```bash
# Check all containers
docker-compose ps

# Frontend accessibility
curl http://localhost:3000

# Backend API docs
curl http://localhost:8000/docs

# Authentication status
curl http://localhost:8000/api/auth/status
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- Create an issue for bug reports
- Check existing issues for known problems
- Review logs for troubleshooting information

## 🎯 Roadmap

- [ ] Additional identity analysis features (privilege escalation paths, orphaned permissions)
- [ ] Role assignment timeline and change tracking
- [ ] Export functionality for identity data (CSV, JSON, PDF reports)
- [ ] Multi-subscription support for enterprise environments
- [ ] Custom role definition analysis
- [ ] Integration with Microsoft Graph for enhanced identity insights
- [ ] Automated role assignment recommendations
- [ ] Compliance reporting for identity governance frameworks

## 🏗️ Current Implementation Status

- ✅ **Authentication**: Azure Device Code flow with token expiration tracking
- ✅ **Identity Analysis**: Role assignment categorization by identity type
- ✅ **Frontend**: React TypeScript with conditional rendering and error handling
- ✅ **Backend**: FastAPI with Azure SDK integration
- ✅ **Docker**: Containerized deployment with Docker Compose
- ⏳ **Testing**: End-to-end authentication flow testing in progress
- ⏳ **Documentation**: API documentation and user guides

---

**⚠️ Important**: This tool provides identity and role assignment analysis for Azure environments. It requires appropriate Azure permissions and should be used in accordance with your organization's security policies. All access is read-only and no Azure configurations are modified.

Built for Azure identity security analysis and reconnaissance.
