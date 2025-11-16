#!/bin/bash
# Test script for ML API endpoints

API_URL="http://localhost:5000"

echo "🧪 Testing ML API Endpoints"
echo "="*70
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "GET $API_URL/health"
curl -s "$API_URL/health" | python -m json.tool
echo ""
echo ""

# Test 2: Model info
echo "Test 2: Get Model Information"
echo "GET $API_URL/api/models/info"
curl -s "$API_URL/api/models/info" | python -m json.tool | head -30
echo "... (truncated)"
echo ""
echo ""

# Test 3: Search institutions
echo "Test 3: Search Institutions"
echo "GET $API_URL/api/institutions/search?q=university&limit=3"
curl -s "$API_URL/api/institutions/search?q=university&limit=3" | python -m json.tool
echo ""
echo ""

# Test 4: Feature importance
echo "Test 4: Get Feature Importance"
echo "GET $API_URL/api/feature-importance?model=r1a"
curl -s "$API_URL/api/feature-importance?model=r1a" | python -m json.tool | head -30
echo "... (truncated)"
echo ""
echo ""

# Test 5: Stats
echo "Test 5: Get Dataset Statistics"
echo "GET $API_URL/api/stats"
curl -s "$API_URL/api/stats" | python -m json.tool
echo ""

echo "="*70
echo "✅ All tests completed!"

