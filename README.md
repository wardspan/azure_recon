# 🔒 Azure Recon - Security Assessment Tool

Azure Recon is a comprehensive security posture assessment tool for Microsoft Azure environments. It provides automated security analysis, vulnerability identification, and detailed reporting for Azure tenants using read-only permissions.

## ✨ Features

- **🛡️ Microsoft Defender Integration**: Secure Score analysis and security recommendations
- **🌐 Exposure Analysis**: Identify publicly accessible resources and network security groups
- **👥 Identity & Access Review**: User management, MFA status, and role assignments
- **📋 Policy Compliance**: Azure Policy assignments and compliance monitoring
- **📊 Interactive Dashboard**: Real-time security metrics and visualizations
- **📄 Comprehensive Reports**: Generate PDF and Markdown security reports
- **🐳 Docker Ready**: Single-command deployment with Docker Compose
- **🔐 Secure Authentication**: Azure Device Code Flow for secure tenant access

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  PostgreSQL DB  │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                     ┌─────────────────┐
                     │   Azure APIs    │
                     │   (Read-Only)   │
                     └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Azure tenant with Reader-level access
- Internet connection for Azure API access

### 1. Clone and Configure

```bash
git clone <repository-url>
cd azure-recon

# Copy and configure environment variables
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# Azure Configuration (optional - uses device code flow)
AZURE_TENANT_ID=your-tenant-id-here

# Database Configuration
POSTGRES_PASSWORD=your-secure-database-password

# Application Security
SECRET_KEY=your-super-secret-key-change-me

# Optional: Customize ports
FRONTEND_PORT=3000
```

### 3. Launch Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 4. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:3000/api/docs
- **Health Check**: http://localhost:3000/health

## 🔐 Authentication Flow

1. Navigate to the web interface
2. Click "Sign in with Azure"
3. Follow the device code authentication prompt:
   - Visit the provided URL (e.g., https://microsoft.com/devicelogin)
   - Enter the device code
   - Sign in with your Azure account
   - Grant read permissions
4. Return to the application - you'll be automatically logged in

## 📊 Using the Dashboard

### Running Security Scans

1. Click **"Run Scan"** button on the dashboard
2. Wait for the scan to complete (typically 2-5 minutes)
3. Review results in the dashboard cards and tables
4. Generate reports as needed

### Dashboard Sections

- **📈 Score Cards**: Key security metrics at a glance
- **🎯 Recommendations**: Prioritized security improvements
- **🌐 Public Resources**: Internet-facing assets analysis
- **👥 Identity Review**: User and access management insights
- **📋 Policy Compliance**: Governance and compliance status

### Report Generation

- **Markdown Reports**: Human-readable format for documentation
- **PDF Reports**: Professional format for stakeholders
- **Raw Data Export**: JSON format for integration

## 🔧 API Endpoints

### Authentication

- `POST /api/login` - Initiate device code flow
- `POST /api/auth/complete` - Complete authentication
- `GET /api/auth/status` - Check authentication status

### Scanning

- `POST /api/scan` - Run comprehensive security scan
- `GET /api/scan/latest` - Get most recent scan results
- `GET /api/subscriptions` - List accessible subscriptions

### Data Modules

- `GET /api/secure_score` - Microsoft Defender secure score
- `GET /api/recommendations` - Security recommendations
- `GET /api/exposure` - Public resources and NSGs
- `GET /api/identity` - Users and identity information
- `GET /api/roles` - Role assignments
- `GET /api/policy` - Policy assignments
- `GET /api/compliance` - Compliance results

### Reporting

- `POST /api/report` - Generate security report
- `GET /api/reports` - List generated reports

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
azure-recon/
├── backend/                 # FastAPI application
│   ├── main.py             # Main application entry
│   ├── auth.py             # Azure authentication
│   ├── secure_score.py     # Defender integration
│   ├── exposure.py         # Network analysis
│   ├── identity.py         # Identity management
│   ├── policy.py           # Policy compliance
│   ├── reporting.py        # Report generation
│   └── models.py           # Data models
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API integration
│   │   └── contexts/       # React contexts
│   └── public/
├── templates/              # Report templates
├── reports/                # Generated reports
├── docker-compose.yml      # Container orchestration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
└── .env                    # Environment configuration
```

## 🔒 Security Considerations

### Permissions Required

- **Azure Reader** role at tenant/subscription level
- **Security Reader** role for Microsoft Defender data
- **Directory Reader** role for identity information

### Data Handling

- No Azure configurations are modified (read-only access)
- Scan data stored locally in PostgreSQL database
- Reports contain sensitive information - handle accordingly
- Authentication tokens are managed securely

### Network Security

- All API calls use HTTPS to Azure endpoints
- Web interface served over HTTP (use reverse proxy for HTTPS in production)
- Database access restricted to application containers

## 🐳 Production Deployment

### Docker Compose Production

```bash
# Production environment
ENVIRONMENT=production docker-compose up -d

# With custom configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

```bash
# Security
SECRET_KEY=your-production-secret-key
POSTGRES_PASSWORD=secure-production-password
REDIS_PASSWORD=secure-redis-password

# Networking
FRONTEND_PORT=80
ALLOWED_HOSTS=your-domain.com,your-ip-address

# Optional: Azure service principal (alternative to device code)
AZURE_CLIENT_ID=your-app-registration-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
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
}
```

## 🔍 Troubleshooting

### Common Issues

**Authentication Fails**

```bash
# Check Azure permissions
az role assignment list --assignee your-user-id

# Verify network connectivity
docker-compose logs backend
```

**Scan Errors**

```bash
# Check subscription access
az account list --all

# Review backend logs
docker-compose logs -f backend
```

**Frontend Not Loading**

```bash
# Check container status
docker-compose ps

# Verify port availability
netstat -an | grep 3000
```

### Health Checks

```bash
# Application health
curl http://localhost:3000/health

# API health
curl http://localhost:3000/api/health

# Database connectivity
docker-compose exec database psql -U azure_recon -c "SELECT 1;"
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

- [ ] Multi-tenant support
- [ ] Scheduled scan automation
- [ ] Custom policy definitions
- [ ] Integration with SIEM systems
- [ ] Advanced threat detection
- [ ] Compliance framework mapping (SOC2, ISO27001, etc.)

---

**⚠️ Important**: This tool provides security assessments based on available data and configurations. Always validate findings and follow your organization's security policies when implementing changes.

Built with ❤️ for Azure security professionals.
