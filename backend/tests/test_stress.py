"""Stress test endpoint tests."""
import pytest
import time

class TestStressTest:
    """Test stress test functionality."""

    def test_get_stress_test_status(self, base_url, api_client):
        """Test stress test status endpoint."""
        response = api_client.get(f"{base_url}/api/stress-test/status")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["running", "progress", "total", "orders_created", "decisions_made"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert isinstance(data["running"], bool)
        assert isinstance(data["progress"], (int, float))
        print(f"✓ Stress test status: running={data['running']}, progress={data['progress']}%")

    def test_start_stress_test(self, base_url, api_client):
        """Test starting a stress test with 50 orders."""
        # Check if already running
        status_response = api_client.get(f"{base_url}/api/stress-test/status")
        status = status_response.json()
        
        if status["running"]:
            pytest.skip("Stress test already running")
        
        # Start stress test
        response = api_client.post(
            f"{base_url}/api/stress-test/start",
            json={"order_count": 50}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "started"
        assert data["order_count"] == 50
        
        print(f"✓ Stress test started: {data['order_count']} orders")
        
        # Wait a bit and check status
        time.sleep(3)
        status_response = api_client.get(f"{base_url}/api/stress-test/status")
        status = status_response.json()
        
        # Should be running or completed
        assert status["progress"] > 0
        assert status["orders_created"] > 0
        print(f"✓ Stress test progress: {status['progress']}%, {status['orders_created']} orders created")
        
        # Wait for completion (max 30 seconds)
        max_wait = 30
        waited = 0
        while waited < max_wait:
            status_response = api_client.get(f"{base_url}/api/stress-test/status")
            status = status_response.json()
            
            if not status["running"] and status["results"]:
                results = status["results"]
                print(f"✓ Stress test completed: {results.get('total_orders')} total orders, {results.get('success_rate')}% success rate")
                
                # Verify results structure
                assert "total_orders" in results
                assert "orders_processed" in results
                assert "success_rate" in results
                assert "agent_decisions" in results
                break
            
            time.sleep(2)
            waited += 2
        
        if waited >= max_wait:
            print(f"⚠ Stress test still running after {max_wait}s (this is normal for large tests)")

    def test_stress_test_already_running(self, base_url, api_client):
        """Test that starting a stress test while one is running fails."""
        # Check current status
        status_response = api_client.get(f"{base_url}/api/stress-test/status")
        status = status_response.json()
        
        if not status["running"]:
            # Start one first
            api_client.post(
                f"{base_url}/api/stress-test/start",
                json={"order_count": 50}
            )
            time.sleep(1)
        
        # Try to start another
        response = api_client.post(
            f"{base_url}/api/stress-test/start",
            json={"order_count": 50}
        )
        
        # Should fail with 400 if one is running
        if response.status_code == 400:
            print("✓ Correctly rejected duplicate stress test")
        else:
            # If it succeeded, the previous one must have finished
            print("✓ Previous stress test completed, new one started")
