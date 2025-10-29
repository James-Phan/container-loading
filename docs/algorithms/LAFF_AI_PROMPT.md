# LAFF 3D Bin Packing - AI Prompt Template

## Context

You are implementing a LAFF (Largest Area Fit First) 3D bin packing algorithm for container layout optimization.

## Container Specifications

- Dimensions: 92.5" × 473" × 106" (width × length × height)
- Total volume: 4,636,753 cubic inches
- Door clearance: 10" from container door

## Core Requirements

### 1. Orientation Rules

**PRE_PACK (materials A-N)**:
- Face with WIDTH × HEIGHT cannot touch floor
- Floor contact must be WIDTH × LENGTH
- No rotation allowed
- Supports vertical stacking with stability check

**CARTON (materials O-K2)**:
- Face with HEIGHT cannot touch floor
- Allowed orientations:
  - WIDTH × LENGTH (normal)
  - LENGTH × WIDTH (swap width↔length, 90° XY plane)
  - WIDTH × HEIGHT (swap length↔height)
- NOT allowed: LENGTH × HEIGHT (would put height on floor)
- **ROTATION OPTIMIZATION**: Choose orientation that maximizes boxes per row
- **Example**: J2 (30"×17"×5") → normal: 3 boxes/row, rotated: 5 boxes/row → choose rotated

### 2. Sorting Priority

Sort boxes by:
1. **Material** (ascending)
2. **Purchasing Document** (ascending)  
3. **Area** (descending: width × length)
4. **Quantity** (descending)

### 3. Placement Rules

- Validate container boundaries before placement
- Row height = **MAX** height (not sum) of cells in row
- Each cell can stack boxes vertically (Z-axis)
- Cells grouped by Y position form rows
- Sort cells by X position (left-to-right)

### 4. Output Format

```json
{
  "containers": [{
    "container_id": 1,
    "rows": [{
      "row": 1,
      "height": 34.5,
      "cells": [{
        "cell": 1,
        "content": "1A+1B+3C+9D+1E+5F",
        "total_boxes": 60,
        "columns": ["A", "B", "C", "D", "E", "F"],
        "position": {"x": 0, "y": 0},
        "items": {"A": 1, "B": 1, "C": 3, "D": 9, "E": 1, "F": 5}
      }]
    }]
  }],
  "total_boxes": 470,
  "total_containers": 1,
  "utilization": 15.2,
  "overall_utilization": 15.2
}
```

## Rotation Optimization for CARTON

### Problem
Current algorithm tries all valid orientations but doesn't choose the BEST one for container width.

### Solution
For CARTON boxes, implement smart orientation selection:

```python
def find_best_carton_orientation(box, container_width):
    """
    Find orientation that fits most boxes per row
    """
    box_dims = box['dimensions']
    orientations = [
        {'width': box_dims['width'], 'length': box_dims['length'], 'height': box_dims['height']},  # Normal
        {'width': box_dims['length'], 'length': box_dims['width'], 'height': box_dims['height']},  # Rotate XY
        {'width': box_dims['width'], 'length': box_dims['height'], 'height': box_dims['length']},  # Rotate XZ
    ]
    
    best_orientation = orientations[0]
    max_boxes_per_row = 0
    
    for orientation in orientations:
        if orientation['height'] <= container_height:  # Can stack to this height
            boxes_per_row = int(container_width / orientation['width'])
            if boxes_per_row > max_boxes_per_row:
                max_boxes_per_row = boxes_per_row
                best_orientation = orientation
    
    return best_orientation
```

### Expected Impact
- Manual: 210" length for 472 boxes
- Current: 466" length for 470 boxes
- Target: ~210-250" length (reduce by 50-60%)

## Key Bugs to Fix

### Bug 1: Row Height Calculation (output_formatter_3d.py:105)

**Current (WRONG)**:
```python
cell_height = sum(box['dimensions']['height'] for box in cell['boxes'])
```

**Correct**:
```python
cell_height = max(box['dimensions']['height'] for box in cell['boxes'])
```

### Bug 2: No Container Boundary Validation

Add validation in `_place_box_in_space()`:
```python
# Check if placement exceeds container
if space.position['x'] + orientation['width'] > self.container['width']:
    return None
if space.position['y'] + orientation['length'] > self.container['length']:
    return None
if space.position['z'] + orientation['height'] > self.container['height']:
    return None
```

### Bug 3: Orientation Rules Not Implemented

Update `EmptySpace.can_fit()` to accept `packing_method`:
```python
def can_fit(self, box, allow_rotation=False, packing_method=None):
    box_dims = box['dimensions']
    position_z = self.position['z']  # z=0 means floor
    
    # PRE_PACK: width×length must be on floor
    if packing_method == 'PRE_PACK' and position_z == 0:
        # Normal orientation: width×length on floor, height vertical
        return self._check_dimensions(box_dims, allow_rotation=False)
    
    # CARTON: height dimension cannot touch floor
    elif packing_method == 'CARTON':
        return self._try_carton_orientations(box_dims, position_z)
    
    # Default behavior
    return self._check_dimensions(box_dims, allow_rotation)
```

### Bug 4: Missing Sorting by Material/Purchasing Doc

Update `_sort_boxes_by_area()` in laff_bin_packing_3d.py:
```python
def _sort_boxes_by_area(self, boxes):
    # Sort by material → purchasing_doc → area → quantity
    sorted_boxes = sorted(boxes, key=lambda x: (
        x['material'],
        x['purchasing_doc'],
        -(x['dimensions']['width'] * x['dimensions']['length']),  # Area descending
        -x['quantity']  # Quantity descending
    ))
    return sorted_boxes
```

## Testing

### Test File
`container-loading-demo/backend/test_data_real_3d.json`

### Expected Results
- All 470 boxes fit in 1-2 containers
- No row height > 102"
- Total length ≤ 473"
- Utilization ≥ 15%
- Orientation rules followed for all boxes

### Run Test
```bash
cd container-loading-demo/backend
python test_laff_packing.py
```

## Implementation Checklist

- [ ] Fix row height calculation (sum → max)
- [ ] Add container boundary validation
- [ ] Implement PRE_PACK orientation rule (width×length on floor)
- [ ] Implement CARTON orientation rules (exclude length×height on floor)
- [ ] Update sorting to use material + purchasing_doc
- [ ] Test with test_data_real_3d.json
- [ ] Validate all constraints
- [ ] Check output format matches manual result

