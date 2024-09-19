import requests
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# API Key for Azure Cognitive Search
api_key = "mDpfeDZCAUTQDfvgkqnSZIrjJAlWK3qwvxEFF8IcJ5AzSeC1sFjS"  

# Azure AD and Cognitive Search settings
search_service_name = "isearchservice"
search_index_name = "searchindex"
credential = DefaultAzureCredential()

# Azure Cognitive Search client
search_client = SearchClient(
    endpoint=f"https://{search_service_name}.search.windows.net/",
    index_name=search_index_name,
    credential=AzureKeyCredential(api_key)  # Using correct API key credential
)

# Microsoft Graph API endpoint
graph_api_endpoint = "https://graph.microsoft.com/v1.0"

# Function to get user's group membership from Microsoft Graph API
def get_user_groups(user_id):
    try:
        access_token = credential.get_token("https://graph.microsoft.com/.default").token
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{graph_api_endpoint}/users/{user_id}/memberOf"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            groups = response.json().get('value', [])
            return [g['displayName'] for g in groups]
        else:
            print(f"Error fetching groups for user {user_id}: {response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred while fetching user groups: {str(e)}")
        return []

# Function to determine user's access level based on group membership
def get_user_access_level(groups):
    if "Executive_Committee" in groups:
        return "L3"
    elif any(g.startswith("VP_") or g.startswith("Director_") for g in groups):
        return "L2"
    elif any(g.startswith("Manager_") for g in groups):
        return "L1"
    else:
        return "L0"

# Function to perform keyword search in Azure Cognitive Search
def perform_keyword_search(user_id, query_text):
    try:
        user_groups = get_user_groups(user_id)
        user_access_level = get_user_access_level(user_groups)

        print(f"User groups: {user_groups}")
        print(f"User access level: {user_access_level}")

        # Determine document access
        can_access_confidential = user_access_level in ["L3", "L2"] and "Finance_Forecasting_Team" in user_groups
        can_access_restricted = user_access_level in ["L3", "L2", "L1"] and any(g.startswith("Finance_") for g in user_groups)

        # Construct filter
        filter_conditions = []
        if can_access_confidential:
            filter_conditions.append("classification eq 'Confidential'")
        if can_access_restricted:
            filter_conditions.append("classification eq 'Restricted'")
        filter_conditions.append("classification eq 'Internal'")
        filter_conditions.append("classification eq 'Public'")

        # Add specific group access
        group_access = " or ".join([f"specific_access_groups/any(g: g eq '{group}')" for group in user_groups])
        filter_conditions.append(f"({group_access})")

        # Construct filter string
        filter_string = " or ".join(filter_conditions)
        print(f"Filter string: {filter_string}")

        # Perform the keyword search
        results = search_client.search(
            search_text=query_text,
            filter=filter_string,
            select="id,title,content,classification,department,specific_access_groups"
        )

        return results

    except Exception as e:
        print(f"An error occurred during search: {str(e)}")
        return []

# Usage
user_id = "finance.manager@jyotirdas845gmail.onmicrosoft.com"
query_text = "annual revenue"

# Perform the keyword search and print results
results = perform_keyword_search(user_id, query_text)

if not results:
    print("No results returned.")
else:
    try:
        for result in results:
            print(f"ID: {result['id']}, Title: {result['title']}, Classification: {result['classification']}")
    except Exception as e:
        print(f"An error occurred while iterating over results: {str(e)}")
