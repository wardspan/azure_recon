import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import jinja2
from weasyprint import HTML, CSS
from models import ScanResult, ReportRequest

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.jinja_env.filters['datetime'] = self._format_datetime
        self.jinja_env.filters['percentage'] = self._format_percentage
        self.jinja_env.filters['severity_color'] = self._severity_color
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display"""
        if not dt:
            return "N/A"
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage value"""
        if value is None:
            return "0%"
        return f"{value:.1f}%"
    
    def _severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        color_map = {
            'Critical': '#dc2626',
            'High': '#ea580c', 
            'Medium': '#d97706',
            'Low': '#65a30d',
            'Info': '#0891b2'
        }
        return color_map.get(severity, '#6b7280')
    
    async def generate_markdown_report(self, scan_data: ScanResult) -> str:
        """Generate markdown report from scan data"""
        try:
            template = self.jinja_env.get_template('report_template.md.j2')
            
            # Prepare template context
            context = {
                'scan_data': scan_data,
                'generated_at': datetime.now(),
                'tenant_id': scan_data.tenant_id,
                'scan_timestamp': scan_data.scan_timestamp,
                'secure_score': scan_data.secure_score,
                'recommendations': scan_data.recommendations,
                'public_resources': scan_data.public_resources,
                'network_security_groups': scan_data.network_security_groups,
                'users': scan_data.users,
                'role_assignments': scan_data.role_assignments,
                'policy_assignments': scan_data.policy_assignments,
                'compliance_results': scan_data.compliance_results,
                
                # Summary statistics
                'total_recommendations': len(scan_data.recommendations),
                'high_severity_recommendations': len([r for r in scan_data.recommendations if r.severity == 'High']),
                'critical_severity_recommendations': len([r for r in scan_data.recommendations if r.severity == 'Critical']),
                'total_public_resources': len(scan_data.public_resources),
                'high_risk_nsgs': len([nsg for nsg in scan_data.network_security_groups if nsg.risk_level == 'High']),
                'total_users': len(scan_data.users),
                'guest_users': len([u for u in scan_data.users if u.is_guest]),
                'users_without_mfa': len([u for u in scan_data.users if not u.mfa_enabled]),
                'total_role_assignments': len(scan_data.role_assignments),
                'privileged_assignments': len([ra for ra in scan_data.role_assignments if any(priv in ra.role_definition_name.lower() for priv in ['admin', 'owner', 'contributor'])]),
                'total_policy_assignments': len(scan_data.policy_assignments),
                'non_compliant_resources': len([cr for cr in scan_data.compliance_results if cr.compliance_state != 'Compliant'])
            }
            
            markdown_content = template.render(context)
            
            # Save markdown file
            filename = f"azure_recon_{scan_data.tenant_id}_{scan_data.scan_timestamp.strftime('%Y%m%d_%H%M%S')}.md"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Markdown report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating markdown report: {str(e)}")
            raise
    
    async def generate_pdf_report(self, scan_data: ScanResult) -> str:
        """Generate PDF report from scan data"""
        try:
            # First generate markdown
            md_filepath = await self.generate_markdown_report(scan_data)
            
            # Convert markdown to HTML for PDF generation
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Azure Recon Report - {{ tenant_id }}</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 210mm;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        text-align: center;
                        border-bottom: 3px solid #0078d4;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }
                    .logo {
                        font-size: 24px;
                        font-weight: bold;
                        color: #0078d4;
                    }
                    .summary-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }
                    .summary-card {
                        border: 1px solid #e1e5e9;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        background: #f8f9fa;
                    }
                    .summary-value {
                        font-size: 32px;
                        font-weight: bold;
                        margin: 10px 0;
                    }
                    .summary-label {
                        color: #666;
                        font-size: 14px;
                    }
                    .score-high { color: #28a745; }
                    .score-medium { color: #ffc107; }
                    .score-low { color: #dc3545; }
                    .critical { color: #dc2626; }
                    .high { color: #ea580c; }
                    .medium { color: #d97706; }
                    .low { color: #65a30d; }
                    .section {
                        margin: 30px 0;
                        page-break-inside: avoid;
                    }
                    .section-title {
                        font-size: 20px;
                        font-weight: bold;
                        color: #0078d4;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #e1e5e9;
                        padding-bottom: 5px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }
                    th, td {
                        border: 1px solid #e1e5e9;
                        padding: 12px 8px;
                        text-align: left;
                        font-size: 12px;
                    }
                    th {
                        background-color: #f8f9fa;
                        font-weight: bold;
                    }
                    .page-break {
                        page-break-before: always;
                    }
                    @page {
                        margin: 2cm;
                        @bottom-center {
                            content: "Page " counter(page) " of " counter(pages);
                            font-size: 12px;
                            color: #666;
                        }
                    }
                </style>
            </head>
            <body>
                {{ content }}
            </body>
            </html>
            """
            
            # Create HTML template
            html_jinja_template = jinja2.Template(html_template)
            
            # Prepare content for HTML
            template = self.jinja_env.get_template('report_template.md.j2')
            context = {
                'scan_data': scan_data,
                'generated_at': datetime.now(),
                'tenant_id': scan_data.tenant_id,
                'scan_timestamp': scan_data.scan_timestamp,
                'secure_score': scan_data.secure_score,
                'recommendations': scan_data.recommendations,
                'public_resources': scan_data.public_resources,
                'network_security_groups': scan_data.network_security_groups,
                'users': scan_data.users,
                'role_assignments': scan_data.role_assignments,
                'policy_assignments': scan_data.policy_assignments,
                'compliance_results': scan_data.compliance_results,
            }
            
            # Convert to HTML-friendly format
            html_content = self._convert_to_html_content(context)
            html_document = html_jinja_template.render(content=html_content, **context)
            
            # Generate PDF
            filename = f"azure_recon_{scan_data.tenant_id}_{scan_data.scan_timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = self.reports_dir / filename
            
            HTML(string=html_document).write_pdf(str(filepath))
            
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _convert_to_html_content(self, context: Dict[str, Any]) -> str:
        """Convert template context to HTML content"""
        scan_data = context['scan_data']
        
        html_content = f"""
        <div class="header">
            <div class="logo">🔒 Azure Recon Security Report</div>
            <h2>Tenant: {scan_data.tenant_id}</h2>
            <p>Generated: {self._format_datetime(context['generated_at'])}</p>
            <p>Scan Time: {self._format_datetime(scan_data.scan_timestamp)}</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value score-{'high' if scan_data.secure_score.percentage > 70 else 'medium' if scan_data.secure_score.percentage > 40 else 'low'}">{scan_data.secure_score.percentage:.1f}%</div>
                <div class="summary-label">Secure Score</div>
            </div>
            <div class="summary-card">
                <div class="summary-value critical">{len([r for r in scan_data.recommendations if r.severity == 'Critical'])}</div>
                <div class="summary-label">Critical Issues</div>
            </div>
            <div class="summary-card">
                <div class="summary-value high">{len([r for r in scan_data.recommendations if r.severity == 'High'])}</div>
                <div class="summary-label">High Priority</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{len(scan_data.public_resources)}</div>
                <div class="summary-label">Public Resources</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🛡️ Security Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Recommendation</th>
                        <th>Severity</th>
                        <th>Category</th>
                        <th>Affected Resources</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{r.name}</td>
                        <td class="{r.severity.lower()}">{r.severity}</td>
                        <td>{r.category}</td>
                        <td>{r.affected_resources}</td>
                    </tr>
                    ''' for r in scan_data.recommendations[:20]])}
                </tbody>
            </table>
        </div>

        <div class="section page-break">
            <h2 class="section-title">🌐 Public Resources</h2>
            <table>
                <thead>
                    <tr>
                        <th>Resource Name</th>
                        <th>Type</th>
                        <th>Public IP</th>
                        <th>Ports</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{r.resource_name}</td>
                        <td>{r.resource_type}</td>
                        <td>{r.public_ip or 'N/A'}</td>
                        <td>{', '.join(map(str, r.ports)) if r.ports else 'N/A'}</td>
                    </tr>
                    ''' for r in scan_data.public_resources])}
                </tbody>
            </table>
        </div>

        <div class="section page-break">
            <h2 class="section-title">👥 Identity & Access</h2>
            <p><strong>Total Users:</strong> {len(scan_data.users)}</p>
            <p><strong>Guest Users:</strong> {len([u for u in scan_data.users if u.is_guest])}</p>
            <p><strong>Users without MFA:</strong> {len([u for u in scan_data.users if not u.mfa_enabled])}</p>
            <p><strong>Total Role Assignments:</strong> {len(scan_data.role_assignments)}</p>
        </div>

        <div class="section page-break">
            <h2 class="section-title">📋 Policy Compliance</h2>
            <p><strong>Policy Assignments:</strong> {len(scan_data.policy_assignments)}</p>
            <p><strong>Non-Compliant Resources:</strong> {len([cr for cr in scan_data.compliance_results if cr.compliance_state != 'Compliant'])}</p>
            <p><strong>Compliance Rate:</strong> {(len([cr for cr in scan_data.compliance_results if cr.compliance_state == 'Compliant']) / len(scan_data.compliance_results) * 100) if scan_data.compliance_results else 0:.1f}%</p>
        </div>
        """
        
        return html_content
    
    async def get_report_file(self, filepath: str) -> Optional[bytes]:
        """Read report file and return contents"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading report file {filepath}: {str(e)}")
        return None
    
    async def list_reports(self) -> list:
        """List all generated reports"""
        reports = []
        try:
            for file_path in self.reports_dir.glob("azure_recon_*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    reports.append({
                        'filename': file_path.name,
                        'filepath': str(file_path),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
        except Exception as e:
            logger.error(f"Error listing reports: {str(e)}")
        
        return sorted(reports, key=lambda x: x['created'], reverse=True)

# Global report generator instance
report_generator = ReportGenerator()