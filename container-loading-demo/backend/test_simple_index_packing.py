"""
Test Simple Index-Based Cell Packing Algorithm
"""

import json
from simple_index_packing_3d import SimpleIndexPackingAlgorithm
from output_formatter_3d import OutputFormatter3D


def test_simple_index_packing():
    # Load test data
    with open('test_data_real_3d.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    container_dims = data['container']
    boxes = data['boxes']
    
    total_boxes = sum(box['quantity'] for box in boxes)
    print(f"Total boxes to pack: {total_boxes}")
    print(f"Container dimensions: {container_dims}")
    
    # Initialize packer
    packer = SimpleIndexPackingAlgorithm(container_dims=container_dims)
    
    # Pack boxes
    print("\n" + "="*80)
    print("SIMPLE INDEX-BASED CELL PACKING ALGORITHM")
    print("="*80)
    
    containers = packer.pack_boxes(boxes)
    
    # Format output
    formatter = OutputFormatter3D()
    result = formatter.format(containers)
    
    # Print summary
    print("\n" + "="*80)
    print("PACKING RESULTS (Simple Index-Based)")
    print("="*80)
    print(f"Containers used: {result['total_containers']}")
    print(f"Boxes packed: {result['total_boxes']}")
    print(f"Container utilization: {result['overall_utilization']:.1f}%")
    
    if result['containers'] and result['containers'][0].get('rows'):
        print(f"\nTotal rows: {len(result['containers'][0]['rows'])}")
        for row in result['containers'][0]['rows']:
            row_width = sum(cell['dimensions']['width'] for cell in row['cells'])
            print(f"Row {row['row']}: {len(row['cells'])} cells, width={row_width:.1f}\", height={row['height']:.1f}\"")
    
    # Save to JSON file
    output_file = 'simple_index_packing_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Results saved to: {output_file}")
    print("[OK] Test completed successfully!")


if __name__ == '__main__':
    test_simple_index_packing()
