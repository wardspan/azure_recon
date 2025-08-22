import os

from azure.core.exceptions import HttpResponseError
from azure.identity import DeviceCodeCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.security import SecurityCenter


def get_credential():
    return DeviceCodeCredential(
        client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        tenant_id=os.getenv("AZURE_TENANT_ID")
    )

def get_all_subscriptions(credential):
    sub_client = SubscriptionClient(credential)
    return [sub.subscription_id for sub in sub_client.subscriptions.list()]

def check_role_assignments(credential, subscription_id):
    try:
        auth_client = AuthorizationManagementClient(credential, subscription_id)
        scope = f"/subscriptions/{subscription_id}"
        assignments = list(auth_client.role_assignments.list_for_scope(scope))
        return [{"principal_id": a.principal_id, "role_id": a.role_definition_id} for a in assignments]
    except HttpResponseError as e:
        return f"❌ Cannot retrieve role assignments: {str(e)}"

def check_resource_access(credential, subscription_id):
    try:
        resource_client = ResourceManagementClient(credential, subscription_id)
        resources = list(resource_client.resources.list())
        return len(resources)
    except HttpResponseError as e:
        return f"❌ Cannot list resources: {str(e)}"

def check_secure_score(credential, subscription_id):
    try:
        sec_client = SecurityCenter(credential, subscription_id)
        scores = list(sec_client.secure_scores.list())
        return len(scores)
    except HttpResponseError as e:
        return f"❌ Cannot access Secure Score: {str(e)}"
    except AttributeError as e:
        return f"❌ Secure Score API not available: {str(e)}"

def run_permission_debug():
    credential = get_credential()
    subs = get_all_subscriptions(credential)
    debug_summary = {}

    for sub_id in subs:
        print(f"\n🔍 Debugging permissions for Subscription: {sub_id}")
        debug_summary[sub_id] = {}

        roles = check_role_assignments(credential, sub_id)
        print(f"🔑 Role Assignments: {roles if isinstance(roles, str) else len(roles)} entries")
        debug_summary[sub_id]["role_assignments"] = roles

        res = check_resource_access(credential, sub_id)
        print(f"📦 Resource visibility: {res}")
        debug_summary[sub_id]["resources"] = res

        score = check_secure_score(credential, sub_id)
        print(f"🛡️ Secure Score access: {score}")
        debug_summary[sub_id]["secure_score"] = score

    return debug_summary

if __name__ == "__main__":
    print("🔧 Running Azure permission debug...\n")
    results = run_permission_debug()

    print("\n📋 Final Summary:")
    for sub_id, data in results.items():
        print(f"\n📌 Subscription: {sub_id}")
        for section, result in data.items():
            print(f"  - {section}: {result}")