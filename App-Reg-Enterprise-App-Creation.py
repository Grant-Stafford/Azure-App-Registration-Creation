import msal
import requests
import json
import datetime
import time
import math
import yaml

# Load the YAML configuration file
with open("PATH\\TO\\variables-from-SNOW.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract variables from the YAML config
CREATOR = config["Creator"]
DATE = config["Date"]
TICKET = config["Ticket"]
CI = config["CI"]
BUSINESS_CONTACT = config["Business Contact"]
TECHNICAL_CONTACT = config["Technical Contact"]
VENDOR_CONTACT = config["Vendor Contact"]
LINK_TO_EDP = config["Link to EDP"]

APP_NAME = config["APP_NAME"]
GROUP_NAMES = config["GROUP_NAMES"]
REDIRECT_URI_TYPE = config["REDIRECT_URI_TYPE"]
REDIRECT_URI = config["REDIRECT_URI"]

# Azure AD Authentication Configuration
TENANT_ID = "<Your Tenant ID>"  # Replace with your actual tenant ID
CLIENT_ID = "<Your Client ID>"  # Required for MSAL authentication
CLIENT_SECRET = "<Your Secret ID>"  # Replace with your App Registration Client Secret
SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Authenticate with Microsoft Graph using Client Credentials
app = msal.ConfidentialClientApplication(
    CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}", client_credential=CLIENT_SECRET
)
token_response = app.acquire_token_for_client(scopes=SCOPES)

if "access_token" in token_response:
    access_token = token_response["access_token"]
    print("Authentication successful")
else:
    print("Authentication failed:", token_response)
    exit()

headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

################################################################################################

# Step 1: Create App Registration
app_data = {
    "displayName": APP_NAME,
    "signInAudience": "AzureADMyOrg"
}
app_create_response = requests.post(f"{GRAPH_API_ENDPOINT}/applications", headers=headers, json=app_data)
if app_create_response.status_code == 201:
    app_info = app_create_response.json()
    new_app_id = app_info["appId"]  # Use 'id' instead of 'appId' for updates
    print(f"App Registration created successfully: {app_info['displayName']} (App ID: {new_app_id})")

################################################################################################

    # Step 1.1: Wait for App Registration to be available before configuring Redirect URIs
    for attempt in range(7):  # Retry up to 7 times (exponential backoff)
        wait_time = math.pow(2, attempt)  # 1, 2, 4, 8, 16, 32 seconds delay
        verify_app_response = requests.get(f"{GRAPH_API_ENDPOINT}/applications?$filter=displayName eq '{APP_NAME}'", headers=headers)
        
        if verify_app_response.status_code == 200 and verify_app_response.json()["value"]:
            app = verify_app_response.json()["value"][0]
            print(f"Display Name: {app['displayName']}, Object ID: {app['id']}, Client ID: {app['appId']}")
            new_app_id = verify_app_response.json()["value"][0]["appId"]
            object_id = verify_app_response.json()["value"][0]["id"]  # Store Object ID for Redirect URI update
            print(f"App Registration is now available: {new_app_id}")
            break
        
        print(f"Waiting for App Registration to be available... Attempt {attempt + 1}/7 (waiting {int(wait_time)}s)")
        time.sleep(wait_time)
    else:
        print(f"ERROR: App Registration '{APP_NAME}' did not become available. Skipping Redirect URI setup.")
        # Stop the script if there's an error
        exit()

    # Step 1.2: Configure Redirect URIs
    if REDIRECT_URI_TYPE == "Other":
        print("Redirect URI either not needed or needs special configuration, contact ticket requestor")
    elif REDIRECT_URI_TYPE in ["Web", "Single-page application"]:
        platform_type = "web" if REDIRECT_URI_TYPE == "Web" else "spa"
        redirect_uri_data = {
            "web": {"web": {"redirectUris": [REDIRECT_URI]}} if platform_type == "web" else {},
            "spa": {"spa": {"redirectUris": [REDIRECT_URI]}} if platform_type == "spa" else {}
        }
        redirect_uri_response = requests.patch(
            f"{GRAPH_API_ENDPOINT}/applications/{object_id}", headers=headers, json=redirect_uri_data[platform_type]
        )
        if redirect_uri_response.status_code in [200, 204]:
            print(f"{REDIRECT_URI_TYPE} platform created with Redirect URI: {REDIRECT_URI}")
        else:
            print(f"ERROR: Failed to add Redirect URI for {REDIRECT_URI_TYPE}:", redirect_uri_response.status_code, redirect_uri_response.text)
