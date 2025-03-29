# Azure-App-Registration-Creation
This automated the process of making an Azure app registration via Python.


# App Registration Automation Script

## Overview

This Python script automates the process of creating and configuring an Azure Active Directory (Azure AD) App Registration and its associated Enterprise Application (Service Principal). It uses the Microsoft Graph API to perform various operations, such as creating the app, assigning groups, setting permissions, and adding custom attributes.

## Features

1. **App Registration Creation**:
   - Creates an Azure AD App Registration with the specified display name.
   - Configures redirect URIs based on the type (Web or Single-page Application).

2. **Enterprise Application Creation**:
   - Creates a Service Principal (Enterprise Application) for the App Registration.

3. **Group Assignment**:
   - Assigns specified Azure AD groups to the Enterprise Application.

4. **Notes Addition**:
   - Adds metadata (e.g., creator, ticket number, business contact) as notes to the Enterprise Application.

5. **Role Assignment Requirement**:
   - Sets the `appRoleAssignmentRequired` property to `true` for the Enterprise Application.

6. **Custom Security Attribute**:
   - Adds a custom security attribute (`MFAEnabled`) to the Enterprise Application.

## Script Steps

1. **Authentication**:
   - Authenticates with Azure AD using the Microsoft Authentication Library (MSAL) and retrieves an access token.

2. **App Registration**:
   - Creates an App Registration and waits for it to become available.

3. **Redirect URI Configuration**:
   - Configures the redirect URI based on the specified type.

4. **Enterprise Application**:
   - Creates a Service Principal for the App Registration.

5. **Group Assignment**:
   - Searches for the specified groups and assigns them to the Enterprise Application.

6. **Notes and Attributes**:
   - Adds metadata as notes and sets custom security attributes (`MFAEnabled`).

7. **Role Assignment Requirement**:
   - Ensures that role assignments are required for the Enterprise Application.

8. **Custom Security Attribute**:
   - Adds a custom security attribute (`MFAEnabled`) to the Enterprise Application.

## Usage

1. Update the `variables-from-SNOW.yaml` file with the required configuration details.
2. Run the script using Python:
   ```bash
   App-Reg.py
   ```
3. Monitor the console output for progress and error messages.

## Notes

- Replace sensitive values like `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` with your actual Azure AD credentials.
- Ensure the account running the script has sufficient permissions to manage Azure AD resources.

## Disclaimer

This script is provided as-is and should be tested in a development environment before use in production. Ensure compliance with your organization's security and governance policies.
