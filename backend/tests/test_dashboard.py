"""Dashboard API endpoint tests."""
import pytest
import time

class TestDashboard:
    """Test dashboard endpoints."""

    def test_get_metrics(self, base_url, api_client):
        """Test dashboard metrics endpoint returns all required fields."""
        response = api_client.get(f"{base_url}/api/dashboard/metrics")
        assert response.status_code == 200
        
        data = response.json()
        # Verify all required metric fields
        required_fields = [
            "total_orders", "active_orders", "pending_orders",
            "delivered", "failed", "success_rate", "stress_level",
            "inventory_health", "avg_delivery_time", "purchase_orders",
            "agent_decisions", "stress_test_running"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate data types and ranges
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["active_orders"], int)
        assert isinstance(data["success_rate"], (int, float))
        assert 0 <= data["success_rate"] <= 100
        assert isinstance(data["stress_level"], (int, float))
        assert 0 <= data["stress_level"] <= 100
        assert isinstance(data["inventory_health"], (int, float))
        assert 0 <= data["inventory_health"] <= 100
        
        print(f"✓ Metrics retrieved: {data['total_orders']} orders, {data['stress_level']}% stress, {data['inventory_health']}% inventory health")

    def test_get_live_feed(self, base_url, api_client):
        """Test live feed endpoint returns agent decisions."""
        response = api_client.get(f"{base_url}/api/dashboard/live-feed?limit=30")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            decision = data[0]
            # Verify decision structure
            required_fields = [
                "decision_id", "agent_type", "decision_type",
                "summary", "reasoning", "outcome", "confidence",
                "execution_status", "created_at"
            ]
            for field in required_fields:
                assert field in decision, f"Missing field in decision: {field}"
            
            # Validate agent_type
            assert decision["agent_type"] in ["inventory", "dispatch"]
            assert decision["execution_status"] == "executed"
            assert 0 <= decision["confidence"] <= 1
            print(f"✓ Live feed retrieved: {len(data)} decisions, latest: {decision['agent_type']} - {decision['summary'][:50]}...")
        else:
            print("✓ Live feed retrieved: 0 decisions (agents haven't run yet)")

    def test_get_stock_heatmap(self, base_url, api_client):
        """Test stock heatmap endpoint returns products with status."""
        response = api_client.get(f"{base_url}/api/dashboard/stock-heatmap")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No products in stock heatmap"
        
        product = data[0]
        # Verify product structure
        required_fields = [
            "product_id", "name", "category", "aisle",
            "current_stock", "max_stock", "stock_pct", "status",
            "demand_velocity", "unit_cost"
        ]
        for field in required_fields:
            assert field in product, f"Missing field in product: {field}"
        
        # Validate status values
        assert product["status"] in ["critical", "low", "moderate", "healthy"]
        assert 0 <= product["stock_pct"] <= 100
        assert product["current_stock"] >= 0
        assert product["max_stock"] > 0
        
        # Count status distribution
        status_counts = {}
        for p in data:
            status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1
        
        print(f"✓ Stock heatmap retrieved: {len(data)} products, status: {status_counts}")

    def test_get_stock_heatmap_with_category_filter(self, base_url, api_client):
        """Test stock heatmap with category filter."""
        response = api_client.get(f"{base_url}/api/dashboard/stock-heatmap?category=Dairy & Eggs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All products should be from the filtered category
        for product in data:
            assert product["category"] == "Dairy & Eggs"
        
        print(f"✓ Stock heatmap filtered by category: {len(data)} Dairy & Eggs products")

    def test_get_categories(self, base_url, api_client):
        """Test categories endpoint returns list of categories."""
        response = api_client.get(f"{base_url}/api/dashboard/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "All" in data
        
        # Verify expected categories exist
        expected_categories = ["Fresh Produce", "Dairy & Eggs", "Beverages", "Snacks"]
        for cat in expected_categories:
            assert cat in data, f"Missing category: {cat}"
        
        print(f"✓ Categories retrieved: {len(data)} categories")

    def test_get_purchase_orders(self, base_url, api_client):
        """Test purchase orders endpoint."""
        response = api_client.get(f"{base_url}/api/dashboard/purchase-orders?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            po = data[0]
            required_fields = [
                "po_id", "product_id", "product_name", "category",
                "quantity", "supplier", "unit_cost", "total_cost",
                "urgency", "status", "created_at"
            ]
            for field in required_fields:
                assert field in po, f"Missing field in PO: {field}"
            
            assert po["urgency"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert po["status"] in ["generated", "approved", "received", "cancelled"]
            print(f"✓ Purchase orders retrieved: {len(data)} POs")
        else:
            print("✓ Purchase orders retrieved: 0 POs (inventory agent hasn't run yet)")
