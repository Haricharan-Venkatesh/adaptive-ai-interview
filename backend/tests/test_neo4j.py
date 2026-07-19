import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.db import neo4j_client
from app.models.health import ServiceStatus


@pytest.fixture(autouse=True)
def reset_neo4j_driver():
    """Reset the global driver state before and after each test."""
    neo4j_client._driver = None
    yield
    neo4j_client._driver = None


@pytest.mark.asyncio
async def test_init_and_close_neo4j():
    with patch("app.db.neo4j_client.AsyncGraphDatabase.driver") as mock_driver_func:
        mock_driver = AsyncMock()
        mock_driver_func.return_value = mock_driver

        assert not neo4j_client.is_neo4j_initialized()

        await neo4j_client.init_neo4j()
        
        assert neo4j_client.is_neo4j_initialized()
        mock_driver.verify_connectivity.assert_called_once()

        await neo4j_client.close_neo4j()
        
        assert not neo4j_client.is_neo4j_initialized()
        mock_driver.close.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_uninitialized():
    status = await neo4j_client.check_neo4j_health()
    assert status.status == "down"
    assert "not initialized" in status.message


@pytest.mark.asyncio
async def test_health_check_healthy():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    
    mock_result.single.return_value = {"n": 1}
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    neo4j_client._driver = mock_driver

    status = await neo4j_client.check_neo4j_health()
    assert status.status == "ok"
    assert "responding" in status.message


@pytest.mark.asyncio
async def test_health_check_unhealthy_response():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    
    mock_result.single.return_value = {"n": 2} # Not 1
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    neo4j_client._driver = mock_driver

    status = await neo4j_client.check_neo4j_health()
    assert status.status == "down"
    assert "unexpected response" in status.message


@pytest.mark.asyncio
async def test_health_check_exception():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    
    mock_session.run.side_effect = Exception("Connection refused")
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    neo4j_client._driver = mock_driver

    status = await neo4j_client.check_neo4j_health()
    assert status.status == "down"
    assert "Connection refused" in status.message


@pytest.mark.asyncio
async def test_execute_query_success():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    
    expected_data = [{"id": 1, "name": "Test"}]
    mock_result.data.return_value = expected_data
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    neo4j_client._driver = mock_driver

    query = "MATCH (n) RETURN n"
    params = {"name": "Test"}
    
    result = await neo4j_client.execute_query(query, params)
    
    assert result == expected_data
    mock_session.run.assert_called_once_with(query, params)


@pytest.mark.asyncio
async def test_execute_query_uninitialized():
    with pytest.raises(RuntimeError, match="not initialized"):
        await neo4j_client.execute_query("MATCH (n) RETURN n")
