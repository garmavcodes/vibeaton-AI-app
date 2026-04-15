"""Order management endpoint tests."""
import pytest
import time

class TestOrders:
    """Test order creation and management."""

    def test_create_order(self, base_url, api_client):
        """Test creating a single order."""
        response = api_client.post(f"{base_url}/api/orders/create")
        assert response.status_code == 200
        
        data = response.json()
        assert "order_id" in data
        assert "items" in data
        assert "zone" in data
        assert data["items"] > 0
        
        print(f"✓ Order created: {data['order_id']}, {data['items']} items, zone: {data['zone']}")
        
        # Verify order was persisted by fetching orders
        time.sleep(0.5)
        get_response = api_client.get(f"{base_url}/api/orders?limit=10")
        assert get_response.status_code == 200
        orders = get_response.json()
        assert any(o["order_id"] == data["order_id"] for o in orders)
        print(f"✓ Order verified in database")

    def test_get_orders(self, base_url, api_client):
        """Test fetching orders list."""
        response = api_client.get(f"{base_url}/api/orders?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            order = data[0]
            required_fields = [
                "order_id", "items", "delivery_zone", "status",
                "priority_score", "created_at"
            ]
            for field in required_fields:
                assert field in order, f"Missing field in order: {field}"
            
            assert order["status"] in ["pending", "batched", "picking", "dispatched", "delivered", "failed"]
            assert 0 <= order["priority_score"] <= 1
            print(f"✓ Orders retrieved: {len(data)} orders")
        else:
            print("✓ Orders retrieved: 0 orders")

    def test_get_orders_by_status(self, base_url, api_client):
        """Test filtering orders by status."""
        response = api_client.get(f"{base_url}/api/orders?status=pending&limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All orders should have pending status
        for order in data:
            assert order["status"] == "pending"
        
        print(f"✓ Pending orders retrieved: {len(data)} orders")
