import React, { useState, useEffect } from 'react'
import { FileText, Download, Calendar, Eye } from 'lucide-react'
import { reportApi } from '../services/api'
import { LoadingSpinner } from '../components/LoadingSpinner'

interface Report {
  filename: string
  filepath: string
  size: number
  created: string
  modified: string
}

const ReportViewer: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedReport, setSelectedReport] = useState<string | null>(null)

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      const reportList = await reportApi.listReports()
      setReports(reportList)
    } catch (error) {
      console.error('Error loading reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async (format: 'markdown' | 'pdf') => {
    try {
      setLoading(true)
      await reportApi.generateReport(format)
      await loadReports() // Refresh the list
    } catch (error: any) {
      alert(`Report generation failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getReportType = (filename: string) => {
    if (filename.endsWith('.pdf')) return 'PDF'
    if (filename.endsWith('.md')) return 'Markdown'
    return 'Unknown'
  }

  if (loading && reports.length === 0) {
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
          <h1 className="text-3xl font-bold text-gray-900">Security Reports</h1>
          <p className="text-gray-600 mt-1">
            Generate and manage Azure security assessment reports
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => generateReport('markdown')}
            disabled={loading}
            className="btn-secondary flex items-center space-x-2"
          >
            <FileText className="h-4 w-4" />
            <span>Generate Markdown</span>
          </button>
          <button
            onClick={() => generateReport('pdf')}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Generate PDF</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-4">
          <LoadingSpinner size="md" />
          <p className="mt-2 text-gray-600">Generating report...</p>
        </div>
      )}

      {/* Reports List */}
      {reports.length === 0 && !loading ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No reports available</h3>
          <p className="text-gray-600 mb-4">Generate your first security report to get started</p>
          <div className="flex justify-center space-x-3">
            <button onClick={() => generateReport('markdown')} className="btn-secondary">
              Generate Markdown Report
            </button>
            <button onClick={() => generateReport('pdf')} className="btn-primary">
              Generate PDF Report
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {reports.map((report, index) => (
            <div key={index} className="card hover:shadow-md transition-shadow duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                      <FileText className="h-6 w-6 text-primary-600" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {report.filename}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>{new Date(report.created).toLocaleDateString()}</span>
                      </div>
                      <span>•</span>
                      <span>{formatFileSize(report.size)}</span>
                      <span>•</span>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          getReportType(report.filename) === 'PDF'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {getReportType(report.filename)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {getReportType(report.filename) === 'Markdown' && (
                    <button
                      onClick={() =>
                        setSelectedReport(
                          selectedReport === report.filename ? null : report.filename
                        )
                      }
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Eye className="h-4 w-4" />
                      <span>{selectedReport === report.filename ? 'Hide' : 'Preview'}</span>
                    </button>
                  )}
                  <a
                    href={`/api/reports/${encodeURIComponent(report.filename)}`}
                    download
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download</span>
                  </a>
                </div>
              </div>

              {/* Markdown Preview */}
              {selectedReport === report.filename &&
                getReportType(report.filename) === 'Markdown' && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-600 italic">
                          Markdown preview would be displayed here. Download the file to view the
                          complete report.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
            </div>
          ))}
        </div>
      )}

      {/* Report Generation Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h4 className="font-medium text-blue-900 mb-3">Report Contents</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h5 className="font-medium mb-2">Security Analysis</h5>
            <ul className="space-y-1">
              <li>• Microsoft Defender secure score</li>
              <li>• Security recommendations by severity</li>
              <li>• Public resource exposure analysis</li>
              <li>• Network security group configurations</li>
            </ul>
          </div>
          <div>
            <h5 className="font-medium mb-2">Identity & Compliance</h5>
            <ul className="space-y-1">
              <li>• User and role assignments</li>
              <li>• Multi-factor authentication status</li>
              <li>• Guest user analysis</li>
              <li>• Azure Policy compliance results</li>
            </ul>
          </div>
        </div>
        <div className="mt-4 p-3 bg-blue-100 rounded-lg">
          <p className="text-sm text-blue-900">
            <strong>Note:</strong> Reports are generated based on the most recent scan data. Run a
            new scan before generating reports to ensure the latest information is included.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ReportViewer
