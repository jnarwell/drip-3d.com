from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

class LinearService:
    def __init__(self, api_key: str):
        transport = AIOHTTPTransport(
            url="https://api.linear.app/graphql",
            headers={"Authorization": api_key}
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.team_id = None  # Will be set from config
        self.project_id = None  # Will be set from config
    
    async def create_test_issue(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Linear issue for test result"""
        mutation = gql("""
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                        url
                    }
                }
            }
        """)
        
        # Map test result to Linear priority
        priority_map = {
            "FAIL": 1,  # Urgent
            "PARTIAL": 2,  # High
            "PASS": 3  # Normal
        }
        
        variables = {
            "input": {
                "title": f"Test {test_data['test_id']}: {test_data['name']}",
                "description": self._format_test_description(test_data),
                "teamId": self.team_id,
                "projectId": self.project_id,
                "priority": priority_map.get(test_data.get('result', 'PASS'), 3),
                "labelIds": self._get_label_ids(test_data),
            }
        }
        
        result = await self.client.execute_async(mutation, variable_values=variables)
        return result['issueCreate']['issue']
    
    async def update_test_issue(self, issue_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Linear issue"""
        mutation = gql("""
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
            }
        """)
        
        variables = {
            "id": issue_id,
            "input": update_data
        }
        
        result = await self.client.execute_async(mutation, variable_values=variables)
        return result['issueUpdate']['issue']
    
    async def sync_test_results(self, last_sync_time: datetime) -> List[Dict[str, Any]]:
        """Pull test results from Linear"""
        query = gql("""
            query GetTestIssues($filter: IssueFilter!) {
                issues(filter: $filter) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        state {
                            name
                            type
                        }
                        priority
                        labels {
                            nodes {
                                name
                            }
                        }
                        customFieldValues
                        comments {
                            nodes {
                                body
                                createdAt
                                user {
                                    email
                                    name
                                }
                            }
                        }
                        updatedAt
                    }
                }
            }
        """)
        
        variables = {
            "filter": {
                "team": {"id": {"eq": self.team_id}},
                "project": {"id": {"eq": self.project_id}},
                "labels": {
                    "name": {"in": ["DRIP-TEST", "STEERING-RESULTS", "BONDING-RESULTS", "THERMAL-TEST"]}
                },
                "updatedAt": {"gte": last_sync_time.isoformat()}
            }
        }
        
        results = await self.client.execute_async(query, variable_values=variables)
        return self._process_linear_results(results['issues']['nodes'])
    
    async def create_component_issue(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Linear issue for component tracking"""
        mutation = gql("""
            mutation CreateComponentIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        url
                    }
                }
            }
        """)
        
        variables = {
            "input": {
                "title": f"Component: {component_data['name']} ({component_data['component_id']})",
                "description": self._format_component_description(component_data),
                "teamId": self.team_id,
                "projectId": self.project_id,
                "priority": 3,  # Normal priority for components
                "labelIds": self._get_component_label_ids(component_data),
            }
        }
        
        result = await self.client.execute_async(mutation, variable_values=variables)
        return result['issueCreate']['issue']
    
    def _format_test_description(self, test_data: Dict[str, Any]) -> str:
        """Format test data into Linear issue description"""
        description_parts = [
            f"## Test Information",
            f"- **Test ID**: {test_data['test_id']}",
            f"- **Category**: {test_data.get('category', 'N/A')}",
            f"- **Result**: {test_data.get('result', 'PENDING')}",
            f"- **Engineer**: {test_data.get('engineer', 'N/A')}",
            f"- **Date**: {test_data.get('executed_date', datetime.utcnow()).strftime('%Y-%m-%d')}",
            "",
            f"## Test Results",
        ]
        
        # Add specific test results based on category
        if test_data.get('steering_force'):
            description_parts.append(f"- **Steering Force**: {test_data['steering_force']} μN")
        if test_data.get('bonding_strength'):
            description_parts.append(f"- **Bonding Strength**: {test_data['bonding_strength']} MPa")
        if test_data.get('temperature_max'):
            description_parts.append(f"- **Max Temperature**: {test_data['temperature_max']} °C")
        if test_data.get('drip_number'):
            description_parts.append(f"- **DRIP Number**: {test_data['drip_number']:.3f}")
        
        if test_data.get('notes'):
            description_parts.extend([
                "",
                "## Notes",
                test_data['notes']
            ])
        
        return "\n".join(description_parts)
    
    def _format_component_description(self, component_data: Dict[str, Any]) -> str:
        """Format component data into Linear issue description"""
        description_parts = [
            f"## Component Details",
            f"- **Component ID**: {component_data['component_id']}",
            f"- **Part Number**: {component_data.get('part_number', 'N/A')}",
            f"- **Category**: {component_data['category']}",
            f"- **Status**: {component_data['status']}",
            f"- **Supplier**: {component_data.get('supplier', 'N/A')}",
            "",
        ]
        
        if component_data.get('tech_specs'):
            description_parts.extend([
                "## Technical Specifications",
                "```json",
                json.dumps(component_data['tech_specs'], indent=2),
                "```",
                ""
            ])
        
        if component_data.get('notes'):
            description_parts.extend([
                "## Notes",
                component_data['notes']
            ])
        
        return "\n".join(description_parts)
    
    def _get_label_ids(self, test_data: Dict[str, Any]) -> List[str]:
        """Get Linear label IDs based on test data"""
        # This would be configured based on actual Linear workspace
        # For now, returning empty list
        return []
    
    def _get_component_label_ids(self, component_data: Dict[str, Any]) -> List[str]:
        """Get Linear label IDs for components"""
        # This would be configured based on actual Linear workspace
        return []
    
    def _process_linear_results(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Linear issues into test results format"""
        processed_results = []
        
        for issue in issues:
            # Extract test ID from title or description
            test_id = self._extract_test_id(issue)
            if not test_id:
                continue
            
            # Map Linear state to test status
            status_map = {
                "Todo": "NOT_STARTED",
                "In Progress": "IN_PROGRESS",
                "Done": "COMPLETED",
                "Canceled": "BLOCKED"
            }
            
            result = {
                "test_id": test_id,
                "linear_issue_id": issue["id"],
                "linear_identifier": issue["identifier"],
                "status": status_map.get(issue["state"]["name"], "NOT_STARTED"),
                "updated_at": issue["updatedAt"],
                "comments": [
                    {
                        "body": comment["body"],
                        "author": comment["user"]["name"],
                        "created_at": comment["createdAt"]
                    }
                    for comment in issue["comments"]["nodes"]
                ]
            }
            
            # Extract custom field values if available
            if issue.get("customFieldValues"):
                for field_value in issue["customFieldValues"]:
                    # Map custom fields to our data model
                    pass
            
            processed_results.append(result)
        
        return processed_results
    
    def _extract_test_id(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract test ID from Linear issue"""
        import re
        
        # Try to extract from title first
        title = issue.get("title", "")
        match = re.search(r'Test\s+([A-Z]{2}-\d{3})', title)
        if match:
            return match.group(1)
        
        # Try description
        description = issue.get("description", "")
        match = re.search(r'\*\*Test ID\*\*:\s*([A-Z]{2}-\d{3})', description)
        if match:
            return match.group(1)
        
        return None