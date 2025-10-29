"""
Test script cho Guided Packing Algorithm
"""

import json
from guided_packing_3d import GuidedPackingAlgorithm
from output_formatter_3d import OutputFormatter3D

def test_guided_packing():
    """Test guided packing with test_data_real_3d.json"""
    
    # Load test data
    with open('test_data_real_3d.json', 'r') as f:
        data = json.load(f)
    
    container_dims = data['container']
    boxes = data['boxes']
    
    # Calculate total boxes
    total_boxes = sum(box['quantity'] for box in boxes)
    print(f"\n{'='*60}")
    print(f"Testing Guided Packing Algorithm")
    print(f"{'='*60}")
    print(f"Total boxes: {total_boxes}")
    print(f"Container: {container_dims}")
    print(f"{'='*60}\n")
    
    # Initialize Guided Packing
    packer = GuidedPackingAlgorithm(
        container_dims=container_dims,
        manual_template_path='manual_layout.json'
    )
    
    # Run packing
    print("Packing boxes...\n")
    containers = packer.pack_boxes(boxes)
    
    # Format output
    formatter = OutputFormatter3D()
    result = formatter.format(containers)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Containers: {result['total_containers']}")
    print(f"Total boxes: {result['total_boxes']}")
    print(f"Utilization: {result['utilization']:.1f}%")
    
    for container_data in result['containers']:
        container_id = container_data['container_id']
        rows = container_data['rows']
        boxes_count = container_data['total_boxes']
        
        print(f"\nContainer {container_id}:")
        print(f"  Boxes: {boxes_count}")
        print(f"  Rows: {len(rows)}")
        
        # Calculate used length
        if rows:
            max_y = 0
            for row in rows:
                for cell in row.get('cells', []):
                    for box in cell.get('boxes', []):
                        max_y = max(max_y, box['position']['y'] + box['dimensions']['length'])
            
            print(f"  Length used: {max_y:.1f}\" (target: ~210\"")
        
        # Print row summary
        for row in rows[:5]:  # Show first 5 rows
            print(f"  Row {row['row']}: height={row['height']:.1f}\", cells={len(row.get('cells', []))}")
        
        if len(rows) > 5:
            print(f"  ... and {len(rows) - 5} more rows")
    
    # Save result to file
    output_file = 'guided_packing_result.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")
    
    return result

if __name__ == '__main__':
    test_guided_packing()

