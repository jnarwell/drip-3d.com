#!/usr/bin/env python3
"""
Test script to debug Linear API project query.

Run with:
  LINEAR_API_KEY=lin_api_xxx python3 scripts/test_linear_project_query.py

Or set the LINEAR_API_KEY in your environment first.
"""

import os
import sys
import httpx

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_API_URL = "https://api.linear.app/graphql"


def test_identifier_query(identifiers: list):
    """Test querying issues by identifier."""
    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not set")
        return None

    identifiers_str = ", ".join(f'"{id}"' for id in identifiers)
    query = f"""
        query {{
            issues(filter: {{ identifier: {{ in: [{identifiers_str}] }} }}) {{
                nodes {{
                    id
                    identifier
                    title
                    project {{
                        id
                        name
                    }}
                }}
            }}
        }}
    """

    print(f"\n📤 GraphQL Query:")
    print(query)

    response = httpx.post(
        LINEAR_API_URL,
        json={"query": query},
        headers={
            "Content-Type": "application/json",
            "Authorization": LINEAR_API_KEY
        },
        timeout=30.0
    )

    print(f"\n📥 Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Response data:")
        import json
        print(json.dumps(data, indent=2))

        # Parse issues
        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
        print(f"\n📊 Found {len(issues)} issues:")
        for issue in issues:
            project = issue.get("project")
            project_name = project.get("name") if project else "No Project"
            print(f"  - {issue['identifier']}: {issue.get('title', 'N/A')}")
            print(f"    Project: {project_name}")

        return issues
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_single_issue(identifier: str):
    """Test fetching a single issue by identifier."""
    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not set")
        return None

    # Try using the issue() query with identifier
    query = f"""
        query {{
            issueVcsBranchSearch(branchName: "{identifier}") {{
                id
                identifier
                title
            }}
        }}
    """

    # Actually, let's try the issues search
    query = f"""
        query {{
            searchIssues(query: "{identifier}", first: 5) {{
                nodes {{
                    id
                    identifier
                    title
                    project {{
                        id
                        name
                    }}
                }}
            }}
        }}
    """

    print(f"\n📤 Search Query for '{identifier}':")

    response = httpx.post(
        LINEAR_API_URL,
        json={"query": query},
        headers={
            "Content-Type": "application/json",
            "Authorization": LINEAR_API_KEY
        },
        timeout=30.0
    )

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        import json
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Linear API Project Query Debug Script")
    print("=" * 60)

    if not LINEAR_API_KEY:
        print("\n❌ ERROR: LINEAR_API_KEY environment variable not set")
        print("   Run with: LINEAR_API_KEY=lin_api_xxx python3 scripts/test_linear_project_query.py")
        sys.exit(1)

    print(f"\n✅ LINEAR_API_KEY is set (length: {len(LINEAR_API_KEY)})")

    # Test identifiers - add any you want to test
    test_identifiers = ["SYS-15"]

    # Allow command line override
    if len(sys.argv) > 1:
        test_identifiers = sys.argv[1:]

    print(f"\n🔍 Testing identifiers: {test_identifiers}")

    # Test 1: Query by identifier filter
    print("\n" + "=" * 40)
    print("TEST 1: Query by identifier filter")
    print("=" * 40)
    test_identifier_query(test_identifiers)

    # Test 2: Search for the issue
    print("\n" + "=" * 40)
    print("TEST 2: Search for issue")
    print("=" * 40)
    test_single_issue(test_identifiers[0])
