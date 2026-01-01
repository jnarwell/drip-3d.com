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
    """Test fetching a single issue by identifier using issue(id:) query."""
    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not set")
        return None

    # Linear's issue(id:) accepts both UUIDs AND human-readable identifiers like "SYS-15"
    query = f"""
        query {{
            issue(id: "{identifier}") {{
                id
                identifier
                title
                project {{
                    id
                    name
                }}
            }}
        }}
    """

    print(f"\n📤 Direct issue(id:) Query for '{identifier}':")
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

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        import json
        print(json.dumps(data, indent=2))

        issue = data.get("data", {}).get("issue")
        if issue:
            project = issue.get("project")
            project_name = project.get("name") if project else "No Project"
            print(f"\n✅ Found: {issue['identifier']} - {issue.get('title', 'N/A')}")
            print(f"   Project: {project_name}")
            if not project:
                print("   ⚠️  Issue has NO PROJECT assigned in Linear!")
        else:
            print(f"\n❌ Issue not found: {identifier}")

        return data
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_aliased_query(identifiers: list):
    """Test the aliased query method (used in /summary/by-project)."""
    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not set")
        return None

    alias_queries = []
    for i, identifier in enumerate(identifiers):
        alias = f"issue_{i}"
        alias_queries.append(f'{alias}: issue(id: "{identifier}") {{ identifier project {{ id name }} }}')

    query = "query { " + " ".join(alias_queries) + " }"

    print(f"\n📤 Aliased Query (same as /summary/by-project):")
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

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        import json
        print(json.dumps(data, indent=2))

        response_data = data.get("data", {})
        print(f"\n📊 Results:")
        for key, issue in response_data.items():
            if issue:
                project = issue.get("project")
                project_name = project.get("name") if project else "No Project"
                print(f"  ✅ {issue['identifier']} -> {project_name}")
                if not project:
                    print(f"     ⚠️  This issue has NO PROJECT in Linear!")
            else:
                print(f"  ❌ {key}: Issue not found")

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

    # Test 1: Query by identifier filter (OLD method - may not work)
    print("\n" + "=" * 40)
    print("TEST 1: Query by identifier filter (OLD)")
    print("=" * 40)
    test_identifier_query(test_identifiers)

    # Test 2: Direct issue(id:) query (NEW method)
    print("\n" + "=" * 40)
    print("TEST 2: Direct issue(id:) query (NEW)")
    print("=" * 40)
    test_single_issue(test_identifiers[0])

    # Test 3: Aliased query (used in /summary/by-project)
    print("\n" + "=" * 40)
    print("TEST 3: Aliased query (production method)")
    print("=" * 40)
    test_aliased_query(test_identifiers)
