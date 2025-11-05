"""
Analyze Width Utilization after Improvements
"""
import json

def analyze_width_utilization():
    # Load results
    with open('z_first_packing_result.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    container = result['containers'][0]
    container_width = container['dimensions']['width']
    container_height = container['dimensions']['height']
    
    print("="*80)
    print("WIDTH UTILIZATION ANALYSIS")
    print("="*80)
    print(f"Container dimensions: {container_width}\" x {container_height}\"")
    print()
    
    rows = container.get('rows', [])
    if not rows:
        print("No rows found in result")
        return
    
    # Previous results (from TEST_REPORT.md)
    previous_results = {
        1: {'width': 91.0, 'width_pct': 98.4, 'cells': 5},
        2: {'width': 51.0, 'width_pct': 55.1, 'cells': 2},
        3: {'width': 85.0, 'width_pct': 91.9, 'cells': 4},
        4: {'width': 65.0, 'width_pct': 70.3, 'cells': 3},
        5: {'width': 90.0, 'width_pct': 97.3, 'cells': 3},
        6: {'width': 30.0, 'width_pct': 32.4, 'cells': 1},
        7: {'width': 90.0, 'width_pct': 97.3, 'cells': 3},
    }
    
    print("Row-by-Row Width Utilization Comparison:")
    print("-"*80)
    print(f"{'Row':<6} {'Cells':<8} {'Width':<10} {'Width%':<10} {'Height':<10} {'Status':<15} {'Change':<15}")
    print("-"*80)
    
    total_width = 0
    total_height = 0
    improved_rows = []
    unchanged_rows = []
    regressed_rows = []
    
    for row in rows:
        row_num = row['row']
        cells = row['cells']
        row_width = sum(cell['dimensions']['width'] for cell in cells)
        row_height = row['height']
        
        width_pct = (row_width / container_width * 100) if container_width > 0 else 0
        height_pct = (row_height / container_height * 100) if container_height > 0 else 0
        
        total_width += row_width
        total_height += row_height
        
        # Compare with previous
        prev = previous_results.get(row_num, {})
        prev_width_pct = prev.get('width_pct', 0)
        
        if prev_width_pct > 0:
            change = width_pct - prev_width_pct
            if change > 5.0:
                status = "IMPROVED"
                change_str = f"+{change:.1f}%"
                improved_rows.append(row_num)
            elif change < -5.0:
                status = "REGRESSED"
                change_str = f"{change:.1f}%"
                regressed_rows.append(row_num)
            else:
                status = "UNCHANGED"
                change_str = f"{change:+.1f}%"
                unchanged_rows.append(row_num)
        else:
            status = "NEW ROW"
            change_str = "N/A"
        
        # Determine status icon
        if width_pct >= 90:
            status_icon = "OK"
        elif width_pct >= 80:
            status_icon = "GOOD"
        elif width_pct >= 70:
            status_icon = "FAIR"
        else:
            status_icon = "LOW"
        
        print(f"{row_num:<6} {len(cells):<8} {row_width:<10.1f} {width_pct:<10.1f} {row_height:<10.1f} {status_icon:<15} {change_str:<15}")
    
    print("-"*80)
    avg_width_pct = (total_width / len(rows) / container_width * 100) if rows else 0
    avg_height_pct = (total_height / len(rows) / container_height * 100) if rows else 0
    
    print(f"\nAverage Width Utilization: {avg_width_pct:.1f}%")
    print(f"Average Height Utilization: {avg_height_pct:.1f}%")
    
    print("\n" + "="*80)
    print("IMPROVEMENT SUMMARY")
    print("="*80)
    print(f"Rows with improved width utilization (>5% increase): {len(improved_rows)}")
    if improved_rows:
        print(f"  -> Rows: {', '.join(map(str, improved_rows))}")
    
    print(f"\nRows with unchanged width utilization: {len(unchanged_rows)}")
    if unchanged_rows:
        print(f"  -> Rows: {', '.join(map(str, unchanged_rows))}")
    
    print(f"\nRows with regressed width utilization (>5% decrease): {len(regressed_rows)}")
    if regressed_rows:
        print(f"  -> Rows: {', '.join(map(str, regressed_rows))}")
    
    # Target rows analysis
    print("\n" + "="*80)
    print("TARGET ROWS ANALYSIS (Row 2, 4, 6)")
    print("="*80)
    
    target_rows = [2, 4, 6]
    for row_num in target_rows:
        row = next((r for r in rows if r['row'] == row_num), None)
        if row:
            cells = row['cells']
            row_width = sum(cell['dimensions']['width'] for cell in cells)
            width_pct = (row_width / container_width * 100) if container_width > 0 else 0
            prev = previous_results.get(row_num, {})
            prev_width_pct = prev.get('width_pct', 0)
            
            print(f"\nRow {row_num}:")
            print(f"  Current width: {row_width:.1f}\" ({width_pct:.1f}%)")
            if prev_width_pct > 0:
                print(f"  Previous width: {prev['width']:.1f}\" ({prev_width_pct:.1f}%)")
                change = width_pct - prev_width_pct
                print(f"  Change: {change:+.1f}%")
                if change > 5:
                    print(f"  Status: IMPROVED (Target: >80% for Row 2, >85% for Row 4, >70% for Row 6)")
                elif change < -5:
                    print(f"  Status: REGRESSED")
                else:
                    print(f"  Status: UNCHANGED")
            else:
                print(f"  Status: NEW ROW")
        else:
            print(f"\nRow {row_num}: NOT FOUND")

if __name__ == '__main__':
    analyze_width_utilization()

