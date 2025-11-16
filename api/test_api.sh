#!/bin/bash

echo "Testing College Affordability ML API..."
echo "========================================="

API_URL="http://localhost:5000"

# Test 1: Home endpoint
echo -e "\n1. Testing home endpoint..."
curl -s "$API_URL/" | python3 -m json.tool

# Test 2: Health check
echo -e "\n\n2. Testing health endpoint..."
curl -s "$API_URL/health" | python3 -m json.tool

# Test 3: List models
echo -e "\n\n3. Testing models endpoint..."
curl -s "$API_URL/models" | python3 -m json.tool

# Test 4: Search institutions
echo -e "\n\n4. Testing institution search (Harvard)..."
curl -s "$API_URL/institutions?name=harvard&limit=3" | python3 -m json.tool

# Test 5: Make a prediction (example with dummy data)
echo -e "\n\n5. Testing prediction endpoint (dummy data)..."
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "r1a",
    "features": {
      "afford_gap_cont": 5000,
      "admit_rate": 0.65,
      "sat_avg": 1200,
      "act_avg": 25,
      "sat_missing": 0,
      "act_missing": 0,
      "inst_size": 5000,
      "pct_pell": 0.30,
      "pct_urm": 0.25,
      "pct_white": 0.50,
      "pct_black": 0.10,
      "pct_latino": 0.15,
      "pct_asian": 0.20,
      "pct_women": 0.55,
      "inst_expend": 15000,
      "endow_log": 10.5,
      "endow_binary": 1,
      "hbcu": 0,
      "hsi": 0,
      "aanapisi": 0,
      "pbi": 0,
      "tribal": 0,
      "msi_other": 0,
      "sector_public_4yr": 1,
      "sector_private_nonprofit_4yr": 0,
      "region_midwest": 0,
      "region_northeast": 1,
      "region_south": 0,
      "region_west": 0,
      "afford_x_admit": 3250,
      "afford_x_sat": 6000000
    }
  }' | python3 -m json.tool

echo -e "\n\n========================================="
echo "API testing complete!"

