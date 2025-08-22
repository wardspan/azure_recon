import asyncio
import logging
from typing import List, Dict, Any
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from auth import azure_auth
from models import PublicResource, NetworkSecurityGroup

logger = logging.getLogger(__name__)

class ExposureAnalyzer:
    def __init__(self):
        self.network_clients: Dict[str, NetworkManagementClient] = {}
        self.resource_clients: Dict[str, ResourceManagementClient] = {}
    
    def get_network_client(self, subscription_id: str) -> NetworkManagementClient:
        """Get or create a Network Management client for a subscription"""
        if subscription_id not in self.network_clients:
            if not azure_auth.is_authenticated():
                raise ValueError("Not authenticated with Azure")
            
            self.network_clients[subscription_id] = NetworkManagementClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        
        return self.network_clients[subscription_id]
    
    def get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create a Resource Management client for a subscription"""
        if subscription_id not in self.resource_clients:
            if not azure_auth.is_authenticated():
                raise ValueError("Not authenticated with Azure")
            
            self.resource_clients[subscription_id] = ResourceManagementClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        
        return self.resource_clients[subscription_id]
    
    async def get_public_resources(self, subscription_ids: List[str]) -> List[PublicResource]:
        """Find all resources with public IP addresses"""
        public_resources = []
        
        for subscription_id in subscription_ids:
            try:
                network_client = self.get_network_client(subscription_id)
                resource_client = self.get_resource_client(subscription_id)
                
                # Get all public IP addresses
                public_ips = {}
                for pip in network_client.public_ip_addresses.list_all():
                    if pip.ip_address:
                        public_ips[pip.id] = {
                            'ip': pip.ip_address,
                            'name': pip.name,
                            'location': pip.location,
                            'resource_group': pip.id.split('/')[4] if len(pip.id.split('/')) > 4 else 'unknown'
                        }
                
                # Get network interfaces and their associations
                for nic in network_client.network_interfaces.list_all():
                    if nic.ip_configurations:
                        for ip_config in nic.ip_configurations:
                            if ip_config.public_ip_address and ip_config.public_ip_address.id in public_ips:
                                pip_info = public_ips[ip_config.public_ip_address.id]
                                
                                # Try to find associated VM or resource
                                resource_name = nic.name
                                resource_type = "NetworkInterface"
                                
                                # Check if NIC is attached to a VM
                                if nic.virtual_machine:
                                    vm_id = nic.virtual_machine.id
                                    vm_name = vm_id.split('/')[-1] if vm_id else "Unknown VM"
                                    resource_name = vm_name
                                    resource_type = "VirtualMachine"
                                
                                public_resource = PublicResource(
                                    resource_id=nic.virtual_machine.id if nic.virtual_machine else nic.id,
                                    resource_name=resource_name,
                                    resource_type=resource_type,
                                    public_ip=pip_info['ip'],
                                    ports=[],  # Will be populated from NSG analysis
                                    protocols=[],  # Will be populated from NSG analysis
                                    subscription_id=subscription_id,
                                    resource_group=pip_info['resource_group']
                                )
                                public_resources.append(public_resource)
                
                # Check for Load Balancers with public IPs
                for lb in network_client.load_balancers.list_all():
                    if lb.frontend_ip_configurations:
                        for frontend_config in lb.frontend_ip_configurations:
                            if frontend_config.public_ip_address and frontend_config.public_ip_address.id in public_ips:
                                pip_info = public_ips[frontend_config.public_ip_address.id]
                                
                                ports = []
                                protocols = []
                                if lb.load_balancing_rules:
                                    for rule in lb.load_balancing_rules:
                                        if rule.frontend_port:
                                            ports.append(rule.frontend_port)
                                        if rule.protocol:
                                            protocols.append(str(rule.protocol))
                                
                                public_resource = PublicResource(
                                    resource_id=lb.id,
                                    resource_name=lb.name,
                                    resource_type="LoadBalancer",
                                    public_ip=pip_info['ip'],
                                    ports=list(set(ports)),
                                    protocols=list(set(protocols)),
                                    subscription_id=subscription_id,
                                    resource_group=pip_info['resource_group']
                                )
                                public_resources.append(public_resource)
                
                # Check Application Gateways
                for ag in network_client.application_gateways.list_all():
                    if ag.frontend_ip_configurations:
                        for frontend_config in ag.frontend_ip_configurations:
                            if frontend_config.public_ip_address and frontend_config.public_ip_address.id in public_ips:
                                pip_info = public_ips[frontend_config.public_ip_address.id]
                                
                                ports = []
                                protocols = []
                                if ag.frontend_ports:
                                    ports = [fp.port for fp in ag.frontend_ports if fp.port]
                                if ag.http_listeners:
                                    protocols = list(set([str(hl.protocol) for hl in ag.http_listeners if hl.protocol]))
                                
                                public_resource = PublicResource(
                                    resource_id=ag.id,
                                    resource_name=ag.name,
                                    resource_type="ApplicationGateway",
                                    public_ip=pip_info['ip'],
                                    ports=ports,
                                    protocols=protocols,
                                    subscription_id=subscription_id,
                                    resource_group=pip_info['resource_group']
                                )
                                public_resources.append(public_resource)
                                
            except Exception as e:
                logger.warning(f"Could not analyze public resources for subscription {subscription_id}: {str(e)}")
                continue
        
        return public_resources
    
    async def get_network_security_groups(self, subscription_ids: List[str]) -> List[NetworkSecurityGroup]:
        """Analyze Network Security Groups for security risks"""
        nsgs = []
        
        for subscription_id in subscription_ids:
            try:
                network_client = self.get_network_client(subscription_id)
                
                for nsg in network_client.network_security_groups.list_all():
                    rules = []
                    risky_rules = []
                    risk_reasons = []
                    risk_level = "Low"
                    
                    # Define dangerous ports with descriptions
                    dangerous_ports = {
                        '22': 'SSH',
                        '3389': 'RDP',
                        '1433': 'SQL Server',
                        '3306': 'MySQL',
                        '5432': 'PostgreSQL',
                        '6379': 'Redis',
                        '27017': 'MongoDB',
                        '5985': 'WinRM HTTP',
                        '5986': 'WinRM HTTPS',
                        '135': 'RPC Endpoint Mapper',
                        '445': 'SMB'
                    }
                    
                    # Analyze security rules
                    if nsg.security_rules:
                        for rule in nsg.security_rules:
                            rule_dict = {
                                'name': rule.name,
                                'priority': rule.priority,
                                'direction': str(rule.direction) if rule.direction else 'Unknown',
                                'access': str(rule.access) if rule.access else 'Unknown',
                                'protocol': str(rule.protocol) if rule.protocol else 'Any',
                                'source_port_range': rule.source_port_range or 'Any',
                                'destination_port_range': rule.destination_port_range or 'Any',
                                'source_address_prefix': rule.source_address_prefix or 'Any',
                                'destination_address_prefix': rule.destination_address_prefix or 'Any'
                            }
                            rules.append(rule_dict)
                            
                            # Risk assessment
                            if (str(rule.access) == 'Allow' and 
                                str(rule.direction) == 'Inbound' and 
                                rule.source_address_prefix in ['*', '0.0.0.0/0', 'Internet']):
                                
                                dest_port = rule.destination_port_range or ''
                                rule_reasons = []
                                
                                # Check for dangerous ports
                                for port, service in dangerous_ports.items():
                                    if port in dest_port:
                                        rule_reasons.append(f"Allows {service} ({port}) from Internet")
                                        risk_level = "High"
                                        risky_rules.append(rule_dict)
                                        break
                                
                                # Check for wildcard ports
                                if dest_port == '*' or dest_port == '0-65535':
                                    rule_reasons.append("Allows ALL ports from Internet")
                                    risk_level = "High"
                                    risky_rules.append(rule_dict)
                                
                                # Check for broad port ranges
                                elif '-' in dest_port:
                                    try:
                                        start, end = dest_port.split('-')
                                        if int(end) - int(start) > 100:
                                            rule_reasons.append(f"Allows broad port range ({dest_port}) from Internet")
                                            if risk_level != "High":
                                                risk_level = "Medium"
                                            risky_rules.append(rule_dict)
                                    except:
                                        pass
                                
                                # Any internet-facing rule that isn't explicitly dangerous
                                if not rule_reasons and risk_level == "Low":
                                    rule_reasons.append(f"Allows port {dest_port} from Internet")
                                    risk_level = "Medium"
                                    risky_rules.append(rule_dict)
                                
                                risk_reasons.extend(rule_reasons)
                    
                    nsg_model = NetworkSecurityGroup(
                        id=nsg.id,
                        name=nsg.name,
                        location=nsg.location,
                        resource_group=nsg.id.split('/')[4] if len(nsg.id.split('/')) > 4 else 'unknown',
                        subscription_id=subscription_id,
                        rules=rules,
                        risk_level=risk_level,
                        risky_rules=risky_rules,
                        risk_reasons=list(set(risk_reasons))  # Remove duplicates
                    )
                    nsgs.append(nsg_model)
                    
            except Exception as e:
                logger.warning(f"Could not analyze NSGs for subscription {subscription_id}: {str(e)}")
                continue
        
        return nsgs
    
    def close_clients(self):
        """Close all network and resource clients"""
        for client in self.network_clients.values():
            if hasattr(client, 'close'):
                client.close()
        for client in self.resource_clients.values():
            if hasattr(client, 'close'):
                client.close()
        self.network_clients.clear()
        self.resource_clients.clear()

# Global analyzer instance
exposure_analyzer = ExposureAnalyzer()