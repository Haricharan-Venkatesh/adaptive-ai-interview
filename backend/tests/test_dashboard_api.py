from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db import neo4j_client
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_neo4j_state():
    """Reset global driver state before and after each test."""
    neo4j_client._driver = None
    yield
    neo4j_client._driver = None


def test_get_codemap_uninitialized_fallback():
    """Test API behavior when Neo4j driver is uninitialized (returns 200 with fallback map)."""
    response = client.get("/api/v1/dashboard/codemap")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["nodes"]) >= 5
    assert len(data["links"]) >= 4
    assert "uninitialized" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_codemap_success_with_neo4j_records():
    """Test API behavior when Neo4j returns real concept nodes and relationships."""
    mock_driver = AsyncMock()
    mock_records = [
        {
            "n": {"id": "trees", "name": "Trees", "group": "Data Structures", "val": 15.0},
            "r": {"type": "DEPENDS_ON", "weight": 1.0},
            "m": {"id": "graphs", "name": "Graphs", "group": "Data Structures", "val": 15.0}
        }
    ]

    neo4j_client._driver = mock_driver

    with patch("app.db.neo4j_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_records
        
        response = client.get("/api/v1/dashboard/codemap")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["count_nodes"] == 2
        assert data["count_links"] == 1
        
        node_ids = [n["id"] for n in data["nodes"]]
        assert "trees" in node_ids
        assert "graphs" in node_ids
        assert data["links"][0]["source"] == "trees"
        assert data["links"][0]["target"] == "graphs"


@pytest.mark.asyncio
async def test_get_codemap_empty_neo4j_graph():
    """Test API behavior when Neo4j graph exists but returns 0 records."""
    mock_driver = AsyncMock()
    neo4j_client._driver = mock_driver

    with patch("app.db.neo4j_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []
        
        response = client.get("/api/v1/dashboard/codemap")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "empty"
        assert len(data["nodes"]) >= 5


@pytest.mark.asyncio
async def test_get_codemap_neo4j_query_exception():
    """Test API exception handling when Neo4j query fails with RuntimeError/DatabaseError."""
    mock_driver = AsyncMock()
    neo4j_client._driver = mock_driver

    with patch("app.db.neo4j_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = Exception("Neo4j database connection lost")
        
        response = client.get("/api/v1/dashboard/codemap")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "error"
        assert "connection lost" in data["message"].lower()
        assert len(data["nodes"]) > 0
