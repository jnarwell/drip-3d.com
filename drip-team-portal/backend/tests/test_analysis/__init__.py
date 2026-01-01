"""
Analysis Dashboard Tests - TDD Test Suite

Tests for the Analysis Dashboard feature:
- CRUD operations for named model instances (analyses)
- WebSocket real-time updates
- Team-wide scope (all users see all analyses)

Architecture:
- Named analyses: component_id IS NULL AND name IS NOT NULL
- Real-time updates via WebSocket at /ws/analysis
- Endpoints: /api/v1/analyses/*

Run with: pytest backend/tests/test_analysis/ -v
"""
