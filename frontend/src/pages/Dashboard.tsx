import React, { useState, useEffect } from 'react'
import { Shield, AlertTriangle, Globe, Users, Play, Download, RefreshCw } from 'lucide-react'
import { ScoreCard } from '../components/ScoreCard'
import { DataTable } from '../components/DataTable'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { scanApi, reportApi, type ScanResult } from '../services/api'

const Dashboard: React.FC = () => {
  const [scanData, setScanData] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadLatestScan()
  }, [])

  const loadLatestScan = async () => {
    try {
      const latest = await scanApi.getLatestScan()
      setScanData(latest)
    } catch (err) {
      console.error('Error loading latest scan:', err)
    }
  }

  const runScan = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await scanApi.runFullScan()
      setScanData(result)
    } catch (err: any) {
      setError(err.message || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async (format: 'markdown' | 'pdf') => {
    try {
      await reportApi.generateReport(format)
    } catch (err: any) {
      alert(`Report generation failed: ${err.message}`)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'red'
      case 'high':
        return 'red'
      case 'medium':
        return 'yellow'
      case 'low':
        return 'green'
      default:
        return 'gray'
    }
  }

  const recommendationColumns = [
    {
      key: 'name',
      header: 'Recommendation',
      render: (value: string) => (
        <div className="max-w-xs truncate" title={value}>
          {value}
        </div>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (value: string) => <span className={`severity-${value.toLowerCase()}`}>{value}</span>,
    },
    {
      key: 'category',
      header: 'Category',
    },
    {
      key: 'affected_resources',
      header: 'Resources',
      render: (value: number) => <span className="font-medium">{value}</span>,
    },
  ]

  const publicResourceColumns = [
    {
      key: 'resource_name',
      header: 'Resource Name',
    },
    {
      key: 'resource_type',
      header: 'Type',
    },
    {
      key: 'public_ip',
      header: 'Public IP',
      render: (value: string) => value || 'N/A',
    },
    {
      key: 'ports',
      header: 'Ports',
      render: (ports: number[]) => (ports.length > 0 ? ports.join(', ') : 'N/A'),
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Running Azure security scan...</p>
          <p className="text-sm text-gray-500">This may take several minutes</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
          <p className="text-gray-600 mt-1">Azure security posture analysis and recommendations</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => generateReport('markdown')}
            disabled={!scanData}
            className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            <span>Export MD</span>
          </button>
          <button
            onClick={() => generateReport('pdf')}
            disabled={!scanData}
            className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            <span>Export PDF</span>
          </button>
          <button
            onClick={runScan}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            {loading ? <LoadingSpinner size="sm" /> : <Play className="h-4 w-4" />}
            <span>Run Scan</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {!scanData && !loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <Shield className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-blue-900 mb-2">No scan data available</h3>
          <p className="text-blue-800 mb-4">
            Run your first security scan to analyze your Azure environment
          </p>
          <button onClick={runScan} className="btn-primary">
            <Play className="h-4 w-4 mr-2" />
            Start Security Scan
          </button>
        </div>
      )}

      {scanData && (
        <>
          {/* Last scan info */}
          <div className="bg-gray-50 rounded-lg p-4 flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-600">
                Last scan: {new Date(scanData.scan_timestamp).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Tenant: {scanData.tenant_id}</p>
            </div>
            <button onClick={runScan} className="btn-secondary flex items-center space-x-2">
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>

          {/* Score Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <ScoreCard
              title="Secure Score"
              value={`${scanData.secure_score.percentage.toFixed(1)}%`}
              subtitle={`${scanData.secure_score.current_score}/${scanData.secure_score.max_score}`}
              icon={Shield}
              color={
                scanData.secure_score.percentage > 70
                  ? 'green'
                  : scanData.secure_score.percentage > 40
                    ? 'yellow'
                    : 'red'
              }
            />

            <ScoreCard
              title="Critical Issues"
              value={scanData.recommendations.filter(r => r.severity === 'Critical').length}
              subtitle="Immediate attention required"
              icon={AlertTriangle}
              color="red"
            />

            <ScoreCard
              title="Public Resources"
              value={scanData.public_resources.length}
              subtitle="Internet-facing assets"
              icon={Globe}
              color={
                scanData.public_resources.length > 10
                  ? 'red'
                  : scanData.public_resources.length > 5
                    ? 'yellow'
                    : 'green'
              }
            />

            <ScoreCard
              title="Users"
              value={scanData.users.length}
              subtitle={`${scanData.users.filter(u => !u.mfa_enabled).length} without MFA`}
              icon={Users}
              color={scanData.users.filter(u => !u.mfa_enabled).length > 0 ? 'yellow' : 'green'}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Recommendations by Severity
              </h3>
              <div className="space-y-3">
                {['Critical', 'High', 'Medium', 'Low'].map(severity => {
                  const count = scanData.recommendations.filter(r => r.severity === severity).length
                  const total = scanData.recommendations.length
                  const percentage = total > 0 ? (count / total) * 100 : 0

                  return (
                    <div key={severity} className="flex items-center space-x-3">
                      <span className={`w-16 text-sm severity-${severity.toLowerCase()}`}>
                        {severity}
                      </span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full bg-${getSeverityColor(severity)}-500`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 w-8">{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Security Metrics</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Policy Compliance</span>
                  <span className="font-medium">
                    {scanData.compliance_results.length > 0
                      ? `${((scanData.compliance_results.filter(c => c.compliance_state === 'Compliant').length / scanData.compliance_results.length) * 100).toFixed(1)}%`
                      : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">High-Risk NSGs</span>
                  <span className="font-medium text-red-600">
                    {
                      scanData.network_security_groups.filter(nsg => nsg.risk_level === 'High')
                        .length
                    }
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Guest Users</span>
                  <span className="font-medium text-yellow-600">
                    {scanData.users.filter(u => u.is_guest).length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Role Assignments</span>
                  <span className="font-medium">{scanData.role_assignments.length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Data Tables */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Top Security Recommendations
              </h3>
              <DataTable
                data={scanData.recommendations.slice(0, 10)}
                columns={recommendationColumns}
                emptyMessage="No recommendations found"
              />
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Public Resources</h3>
              <DataTable
                data={scanData.public_resources}
                columns={publicResourceColumns}
                emptyMessage="No public resources found"
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Dashboard