else:
    print("Failed to create App Registration:", app_create_response.status_code, app_create_response.text)
    # Stop the script if there's an error
    exit()

################################################################################################

# Step 2.1: Ensure App Registration is Fully Available Before Creating Enterprise App
for attempt in range(7):  # Retry up to 7 times (exponential backoff)
    wait_time = math.pow(2, attempt)  # 1, 2, 4, 8, 16, 32 seconds delay
    verify_app_response = requests.get(f"{GRAPH_API_ENDPOINT}/applications?$filter=displayName eq '{APP_NAME}'", headers=headers)
    
    if verify_app_response.status_code == 200 and verify_app_response.json()["value"]:
        print("Retrieved application IDs:")
        for app in verify_app_response.json()["value"]:
            print(f"Display Name: {app['displayName']}, Object ID: {app['id']}, Client ID: {app['appId']}")

        # Update new_app_id with the correct Client ID (appId)
        new_app_id = verify_app_response.json()["value"][0]["appId"]
        print(f"Confirmed App Registration exists and is ready (Client ID): {new_app_id}")
        break
    
    print(f"Waiting for App Registration to be fully available before creating Enterprise App... Attempt {attempt + 1}/7 (waiting {int(wait_time)}s)")
    time.sleep(wait_time)
else:
    print(f"ERROR: App Registration '{APP_NAME}' did not become available. Skipping Enterprise App creation.")
    # Stop the script if there's an error
    exit()

# Step 2.2: Create Enterprise Application (Service Principal)
print("Creating Enterprise App (Service Principal)...")

sp_data = {"appId": new_app_id, "displayName": APP_NAME}
sp_create_response = requests.post(f"{GRAPH_API_ENDPOINT}/servicePrincipals", headers=headers, json=sp_data)

if sp_create_response.status_code == 201:
    ENTERPRISE_APP_ID = sp_create_response.json().get("id")
    print(f"Enterprise App (Service Principal) created successfully: {ENTERPRISE_APP_ID}")
else:
    print(f"ERROR: Failed to create Enterprise App: {sp_create_response.status_code} - {sp_create_response.text}")
    # Stop the script if there's an error
    exit()

################################################################################################

# Step 3: Assign AD Groups to the Enterprise App
for group_name in GROUP_NAMES:
    group_search_response = requests.get(f"{GRAPH_API_ENDPOINT}/groups?$filter=displayName eq '{group_name}'", headers=headers)
    if group_search_response.status_code == 200 and group_search_response.json()["value"]:
        group_id = group_search_response.json()["value"][0]["id"]
        print(f"Found group '{group_name}' (ID: {group_id}), assigning to Enterprise App...")
        
        # Assign the group to the Enterprise App
        group_assignment_data = {
            "principalId": group_id,
            "resourceId": ENTERPRISE_APP_ID
        }
        group_assignment_response = requests.post(f"{GRAPH_API_ENDPOINT}/servicePrincipals/{ENTERPRISE_APP_ID}/appRoleAssignments", headers=headers, json=group_assignment_data)
        
        if group_assignment_response.status_code == 201:
            print(f"Successfully assigned '{group_name}' to the Enterprise App.")
        else:
            print(f"ERROR: Failed to assign '{group_name}':", group_assignment_response.status_code, group_assignment_response.text)
    else:
        print(f"ERROR: Group '{group_name}' not found. Make sure the group exists.")
    # Stop the script if there's an error
    # exit()

################################################################################################

# Step 4: Add notes to the Enterprise App
print("Adding notes to the Enterprise App...")

