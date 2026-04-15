"""Agent execution endpoint tests."""
import pytest
import time

class TestAgents:
    """Test autonomous agent execution."""

    def test_run_agents_manual(self, base_url, api_client):
        """Test manual agent execution endpoint."""
        # First create some orders to give agents work to do
        for _ in range(3):
            api_client.post(f"{base_url}/api/orders/create")
        
        time.sleep(1)
        
        # Run agents
        response = api_client.post(f"{base_url}/api/agents/run")
        assert response.status_code == 200
        
        data = response.json()
        assert "inventory_decisions" in data
        assert "dispatch_decisions" in data
        assert isinstance(data["inventory_decisions"], int)
        assert isinstance(data["dispatch_decisions"], int)
        assert data["inventory_decisions"] >= 0
        assert data["dispatch_decisions"] >= 0
        
        total_decisions = data["inventory_decisions"] + data["dispatch_decisions"]
        print(f"✓ Agents executed: {data['inventory_decisions']} inventory + {data['dispatch_decisions']} dispatch = {total_decisions} total decisions")
        
        # Verify decisions were logged
        if total_decisions > 0:
            time.sleep(0.5)
            feed_response = api_client.get(f"{base_url}/api/dashboard/live-feed?limit=10")
            assert feed_response.status_code == 200
            decisions = feed_response.json()
            assert len(decisions) > 0
            print(f"✓ Agent decisions logged in live feed")
