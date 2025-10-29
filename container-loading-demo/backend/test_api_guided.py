"""
Test API với Guided Packing
"""

import requests
import json

# Load test data
with open('test_data_real_3d.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Test với Guided algorithm
print("Testing with GUIDED algorithm...")
response = requests.post('http://localhost:8000/calculate', json={
    "boxes": data['boxes'],
    "algorithm": "guided"
})

if response.status_code == 200:
    result = response.json()
    
    print(f"\n✅ Success!")
    print(f"Containers: {result['layout']['total_containers']}")
    print(f"Total boxes: {result['layout']['total_boxes']}")
    print(f"Utilization: {result['layout']['utilization']:.1f}%")
    print(f"Algorithm: {result['layout'].get('algorithm', 'unknown')}")
    
    # Save result
    with open('guided_api_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nResult saved to: guided_api_result.json")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