# Prepare the notes section with variables from the YAML file
notes_content = f"""
Creator: {CREATOR}
Date: {DATE}
Ticket: {TICKET}
CI: {CI}
Business Contact: {BUSINESS_CONTACT}
Technical Contact: {TECHNICAL_CONTACT}
Vendor Contact: {VENDOR_CONTACT}
Link to EDP: {LINK_TO_EDP}
"""

# Verify the Service Principal exists
verify_sp_response = requests.get(
    f"{GRAPH_API_ENDPOINT}/servicePrincipals/{ENTERPRISE_APP_ID}",
    headers=headers
)

if verify_sp_response.status_code == 200:
    print("Service Principal exists:")#, verify_sp_response.json()) <uncomment to get all the properties created>
    
# Prepare the data to update the 'notes' property directly on the servicePrincipal object
notes_data = {
    "notes": notes_content  # Directly setting the 'notes' property
}

# Send PATCH request to update the app's notes section
update_notes_response = requests.patch(
    f"{GRAPH_API_ENDPOINT}/servicePrincipals/{ENTERPRISE_APP_ID}", headers=headers, json=notes_data
)

# Check if the update was successful
if update_notes_response.status_code == 204:
    print("Notes added successfully to the Enterprise App.")
else:
    print(f"ERROR: Failed to add notes to the Enterprise App: {update_notes_response.status_code} - {update_notes_response.text}")
    # Stop the script if there's an error
    exit()

print("Step 4 Completed: Notes updated successfully.")

################################################################################################

# Step 5: Set appRoleAssignmentRequired to Yes (true)
print("Setting 'appRoleAssignmentRequired' to Yes (true) on the Enterprise App...")

# Prepare the data to update the 'appRoleAssignmentRequired' field under 'properties'
assignment_required_data = {
    "appRoleAssignmentRequired": True  # Set this to True (Yes) as per your requirement
}

# Send PATCH request to update the 'appRoleAssignmentRequired' field
update_assignment_response = requests.patch(
    f"{GRAPH_API_ENDPOINT}/servicePrincipals/{ENTERPRISE_APP_ID}", headers=headers, json=assignment_required_data
)

# Check if the update was successful
if update_assignment_response.status_code == 204:
    print("Successfully set 'appRoleAssignmentRequired' to Yes (true) on the Enterprise App.")
else:
    print(f"ERROR: Failed to set 'appRoleAssignmentRequired' to Yes: {update_assignment_response.status_code} - {update_assignment_response.text}")
    # Stop the script if there's an error
    exit()

print("Step 5 Completed: 'appRoleAssignmentRequired' set to Yes successfully.")

################################################################################################

# Step 6: Add custom security attribute 'MFAEnabled' to the Enterprise App
print("Adding custom security attribute 'MFAEnabled' to the Enterprise App...")

# Prepare the custom security attribute 'MFAEnabled' under 'requireMFA' attribute set. note custom sec attribute must already be made in portal. this only applys it to the app
mfa_enabled_data = {
    "customSecurityAttributes": {
        "requireMFA": {
            "@odata.type": "#Microsoft.DirectoryServices.CustomSecurityAttributeValue",
            "MFAEnabled@odata.type": "#String", # Must be a string
            "MFAEnabled": "True"  # Set this to True or False based on your requirement
        }
    }
}

# Send PATCH request to update the custom security attribute 'MFAEnabled'
update_mfa_enabled_response = requests.patch(
    f"{GRAPH_API_ENDPOINT}/servicePrincipals/{ENTERPRISE_APP_ID}", headers=headers, json=mfa_enabled_data
)

# Check if the update was successful
if update_mfa_enabled_response.status_code == 204:
    print("Successfully added 'MFAEnabled' custom security attribute to the Enterprise App.")
else:
    print(f"ERROR: Failed to add 'MFAEnabled' custom security attribute: {update_mfa_enabled_response.status_code} - {update_mfa_enabled_response.text}")
    exit()

print("Step 6 Completed: 'MFAEnabled' custom security attribute added successfully.")

print("App is created, also Grant is kinda cool :)")
