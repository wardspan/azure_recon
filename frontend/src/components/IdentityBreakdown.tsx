import React from 'react'
import { Users, UserCheck, UserX, Bot, UsersIcon, HelpCircle } from 'lucide-react'

interface IdentityBreakdownProps {
  identitySummary: Record<string, { count: number; roles: Record<string, number> }>
}

const getIdentityIcon = (identityType: string) => {
  switch (identityType) {
    case 'User':
      return UserCheck
    case 'ServicePrincipal':
      return Bot
    case 'Group':
      return UsersIcon
    case 'ManagedIdentity':
      return Users
    case 'Unknown or Deleted':
      return UserX
    default:
      return HelpCircle
  }
}

const getIdentityColor = (identityType: string) => {
  switch (identityType) {
    case 'User':
      return 'blue'
    case 'ServicePrincipal':
      return 'purple'
    case 'Group':
      return 'green'
    case 'ManagedIdentity':
      return 'indigo'
    case 'Unknown or Deleted':
      return 'red'
    default:
      return 'gray'
  }
}

const getIdentityEmoji = (identityType: string) => {
  switch (identityType) {
    case 'User':
      return '👤'
    case 'ServicePrincipal':
      return '🤖'
    case 'Group':
      return '👥'
    case 'ManagedIdentity':
      return '🆔'
    case 'Unknown or Deleted':
      return '❓'
    default:
      return '🧩'
  }
}

export const IdentityBreakdown: React.FC<IdentityBreakdownProps> = ({ identitySummary }) => {
  if (!identitySummary || Object.keys(identitySummary).length === 0) {
    return (
      <div className="card text-center py-8">
        <HelpCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Identity Data Available</h3>
        <p className="text-gray-600">Run a scan to see identity type breakdown</p>
      </div>
    )
  }

  // Sort identity types by count (descending)
  const sortedIdentities = Object.entries(identitySummary).sort(([, a], [, b]) => b.count - a.count)

  const totalAssignments = Object.values(identitySummary).reduce(
    (sum, identity) => sum + identity.count,
    0
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🔎</span>
          <h2 className="text-xl font-semibold text-gray-900">Identity Type Breakdown</h2>
        </div>
        <div className="text-sm text-gray-500">({totalAssignments} total role assignments)</div>
      </div>

      {/* Identity Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedIdentities.map(([identityType, data]) => {
          const Icon = getIdentityIcon(identityType)
          const color = getIdentityColor(identityType)
          const emoji = getIdentityEmoji(identityType)

          // Sort roles by count (descending)
          const sortedRoles = Object.entries(data.roles).sort(([, a], [, b]) => b - a)

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
                      <h3 className="font-medium text-gray-900">{identityType}</h3>
                    </div>
                    <p className="text-sm text-gray-500">{data.count} entries</p>
                  </div>
                </div>
                <div className={`text-2xl font-bold text-${color}-600`}>{data.count}</div>
              </div>

              {/* Role Breakdown */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Role Assignments:</h4>
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
                  <span>{((data.count / totalAssignments) * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full bg-${color}-500`}
                    style={{ width: `${(data.count / totalAssignments) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{identitySummary.User?.count || 0}</div>
          <div className="text-sm text-blue-800">Users</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {identitySummary.ServicePrincipal?.count || 0}
          </div>
          <div className="text-sm text-purple-800">Service Principals</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {identitySummary.Group?.count || 0}
          </div>
          <div className="text-sm text-green-800">Groups</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-600">
            {identitySummary['Unknown or Deleted']?.count || 0}
          </div>
          <div className="text-sm text-red-800">Unknown/Deleted</div>
        </div>
      </div>
    </div>
  )
}
