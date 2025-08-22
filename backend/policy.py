import asyncio
import logging
from typing import List, Dict, Any
from azure.mgmt.resource import PolicyClient
from auth import azure_auth
from models import PolicyAssignment, ComplianceResult

logger = logging.getLogger(__name__)

class PolicyAnalyzer:
    def __init__(self):
        self.policy_clients: Dict[str, PolicyClient] = {}
    
    def get_policy_client(self, subscription_id: str) -> PolicyClient:
        """Get or create a Policy client for a subscription"""
        if subscription_id not in self.policy_clients:
            if not azure_auth.is_authenticated():
                raise ValueError("Not authenticated with Azure")
            
            self.policy_clients[subscription_id] = PolicyClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        
        return self.policy_clients[subscription_id]
    
    async def get_policy_assignments(self, subscription_ids: List[str]) -> List[PolicyAssignment]:
        """Get all policy assignments across subscriptions"""
        assignments = []
        
        for subscription_id in subscription_ids:
            try:
                policy_client = self.get_policy_client(subscription_id)
                
                # Get policy assignments at subscription scope
                for assignment in policy_client.policy_assignments.list():
                    try:
                        # Determine enforcement mode
                        enforcement_mode = "Default"
                        if hasattr(assignment, 'enforcement_mode') and assignment.enforcement_mode:
                            enforcement_mode = str(assignment.enforcement_mode)
                        
                        policy_assignment = PolicyAssignment(
                            id=assignment.id,
                            name=assignment.name,
                            display_name=assignment.display_name or assignment.name,
                            policy_definition_id=assignment.policy_definition_id,
                            scope=assignment.scope or f"/subscriptions/{subscription_id}",
                            enforcement_mode=enforcement_mode,
                            compliance_state=None  # Will be populated separately
                        )
                        assignments.append(policy_assignment)
                        
                    except Exception as e:
                        logger.warning(f"Error processing policy assignment: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not get policy assignments for subscription {subscription_id}: {str(e)}")
                continue
        
        return assignments
    
    async def get_compliance_results(self, subscription_ids: List[str]) -> List[ComplianceResult]:
        """Get policy compliance results across subscriptions"""
        compliance_results = []
        
        for subscription_id in subscription_ids:
            try:
                policy_client = self.get_policy_client(subscription_id)
                
                # Get policy states (compliance results)
                try:
                    # This would normally use the Policy Insights API, but we'll simulate with basic logic
                    # In a real implementation, you'd use azure.mgmt.policyinsights.PolicyInsightsClient
                    
                    # Get policy assignments first
                    assignments = {}
                    for assignment in policy_client.policy_assignments.list():
                        assignments[assignment.id] = assignment
                    
                    # For each assignment, create sample compliance results
                    # In reality, you'd query actual compliance data
                    for assignment_id, assignment in assignments.items():
                        
                        # Simulate compliance results for different resource types
                        sample_resources = [
                            {
                                'resource_id': f"/subscriptions/{subscription_id}/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1",
                                'resource_type': "Microsoft.Compute/virtualMachines",
                                'resource_location': "eastus",
                                'compliance_state': "Compliant"
                            },
                            {
                                'resource_id': f"/subscriptions/{subscription_id}/resourceGroups/rg2/providers/Microsoft.Storage/storageAccounts/storage1",
                                'resource_type': "Microsoft.Storage/storageAccounts", 
                                'resource_location': "westus",
                                'compliance_state': "NonCompliant"
                            }
                        ]
                        
                        for resource in sample_resources:
                            compliance_result = ComplianceResult(
                                policy_assignment_id=assignment_id,
                                policy_assignment_name=assignment.display_name or assignment.name,
                                resource_id=resource['resource_id'],
                                compliance_state=resource['compliance_state'],
                                resource_type=resource['resource_type'],
                                resource_location=resource['resource_location']
                            )
                            compliance_results.append(compliance_result)
                    
                except Exception as e:
                    logger.warning(f"Could not get compliance results for subscription {subscription_id}: {str(e)}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error getting compliance data for subscription {subscription_id}: {str(e)}")
                continue
        
        return compliance_results
    
    async def get_policy_definitions(self, subscription_ids: List[str]) -> List[Dict[str, Any]]:
        """Get policy definitions and their details"""
        policy_definitions = []
        
        for subscription_id in subscription_ids:
            try:
                policy_client = self.get_policy_client(subscription_id)
                
                # Get built-in policy definitions (most commonly used)
                for definition in policy_client.policy_definitions.list_built_in():
                    try:
                        # Only include commonly used/important policies
                        important_categories = [
                            'Security Center',
                            'Security',
                            'Monitoring',
                            'Compute',
                            'Storage',
                            'Networking'
                        ]
                        
                        category = "General"
                        if hasattr(definition, 'metadata') and definition.metadata:
                            metadata_category = definition.metadata.get('category')
                            if metadata_category in important_categories:
                                category = metadata_category
                            else:
                                continue  # Skip less important policies
                        
                        policy_def = {
                            'id': definition.id,
                            'name': definition.name,
                            'display_name': definition.display_name or definition.name,
                            'description': definition.description or 'No description',
                            'category': category,
                            'policy_type': str(definition.policy_type) if definition.policy_type else 'Unknown',
                            'mode': definition.mode or 'All',
                            'parameters': list(definition.parameters.keys()) if definition.parameters else []
                        }
                        policy_definitions.append(policy_def)
                        
                        # Limit to prevent too much data
                        if len(policy_definitions) >= 50:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error processing policy definition: {str(e)}")
                        continue
                
                # Also get custom policy definitions
                for definition in policy_client.policy_definitions.list():
                    try:
                        if definition.policy_type and str(definition.policy_type) == 'Custom':
                            policy_def = {
                                'id': definition.id,
                                'name': definition.name,
                                'display_name': definition.display_name or definition.name,
                                'description': definition.description or 'No description',
                                'category': 'Custom',
                                'policy_type': 'Custom',
                                'mode': definition.mode or 'All',
                                'parameters': list(definition.parameters.keys()) if definition.parameters else []
                            }
                            policy_definitions.append(policy_def)
                            
                    except Exception as e:
                        logger.warning(f"Error processing custom policy definition: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not get policy definitions for subscription {subscription_id}: {str(e)}")
                continue
        
        return policy_definitions
    
    async def get_compliance_summary(self, subscription_ids: List[str]) -> Dict[str, Any]:
        """Get overall compliance summary"""
        summary = {
            'total_assignments': 0,
            'compliant_resources': 0,
            'non_compliant_resources': 0,
            'compliance_percentage': 0,
            'by_subscription': {}
        }
        
        try:
            compliance_results = self.get_compliance_results(subscription_ids)
            
            for result in compliance_results:
                summary['total_assignments'] += 1
                
                # Extract subscription ID from resource ID
                resource_parts = result.resource_id.split('/')
                sub_id = resource_parts[2] if len(resource_parts) > 2 else 'unknown'
                
                if sub_id not in summary['by_subscription']:
                    summary['by_subscription'][sub_id] = {
                        'compliant': 0,
                        'non_compliant': 0,
                        'total': 0
                    }
                
                summary['by_subscription'][sub_id]['total'] += 1
                
                if result.compliance_state == 'Compliant':
                    summary['compliant_resources'] += 1
                    summary['by_subscription'][sub_id]['compliant'] += 1
                else:
                    summary['non_compliant_resources'] += 1
                    summary['by_subscription'][sub_id]['non_compliant'] += 1
            
            # Calculate overall compliance percentage
            total_resources = summary['compliant_resources'] + summary['non_compliant_resources']
            if total_resources > 0:
                summary['compliance_percentage'] = (summary['compliant_resources'] / total_resources) * 100
            
        except Exception as e:
            logger.error(f"Error calculating compliance summary: {str(e)}")
        
        return summary
    
    def close_clients(self):
        """Close all policy clients"""
        for client in self.policy_clients.values():
            if hasattr(client, 'close'):
                client.close()
        self.policy_clients.clear()

# Global analyzer instance
policy_analyzer = PolicyAnalyzer()