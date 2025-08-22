import React, { useState, useEffect } from 'react'
import {
  Users,
  UserCheck,
  UserX,
  Bot,
  UsersIcon,
  HelpCircle,
  AlertTriangle,
  Play,
  Loader2,
} from 'lucide-react'
import { authApi, scanApi, type AuthStatus, type IdentityScanResult } from '../services/api'

const getIdentityIcon = (identityType: string) => {
  switch (identityType) {
    case 'users':
      return UserCheck
    case 'service_principals':
      return Bot
    case 'groups':
      return UsersIcon
    case 'managed_identities':
      return Users
    case 'unknown_or_deleted':
      return UserX
    default:
      return HelpCircle
  }
}

const getIdentityColor = (identityType: string) => {
  switch (identityType) {
    case 'users':
      return 'blue'
    case 'service_principals':
      return 'purple'
    case 'groups':
      return 'green'
    case 'managed_identities':
      return 'indigo'
    case 'unknown_or_deleted':
      return 'red'
    default:
      return 'gray'
  }
}

const getIdentityEmoji = (identityType: string) => {
  switch (identityType) {
    case 'users':
      return '👤'
    case 'service_principals':
      return '🤖'
    case 'groups':
      return '👥'
    case 'managed_identities':
      return '🆔'
    case 'unknown_or_deleted':
      return '❓'
    default:
      return '🧩'
  }
}

const getIdentityDisplayName = (identityType: string) => {
  switch (identityType) {
    case 'users':
      return 'Users'
    case 'service_principals':
      return 'Service Principals'
    case 'groups':
      return 'Groups'
    case 'managed_identities':
      return 'Managed Identities'
    case 'unknown_or_deleted':
      return 'Unknown/Deleted'
    default:
      return identityType
  }
}

export const EnhancedIdentityBreakdown: React.FC = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [identityData, setIdentityData] = useState<IdentityScanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkAuthStatus = async () => {
    try {
      const status = await authApi.getStatus()
      setAuthStatus(status)
    } catch (err: any) {
      console.error('Error checking auth status:', err)
      setAuthStatus({ authenticated: false, error: err.message })
    }
  }

  const loadIdentityData = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await scanApi.getIdentityScan()
      setIdentityData(data)
    } catch (err: any) {
      console.error('Error loading identity data:', err)
      setError(err.message || 'Failed to load identity data')
    } finally {
      setLoading(false)
    }
  }

  const initiateLogin = async () => {
    try {
      const response = await authApi.initiateLogin()
      // Show device code flow instructions
      alert(`Please go to ${response.verification_uri} and enter code: ${response.user_code}`)

      // Poll for completion (simplified - in real app, use proper polling)
      setTimeout(async () => {
        await checkAuthStatus()
        if (authStatus?.authenticated) {
          await loadIdentityData()
        }
      }, 30000) // Check after 30 seconds
    } catch (err: any) {
      setError(err.message || 'Failed to initiate login')
    }
  }

  useEffect(() => {
    checkAuthStatus()
  }, [])

  useEffect(() => {
    if (authStatus?.authenticated) {
      loadIdentityData()
    }
  }, [authStatus?.authenticated])

  // Not authenticated state
  if (authStatus && !authStatus.authenticated) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-yellow-900 mb-2">Authentication Required</h3>
          <p className="text-yellow-800 mb-4">
            ⚠️ You must complete Azure login before identity data can be scanned.
          </p>
          <button
            onClick={initiateLogin}
            className="btn-primary flex items-center space-x-2 mx-auto"
          >
            <Play className="h-4 w-4" />
            <span>Start Login</span>
          </button>
        </div>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>

        <div className="flex items-center justify-center min-h-64">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading identity data...</p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-red-900 mb-2">Error Loading Identity Data</h3>
          <p className="text-red-800 mb-4">{error}</p>
          <button
            onClick={loadIdentityData}
            className="btn-secondary flex items-center space-x-2 mx-auto"
          >
            <Play className="h-4 w-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  // No data state
  if (!identityData || Object.values(identityData).every(arr => arr.length === 0)) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <HelpCircle className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-blue-900 mb-2">No Role Assignments Found</h3>
          <p className="text-blue-800">
            No role assignments detected. You may not have access to identity metadata.
          </p>
        </div>
      </div>
    )
  }

  const totalAssignments = Object.values(identityData).reduce(
    (sum, assignments) => sum + assignments.length,
    0
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">({totalAssignments} total role assignments)</div>
          {authStatus?.expires_in_minutes && authStatus.expires_in_minutes < 60 && (
            <div className="text-sm text-yellow-600">
              Auth expires in {authStatus.expires_in_minutes}min
            </div>
          )}
        </div>
      </div>

      {/* Identity Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(identityData).map(([identityType, assignments]) => {
          if (assignments.length === 0) return null

          const Icon = getIdentityIcon(identityType)
          const color = getIdentityColor(identityType)
          const emoji = getIdentityEmoji(identityType)
          const displayName = getIdentityDisplayName(identityType)

          // Group assignments by role
          const roleGroups: Record<string, number> = {}
          assignments.forEach((assignment: any) => {
            roleGroups[assignment.role_definition_name] =
              (roleGroups[assignment.role_definition_name] || 0) + 1
          })

          const sortedRoles = Object.entries(roleGroups).sort(([, a], [, b]) => b - a)

          return (
            <div key={identityType} className="card hover:shadow-md transition-shadow">
              {/* Identity Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg bg-${color}-100`}>
                    <Icon className={`h-5 w-5 text-${color}-600`} />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{emoji}</span>
                      <h3 className="font-medium text-gray-900">{displayName}</h3>
                    </div>
                    <p className="text-sm text-gray-500">{assignments.length} assignments</p>
                  </div>
                </div>
                <div className={`text-2xl font-bold text-${color}-600`}>{assignments.length}</div>
              </div>

              {/* Role Breakdown */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Top Roles:</h4>
                {sortedRoles.length > 0 ? (
                  <div className="space-y-1">
                    {sortedRoles.slice(0, 5).map(([roleName, count]) => (
                      <div key={roleName} className="flex items-center justify-between">
                        <span
                          className="text-sm text-gray-600 truncate flex-1 pr-2"
                          title={roleName}
                        >
                          • {roleName}
                        </span>
                        <span className="text-sm font-medium text-gray-900 bg-gray-100 px-2 py-1 rounded-md">
                          {count}
                        </span>
                      </div>
                    ))}
                    {sortedRoles.length > 5 && (
                      <div className="text-xs text-gray-500 pt-1">
                        +{sortedRoles.length - 5} more roles...
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 italic">No roles found</div>
                )}
              </div>

              {/* Progress Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>% of total assignments</span>
                  <span>{((assignments.length / totalAssignments) * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full bg-${color}-500`}
                    style={{ width: `${(assignments.length / totalAssignments) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(identityData).map(([identityType, assignments]) => {
          const color = getIdentityColor(identityType)
          const displayName = getIdentityDisplayName(identityType)

          return (
            <div
              key={identityType}
              className={`bg-${color}-50 border border-${color}-200 rounded-lg p-4 text-center`}
            >
              <div className={`text-2xl font-bold text-${color}-600`}>{assignments.length}</div>
              <div className={`text-sm text-${color}-800`}>{displayName}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
