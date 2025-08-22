import React, { useState, useEffect } from 'react'
import { Database, RefreshCw, Eye, EyeOff } from 'lucide-react'
import { DataTable } from '../components/DataTable'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { scanApi, type ScanResult } from '../services/api'

type DataModule =
  | 'overview'
  | 'secure_score'
  | 'recommendations'
  | 'exposure'
  | 'identity'
  | 'policy'
  | 'compliance'

const DataViewer: React.FC = () => {
  const [activeModule, setActiveModule] = useState<DataModule>('overview')
  const [scanData, setScanData] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [showRawJson, setShowRawJson] = useState(false)

  const modules = [
    {
      key: 'overview' as DataModule,
      name: 'Overview',
      description: 'Complete scan results',
    },
    {
      key: 'secure_score' as DataModule,
      name: 'Secure Score',
      description: 'Microsoft Defender scores',
    },
    {
      key: 'recommendations' as DataModule,
      name: 'Recommendations',
      description: 'Security recommendations',
    },
    {
      key: 'exposure' as DataModule,
      name: 'Exposure',
      description: 'Public resources and NSGs',
    },
    {
      key: 'identity' as DataModule,
      name: 'Identity',
      description: 'Users and roles',
    },
    {
      key: 'policy' as DataModule,
      name: 'Policy',
      description: 'Policy assignments',
    },
    {
      key: 'compliance' as DataModule,
      name: 'Compliance',
      description: 'Compliance results',
    },
  ]

  useEffect(() => {
    loadLatestScan()
  }, [])

  const loadLatestScan = async () => {
    setLoading(true)
    try {
      const latest = await scanApi.getLatestScan()
      setScanData(latest)
    } catch (error) {
      console.error('Error loading scan data:', error)
    } finally {
      setLoading(false)
    }
  }

  const renderModuleData = () => {
    if (!scanData) return null

    const recommendationColumns = [
      { key: 'name', header: 'Name', className: 'max-w-xs' },
      {
        key: 'severity',
        header: 'Severity',
        render: (value: string) => (
          <span className={`severity-${value.toLowerCase()}`}>{value}</span>
        ),
      },
      { key: 'category', header: 'Category' },
      { key: 'state', header: 'State' },
      { key: 'affected_resources', header: 'Affected Resources' },
    ]

    const publicResourceColumns = [
      { key: 'resource_name', header: 'Resource Name' },
      { key: 'resource_type', header: 'Type' },
      {
        key: 'public_ip',
        header: 'Public IP',
        render: (value: string) => value || 'N/A',
      },
      {
        key: 'subscription_id',
        header: 'Subscription',
        className: 'max-w-xs truncate',
      },
    ]

    const userColumns = [
      { key: 'display_name', header: 'Display Name' },
      { key: 'user_principal_name', header: 'UPN', className: 'max-w-xs' },
      {
        key: 'is_guest',
        header: 'Guest',
        render: (value: boolean) => (value ? 'Yes' : 'No'),
      },
      {
        key: 'mfa_enabled',
        header: 'MFA',
        render: (value: boolean) => (
          <span className={value ? 'text-green-600' : 'text-red-600'}>
            {value ? 'Enabled' : 'Disabled'}
          </span>
        ),
      },
    ]

    const roleColumns = [
      { key: 'principal_name', header: 'Principal' },
      { key: 'principal_type', header: 'Type' },
      { key: 'role_definition_name', header: 'Role' },
      { key: 'scope', header: 'Scope', className: 'max-w-xs truncate' },
    ]

    const policyColumns = [
      { key: 'display_name', header: 'Policy Name', className: 'max-w-xs' },
      { key: 'enforcement_mode', header: 'Enforcement' },
      { key: 'scope', header: 'Scope', className: 'max-w-xs truncate' },
    ]

    const complianceColumns = [
      {
        key: 'policy_assignment_name',
        header: 'Policy',
        className: 'max-w-xs',
      },
      { key: 'resource_type', header: 'Resource Type' },
      {
        key: 'compliance_state',
        header: 'State',
        render: (value: string) => (
          <span className={value === 'Compliant' ? 'text-green-600' : 'text-red-600'}>{value}</span>
        ),
      },
      { key: 'resource_location', header: 'Location' },
    ]

    const nsgColumns = [
      { key: 'name', header: 'NSG Name' },
      { key: 'location', header: 'Location' },
      {
        key: 'risk_level',
        header: 'Risk Level',
        render: (value: string) => <span className={`risk-${value.toLowerCase()}`}>{value}</span>,
      },
      { key: 'resource_group', header: 'Resource Group' },
    ]

    switch (activeModule) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card text-center">
                <h3 className="text-lg font-medium text-gray-900">Secure Score</h3>
                <p className="text-3xl font-bold text-primary-600 mt-2">
                  {scanData.secure_score.percentage.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500">
                  {scanData.secure_score.current_score}/{scanData.secure_score.max_score}
                </p>
              </div>
              <div className="card text-center">
                <h3 className="text-lg font-medium text-gray-900">Recommendations</h3>
                <p className="text-3xl font-bold text-yellow-600 mt-2">
                  {scanData.recommendations.length}
                </p>
                <p className="text-sm text-gray-500">
                  {scanData.recommendations.filter(r => r.severity === 'Critical').length} Critical
                </p>
              </div>
              <div className="card text-center">
                <h3 className="text-lg font-medium text-gray-900">Public Resources</h3>
                <p className="text-3xl font-bold text-red-600 mt-2">
                  {scanData.public_resources.length}
                </p>
                <p className="text-sm text-gray-500">Internet accessible</p>
              </div>
            </div>
          </div>
        )

      case 'recommendations':
        return (
          <DataTable
            data={scanData.recommendations}
            columns={recommendationColumns}
            emptyMessage="No recommendations found"
          />
        )

      case 'exposure':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Public Resources</h3>
              <DataTable
                data={scanData.public_resources}
                columns={publicResourceColumns}
                emptyMessage="No public resources found"
              />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Network Security Groups</h3>
              <DataTable
                data={scanData.network_security_groups}
                columns={nsgColumns}
                emptyMessage="No NSGs found"
              />
            </div>
          </div>
        )

      case 'identity':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Users</h3>
              <DataTable
                data={scanData.users}
                columns={userColumns}
                emptyMessage="No users found"
              />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Role Assignments</h3>
              <DataTable
                data={scanData.role_assignments}
                columns={roleColumns}
                emptyMessage="No role assignments found"
              />
            </div>
          </div>
        )

      case 'policy':
        return (
          <DataTable
            data={scanData.policy_assignments}
            columns={policyColumns}
            emptyMessage="No policy assignments found"
          />
        )

      case 'compliance':
        return (
          <DataTable
            data={scanData.compliance_results}
            columns={complianceColumns}
            emptyMessage="No compliance results found"
          />
        )

      default:
        return <div>Select a module to view data</div>
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Raw Data Viewer</h1>
          <p className="text-gray-600 mt-1">Detailed view of Azure security scan results</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            disabled={!scanData}
            className="btn-secondary flex items-center space-x-2"
          >
            {showRawJson ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{showRawJson ? 'Hide' : 'Show'} JSON</span>
          </button>
          <button onClick={loadLatestScan} className="btn-primary flex items-center space-x-2">
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {!scanData ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No scan data available</h3>
          <p className="text-gray-600">Run a security scan first to view detailed data</p>
        </div>
      ) : (
        <>
          {/* Module Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {modules.map(module => (
                <button
                  key={module.key}
                  onClick={() => setActiveModule(module.key)}
                  className={`${
                    activeModule === module.key
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
                >
                  {module.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Scan Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">
                  Scan Date: {new Date(scanData.scan_timestamp).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">Tenant: {scanData.tenant_id}</p>
              </div>
              <div className="text-sm text-gray-600">
                {modules.find(m => m.key === activeModule)?.description}
              </div>
            </div>
          </div>

          {/* Raw JSON View */}
          {showRawJson && (
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Raw JSON Data</h3>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(scanData, null, 2))
                    alert('JSON copied to clipboard!')
                  }}
                  className="btn-secondary text-sm"
                >
                  Copy JSON
                </button>
              </div>
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96 text-xs">
                {JSON.stringify(scanData, null, 2)}
              </pre>
            </div>
          )}

          {/* Module Data */}
          <div>{renderModuleData()}</div>
        </>
      )}
    </div>
  )
}

export default DataViewer
