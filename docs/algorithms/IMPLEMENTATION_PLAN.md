# Implementation Plan: Optimal Layer-Based Bin Packing

## Mục Tiêu

Match manual layout:
- 8 rows (thay vì 17-23 rows của LAFF)
- ~210" length (thay vì 454")
- 1 container (thay vì 2)
- Compact, grouped packing

## Approach

### Strategy Shift

**FROM**: Space-based packing (find best space)  
**TO**: Layer-based packing (fill width first)

### Key Changes

1. **Sorting Priority**:
   ```
   LAFF: material → purchasing_doc → area → quantity
   OPTIMAL: material → purchasing_doc → HEIGHT → area
   ```
   
   Why: Group by height để tạo layers

2. **Packing Order**:
   ```
   LAFF: Try largest available space → place → split
   OPTIMAL: Fill width horizontally → stack vertically → next row
   ```

3. **Orientation Selection**:
   ```
   LAFF: Try all orientations, return first that fits
   OPTIMAL: Try all orientations, return BEST (maximizes boxes/row)
   ```

## Implementation Steps

### Step 1: Update Sorting (HIGH PRIORITY)

File: `laff_bin_packing_3d.py`

Change `_sort_boxes_by_area()` to sort by HEIGHT first:

```python
def _sort_boxes_by_height_first(self, boxes):
    """
    Sort by: material → purchasing_doc → HEIGHT → area → quantity
    
    This enables layer-based packing
    """
    sorted_boxes = sorted(boxes, key=lambda x: (
        x.get('material', ''),
        x.get('purchasing_doc', ''),
        x['dimensions']['height'],  # HEIGHT FIRST!
        -(x['dimensions']['width'] * x['dimensions']['length']),
        -x['quantity']
    ))
    
    return sorted_boxes
```

Impact: Boxes cùng height sẽ gom lại, dễ tạo layers

### Step 2: Horizontal-First Packing (HIGH PRIORITY)

File: `laff_bin_packing_3d.py`

Replace space-based packing with row-based packing:

```python
def pack_boxes_in_row(self, boxes, row_y, row_height_limit):
    """
    Pack boxes horizontally in a row
    Fill width completely before moving to next row
    """
    placed_boxes = []
    current_x = 0
    current_z = 0
    row_height = 0
    
    for box in boxes:
        # Get best orientation
        orientation = self._get_optimal_orientation(box)
        
        # Check if fits in current row width
        if current_x + orientation['width'] <= self.container['width']:
            # Place in current position
            placed_boxes.append({
                **box,
                'position': {'x': current_x, 'y': row_y, 'z': current_z},
                'dimensions': orientation
            })
            current_x += orientation['width']
            row_height = max(row_height, orientation['height'])
        else:
            # Move to next column (stack vertically)
            current_x = 0
            current_z += orientation['height']
            
            # Check if exceeded row height limit
            if current_z + orientation['height'] > row_height_limit:
                break  # Move to next row
            
            # Place in new column
            placed_boxes.append({
                **box,
                'position': {'x': current_x, 'y': row_y, 'z': current_z},
                'dimensions': orientation
            })
            current_x += orientation['width']
            row_height = max(row_height, orientation['height'])
    
    return placed_boxes, row_height
```

Impact: Tạo rows compact, fill width hiệu quả hơn

### Step 3: Layer Creation (MEDIUM PRIORITY)

File: `laff_bin_packing_3d.py`

Add method to create layers based on heights:

```python
def create_height_layers(self, sorted_boxes):
    """
    Create layers based on box heights
    Similar to row heights in manual layout
    """
    layers = []
    
    target_row_heights = [34.5, 26.5, 26.5, 16.5, 17.5, 30.5, 30.5, 17.5]
    
    boxes_by_height = {}
    for box in sorted_boxes:
        h = box['dimensions']['height']
        if h not in boxes_by_height:
            boxes_by_height[h] = []
        boxes_by_height[h].append(box)
    
    # Group similar heights together
    for target_height in target_row_heights:
        layer_boxes = []
        # Find boxes with compatible heights
        for h, boxes in boxes_by_height.items():
            if h <= target_height:
                layer_boxes.extend(boxes[:20])  # Limit boxes per layer
        
        if layer_boxes:
            layers.append({
                'target_height': target_height,
                'boxes': layer_boxes
            })
    
    return layers
```

Impact: Tạo structure giống manual layout

### Step 4: Orientation Optimization (ALREADY DONE)

Current code already chooses best orientation by min width. Good!

### Step 5: Row Consolidation (LOW PRIORITY)

File: `output_formatter_3d.py`

Merge consecutive cells with similar characteristics:

```python
def consolidate_rows(self, cells):
    """
    Merge cells that are adjacent and similar
    Creates fewer but larger cells
    """
    # Group by y position
    by_y = {}
    for cell in cells:
        y = cell['position']['y']
        if y not in by_y:
            by_y[y] = []
        by_y[y].append(cell)
    
    # Merge adjacent similar cells
    merged = []
    for y, cell_list in sorted(by_y.items()):
        # Sort by x
        cell_list.sort(key=lambda c: c['position']['x'])
        
        # Try to merge
        current_group = [cell_list[0]]
        for cell in cell_list[1:]:
            if self._can_merge_cells(current_group[-1], cell):
                current_group.append(cell)
            else:
                merged.append(self._merge_cell_group(current_group))
                current_group = [cell]
        
        merged.append(self._merge_cell_group(current_group))
    
    return merged
```

Impact: Giảm số cells, tăng compactness

## Expected Improvements

| Metric | Current LAFF | Target | Improvement |
|--------|--------------|--------|-------------|
| Rows | 17-23 | 8-10 | 50-60% ↓ |
| Length | 454" | 210-250" | 50-55% ↓ |
| Containers | 2 | 1 | 50% ↓ |
| Utilization | 33% | 40-45% | 20-30% ↑ |
| Cell compactness | Low | High | Better |

## Testing

After implementation, test with:

```python
# Should get similar to manual layout:
- 8 rows
- ~210" length
- Grouped boxes (C2 together, J2 together)
- Consistent row heights (16-35")
- Fewer containers (1 vs 2)
```

## Implementation Order

1. ✓ Update container dimensions (92.5"×106")
2. ✓ Implement rotation optimization
3. ⏳ Update sorting to height-first
4. ⏳ Implement horizontal-first packing
5. ⏳ Add layer creation logic
6. ⏳ Test and tune

## Risks & Mitigation

**Risk**: Breaking existing functionality  
**Mitigation**: Keep LAFF as backup, implement as optional strategy

**Risk**: Performance degradation  
**Mitigation**: Profile code, optimize bottlenecks

**Risk**: Edge cases not handled  
**Mitigation**: Comprehensive testing with varied inputs

