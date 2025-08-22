import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Import our modules
from auth import azure_auth
from secure_score import secure_score_analyzer
from exposure import exposure_analyzer
from identity import identity_analyzer
from policy import policy_analyzer
from reporting import report_generator
from role_analysis import summarize_identity_roles, role_analyzer, get_detailed_identity_roles
from models import (
    AuthResponse, AuthStatus, ScanResult, ReportRequest,
    SecureScoreData, Recommendation, PublicResource, 
    NetworkSecurityGroup, UserInfo, RoleAssignment,
    PolicyAssignment, ComplianceResult, Subscription, 
    PasswordLoginRequest, ServicePrincipalLoginRequest,
    IdentityScanResult, IdentityRoleAssignment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Azure Recon API",
    description="Azure security posture assessment tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store latest scan results
latest_scan_result: Optional[ScanResult] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Azure Recon API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Authentication endpoints
@app.post("/api/login", response_model=AuthResponse)
async def initiate_login():
    """Initiate Azure device code authentication flow"""
    try:
        auth_response = await azure_auth.initiate_device_code_flow()
        return auth_response
    except Exception as e:
        logger.error(f"Login initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication initiation failed: {str(e)}")

@app.post("/api/login/password", response_model=AuthStatus)
async def login_with_password(request: PasswordLoginRequest):
    """Login with username and password"""
    try:
        auth_status = await azure_auth.authenticate_with_password(
            request.username, 
            request.password, 
            request.tenant_id
        )
        return auth_status
    except Exception as e:
        logger.error(f"Password login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password authentication failed: {str(e)}")

@app.post("/api/login/service-principal", response_model=AuthStatus)
async def login_with_service_principal(request: ServicePrincipalLoginRequest):
    """Login with service principal (App ID + Secret)"""
    try:
        auth_status = await azure_auth.authenticate_with_service_principal(
            request.client_id,
            request.client_secret, 
            request.tenant_id
        )
        return auth_status
    except Exception as e:
        logger.error(f"Service principal login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service principal authentication failed: {str(e)}")

@app.post("/api/login/cli", response_model=AuthStatus)
async def login_with_cli():
    """Login using existing Azure CLI session"""
    try:
        auth_status = await azure_auth.authenticate_with_cli()
        return auth_status
    except Exception as e:
        logger.error(f"Azure CLI login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Azure CLI authentication failed: {str(e)}")

@app.post("/api/auth/complete", response_model=AuthStatus)
async def complete_authentication():
    """Complete Azure authentication"""
    try:
        auth_status = await azure_auth.complete_authentication()
        return auth_status
    except Exception as e:
        logger.error(f"Authentication completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/api/auth/status", response_model=AuthStatus)
async def get_auth_status():
    """Get current authentication status"""
    try:
        expires_in_minutes = None
        if azure_auth.expires_at:
            from datetime import datetime
            expires_in_seconds = (azure_auth.expires_at - datetime.now()).total_seconds()
            expires_in_minutes = max(0, int(expires_in_seconds / 60))
        
        return AuthStatus(
            authenticated=azure_auth.is_authenticated(),
            tenant_id=azure_auth.tenant_id,
            expires_at=azure_auth.expires_at,
            expires_in_minutes=expires_in_minutes
        )
    except Exception as e:
        logger.error(f"Error getting auth status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting authentication status: {str(e)}")

@app.get("/api/subscriptions", response_model=List[Subscription])
async def get_subscriptions():
    """Get all accessible Azure subscriptions"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        return subscriptions
    except Exception as e:
        logger.error(f"Error getting subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting subscriptions: {str(e)}")

# Scan endpoints
@app.post("/api/scan", response_model=ScanResult)
async def run_full_scan(background_tasks: BackgroundTasks):
    """Run a complete Azure security scan"""
    global latest_scan_result
    
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get subscriptions first
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        
        if not subscription_ids:
            raise HTTPException(status_code=400, detail="No subscriptions found")
        
        logger.info(f"Starting scan for {len(subscription_ids)} subscriptions")
        
        # Run all analyses in parallel for better performance
        secure_score_task = secure_score_analyzer.get_secure_scores(subscription_ids)
        recommendations_task = secure_score_analyzer.get_security_recommendations(subscription_ids)
        public_resources_task = exposure_analyzer.get_public_resources(subscription_ids)
        nsgs_task = exposure_analyzer.get_network_security_groups(subscription_ids)
        users_task = identity_analyzer.get_users_info()
        role_assignments_task = identity_analyzer.get_role_assignments(subscription_ids)
        policy_assignments_task = policy_analyzer.get_policy_assignments(subscription_ids)
        compliance_results_task = policy_analyzer.get_compliance_results(subscription_ids)
        identity_summary_task = summarize_identity_roles(subscription_ids)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(
            secure_score_task,
            recommendations_task,
            public_resources_task,
            nsgs_task,
            users_task,
            role_assignments_task,
            policy_assignments_task,
            compliance_results_task,
            identity_summary_task,
            return_exceptions=True
        )
        
        # Extract results and handle any exceptions
        secure_score = results[0] if not isinstance(results[0], Exception) else SecureScoreData(current_score=0, max_score=100, percentage=0, control_scores=[])
        recommendations = results[1] if not isinstance(results[1], Exception) else []
        public_resources = results[2] if not isinstance(results[2], Exception) else []
        nsgs = results[3] if not isinstance(results[3], Exception) else []
        users = results[4] if not isinstance(results[4], Exception) else []
        role_assignments = results[5] if not isinstance(results[5], Exception) else []
        policy_assignments = results[6] if not isinstance(results[6], Exception) else []
        compliance_results = results[7] if not isinstance(results[7], Exception) else []
        identity_summary = results[8] if not isinstance(results[8], Exception) else {}
        
        # Create scan result
        scan_result = ScanResult(
            tenant_id=azure_auth.tenant_id or "unknown",
            scan_timestamp=datetime.now(),
            secure_score=secure_score,
            recommendations=recommendations,
            public_resources=public_resources,
            network_security_groups=nsgs,
            users=users,
            role_assignments=role_assignments,
            policy_assignments=policy_assignments,
            compliance_results=compliance_results,
            identity_summary=identity_summary
        )
        
        latest_scan_result = scan_result
        logger.info("Scan completed successfully")
        
        return scan_result
        
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/scan/latest", response_model=Optional[ScanResult])
async def get_latest_scan():
    """Get the latest scan results"""
    return latest_scan_result

# Individual module endpoints
@app.get("/api/secure_score", response_model=SecureScoreData)
async def get_secure_score():
    """Get Microsoft Defender for Cloud secure score"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        secure_score = await secure_score_analyzer.get_secure_scores(subscription_ids)
        return secure_score
    except Exception as e:
        logger.error(f"Error getting secure score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting secure score: {str(e)}")

@app.get("/api/recommendations", response_model=List[Recommendation])
async def get_recommendations():
    """Get security recommendations"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        recommendations = await secure_score_analyzer.get_security_recommendations(subscription_ids)
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.get("/api/exposure", response_model=List[PublicResource])
async def get_exposure():
    """Get exposed/public resources"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        public_resources = await exposure_analyzer.get_public_resources(subscription_ids)
        return public_resources
    except Exception as e:
        logger.error(f"Error getting exposure data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting exposure data: {str(e)}")

@app.get("/api/nsgs", response_model=List[NetworkSecurityGroup])
async def get_network_security_groups():
    """Get Network Security Groups analysis"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        nsgs = await exposure_analyzer.get_network_security_groups(subscription_ids)
        return nsgs
    except Exception as e:
        logger.error(f"Error getting NSGs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting NSGs: {str(e)}")

@app.get("/api/nsgs/detailed")
async def get_detailed_nsgs():
    """Get detailed NSG analysis with risk explanations"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        nsgs = await exposure_analyzer.get_network_security_groups(subscription_ids)
        
        # Format detailed response with risk explanations
        detailed_nsgs = []
        for nsg in nsgs:
            nsg_detail = {
                "name": nsg.name,
                "location": nsg.location,
                "resource_group": nsg.resource_group,
                "risk_level": nsg.risk_level,
                "risk_reasons": nsg.risk_reasons,
                "risky_rules_count": len(nsg.risky_rules),
                "total_rules_count": len(nsg.rules),
                "risky_rules": nsg.risky_rules
            }
            detailed_nsgs.append(nsg_detail)
        
        # Sort by risk level (High first, then Medium, then Low)
        risk_order = {"High": 0, "Medium": 1, "Low": 2}
        detailed_nsgs.sort(key=lambda x: risk_order.get(x["risk_level"], 3))
        
        return detailed_nsgs
        
    except Exception as e:
        logger.error(f"Error getting detailed NSGs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting detailed NSGs: {str(e)}")

@app.get("/api/identity", response_model=List[UserInfo])
async def get_identity():
    """Get identity and user information"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        users = await identity_analyzer.get_users_info()
        return users
    except Exception as e:
        logger.error(f"Error getting identity data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting identity data: {str(e)}")

@app.get("/api/roles", response_model=List[RoleAssignment])
async def get_role_assignments():
    """Get role assignments"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        role_assignments = await identity_analyzer.get_role_assignments(subscription_ids)
        return role_assignments
    except Exception as e:
        logger.error(f"Error getting role assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting role assignments: {str(e)}")

@app.get("/api/identity-summary")
async def get_identity_summary():
    """Get identity-type breakdown of all role assignments"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        identity_breakdown = await summarize_identity_roles(subscription_ids)
        return identity_breakdown
    except Exception as e:
        logger.error(f"Error getting identity summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting identity summary: {str(e)}")

@app.get("/api/scan/identity", response_model=IdentityScanResult)
async def get_identity_scan():
    """Get detailed role assignments grouped by identity type"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        detailed_roles = await get_detailed_identity_roles(subscription_ids)
        
        # Convert to IdentityScanResult format
        return IdentityScanResult(
            users=[IdentityRoleAssignment(**assignment) for assignment in detailed_roles["users"]],
            service_principals=[IdentityRoleAssignment(**assignment) for assignment in detailed_roles["service_principals"]],
            managed_identities=[IdentityRoleAssignment(**assignment) for assignment in detailed_roles["managed_identities"]],
            groups=[IdentityRoleAssignment(**assignment) for assignment in detailed_roles["groups"]],
            unknown_or_deleted=[IdentityRoleAssignment(**assignment) for assignment in detailed_roles["unknown_or_deleted"]]
        )
    except Exception as e:
        logger.error(f"Error getting identity scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting identity scan: {str(e)}")

@app.get("/api/policy", response_model=List[PolicyAssignment])
async def get_policy():
    """Get policy assignments"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        policies = await policy_analyzer.get_policy_assignments(subscription_ids)
        return policies
    except Exception as e:
        logger.error(f"Error getting policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting policies: {str(e)}")

@app.get("/api/compliance", response_model=List[ComplianceResult])
async def get_compliance():
    """Get policy compliance results"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        subscriptions = await azure_auth.get_subscriptions()
        subscription_ids = [sub.subscription_id for sub in subscriptions]
        compliance = await policy_analyzer.get_compliance_results(subscription_ids)
        return compliance
    except Exception as e:
        logger.error(f"Error getting compliance data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting compliance data: {str(e)}")

# Report endpoints
@app.post("/api/report")
async def generate_report(request: ReportRequest):
    """Generate a security assessment report"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Use latest scan result or run a new scan
    scan_data = latest_scan_result
    if not scan_data:
        # Run a new scan if no recent data
        try:
            subscriptions = await azure_auth.get_subscriptions()
            subscription_ids = [sub.subscription_id for sub in subscriptions]
            
            # Quick scan for report generation
            secure_score = await secure_score_analyzer.get_secure_scores(subscription_ids)
            recommendations = await secure_score_analyzer.get_security_recommendations(subscription_ids)
            public_resources = await exposure_analyzer.get_public_resources(subscription_ids)
            nsgs = await exposure_analyzer.get_network_security_groups(subscription_ids)
            users = await identity_analyzer.get_users_info()
            role_assignments = await identity_analyzer.get_role_assignments(subscription_ids)
            policy_assignments = await policy_analyzer.get_policy_assignments(subscription_ids)
            compliance_results = await policy_analyzer.get_compliance_results(subscription_ids)
            identity_summary = await summarize_identity_roles(subscription_ids)
            
            scan_data = ScanResult(
                tenant_id=azure_auth.tenant_id or "unknown",
                scan_timestamp=datetime.now(),
                secure_score=secure_score,
                recommendations=recommendations,
                public_resources=public_resources,
                network_security_groups=nsgs,
                users=users,
                role_assignments=role_assignments,
                policy_assignments=policy_assignments,
                compliance_results=compliance_results,
                identity_summary=identity_summary
            )
        except Exception as e:
            logger.error(f"Error running scan for report: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating scan data for report: {str(e)}")
    
    try:
        if request.format.lower() == "pdf":
            filepath = await report_generator.generate_pdf_report(scan_data)
            return FileResponse(
                filepath, 
                filename=f"azure_recon_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                media_type="application/pdf"
            )
        else:  # Default to markdown
            filepath = await report_generator.generate_markdown_report(scan_data)
            return FileResponse(
                filepath,
                filename=f"azure_recon_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                media_type="text/markdown"
            )
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.get("/api/reports")
async def list_reports():
    """List all generated reports"""
    try:
        reports = await report_generator.list_reports()
        return reports
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@app.get("/api/diagnostics")
async def get_diagnostics():
    """Get diagnostic information about Azure access and permissions"""
    if not azure_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        diagnostics = {
            "tenant_id": azure_auth.tenant_id,
            "auth_method": azure_auth.auth_method,
        }
        
        # Test subscription access
        try:
            subscriptions = await azure_auth.get_subscriptions()
            diagnostics["subscriptions"] = {
                "count": len(subscriptions),
                "details": [{"id": sub.subscription_id, "name": sub.display_name, "state": sub.state} for sub in subscriptions]
            }
        except Exception as e:
            diagnostics["subscriptions"] = {"error": str(e)}
        
        # Test security center access
        try:
            from azure.mgmt.security import SecurityCenter
            subscription_ids = [sub.subscription_id for sub in subscriptions]
            if subscription_ids:
                security_client = SecurityCenter(
                    credential=azure_auth.credential,
                    subscription_id=subscription_ids[0]
                )
                # Try to get secure scores
                scores = list(security_client.secure_scores.list())
                diagnostics["security_center"] = {
                    "accessible": True,
                    "secure_scores_count": len(scores)
                }
                security_client.close()
        except Exception as e:
            diagnostics["security_center"] = {"accessible": False, "error": str(e)}
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Diagnostics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    try:
        await azure_auth.close()
        secure_score_analyzer.close_clients()
        exposure_analyzer.close_clients()
        identity_analyzer.close_clients()
        policy_analyzer.close_clients()
        role_analyzer.close_clients()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )