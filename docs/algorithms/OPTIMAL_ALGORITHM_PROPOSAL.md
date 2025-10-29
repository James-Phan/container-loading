# Đề Xuất Thuật Toán Tối Ưu Cho Container Layout

## Phân Tích Manual Layout Thành Công

### Pattern từ Manual Layout (210" cho 472 boxes):

1. **Row Structure**:
   - Row 1-2: PRE_PACK boxes (A-N), heights ~26-34"
   - Row 3-5: Mixed PRE_PACK + CARTON, heights ~16-26"
   - Row 6-8: Pure CARTON (J2, K2), heights 17-30"

2. **Rotation Strategy**:
   - J2/K2 (30"×17"×5"): Rotate → 17" width → 5 boxes/row
   - D2/E2/F2/G2 (24"×16"×h): Rotate → 16" width → 5 boxes/row

3. **Horizontal Packing**:
   - Fill width trước (x-axis): 92.5" / box_width = boxes per row
   - Fill rows ngang (y-axis): stack boxes vertically within row
   - Minimal gaps: packs tightly left-to-right

4. **Grouping Strategy**:
   - Gom boxes cùng material/purchasing_doc
   - Gom boxes cùng height trong cùng row
   - Không tách nhóm: 28 C2 → pack liên tục, không rải

## Đề Xuất Thuật Toán: Layer-Based Bin Packing

### Core Strategy

```
Phase 1: Sort & Group
Phase 2: Create Layers (by height)
Phase 3: Pack Horizontally (fill width)
Phase 4: Stack Vertically (fill height)
```

### Phase 1: Sort & Group

```python
def sort_and_group(boxes):
    # Sort by: material → purchasing_doc → height → area
    sorted_boxes = sorted(boxes, key=lambda x: (
        x['material'],
        x['purchasing_doc'],
        x['dimensions']['height'],
        -(x['dimensions']['width'] * x['dimensions']['length'])
    ))
    
    # Group by height ranges (for layer creation)
    height_groups = {
        'low': [],    # height 3-6"
        'medium': [], # height 7-12"
        'high': []    # height 13-17"
    }
    
    for box in sorted_boxes:
        h = box['dimensions']['height']
        if h <= 6:
            height_groups['low'].append(box)
        elif h <= 12:
            height_groups['medium'].append(box)
        else:
            height_groups['high'].append(box)
    
    return height_groups
```

### Phase 2: Create Layers

```python
def create_layers(height_groups, container):
    """
    Create layers based on row heights from manual layout
    
    Row heights observed: 16.5", 17.5", 26.5", 30.5", 34.5"
    
    Strategy: Group boxes into layers with similar heights
    """
    layers = []
    
    # Layer 1: High boxes (17.5", 26.5", 34.5")
    layer1 = {
        'target_height': 34.5,
        'boxes': height_groups['high'][:60]  # First 60 boxes
    }
    layers.append(layer1)
    
    # Layer 2-3: Medium boxes (26.5")
    # Layer 4-5: Low+Medium mixed (16.5", 17.5")
    # ... etc
    
    return layers
```

### Phase 3: Pack Horizontally (Fill Width)

```python
def pack_layer_horizontally(layer, container_width):
    """
    Pack boxes in a layer, prioritizing width filling
    
    Key insight from manual: Fill container width first!
    """
    rows = []
    current_row = {
        'boxes': [],
        'x': 0,
        'y': 0,
        'height': 0
    }
    
    for box in layer['boxes']:
        # Optimize rotation for CARTON
        orientation = find_best_orientation(box, container_width)
        
        # Check if fits in current row
        if current_row['x'] + orientation['width'] <= container_width:
            # Add to current row
            box['position'] = {
                'x': current_row['x'],
                'y': current_row['y'],
                'z': current_row.get('z', 0)
            }
            current_row['boxes'].append(box)
            current_row['x'] += orientation['width']
            current_row['height'] = max(current_row['height'], orientation['height'])
        else:
            # Finish current row, start new row
            rows.append(current_row)
            current_row = {
                'boxes': [box],
                'x': 0,
                'y': rows[-1]['y'] + rows[-1]['height'],
                'height': orientation['height']
            }
    
    return rows
```

### Phase 4: Stack Vertically (Fill Height)

```python
def stack_within_row(boxes_in_row):
    """
    Stack boxes vertically within a row
    
    Similar to manual: Stack boxes on top of each other
    """
    stacked = []
    z_positions = {}  # Track z level for each (x, y)
    
    for box in boxes_in_row:
        pos = box['position']
        key = f"{pos['x']},{pos['y']}"
        
        # Find z position for this stack
        if key in z_positions:
            z = z_positions[key]
        else:
            z = 0
            z_positions[key] = 0
        
        # Place box
        box['position']['z'] = z
        box['dimensions'] = box.get('orientation', box['dimensions'])
        
        # Update z for next box in this stack
        z_positions[key] = z + box['dimensions']['height']
        
        stacked.append(box)
    
    return stacked
```

## Thuật Toán Hoàn Chỉnh

### ALGORITHM: Optimal Layer-Based Packing

```python
def pack_boxes_optimally(boxes, container):
    # Phase 1: Sort & Group
    height_groups = sort_and_group(boxes)
    
    # Phase 2: Create Layers
    layers = create_layers(height_groups, container)
    
    # Phase 3 & 4: Pack each layer
    all_placed_boxes = []
    current_y = 10  # Door clearance
    
    for layer in layers:
        # Pack horizontally in this layer
        rows = pack_layer_horizontally(layer, container['width'])
        
        for row in rows:
            # Adjust y position
            for box in row['boxes']:
                box['position']['y'] = current_y
            
            # Stack vertically
            stacked = stack_within_row(row['boxes'])
            
            all_placed_boxes.extend(stacked)
            
            # Move to next row
            current_y += row['height']
    
    return all_placed_boxes
```

## Key Differences from LAFF

| Aspect | LAFF (Current) | Layer-Based (Optimal) |
|--------|----------------|---------------------|
| Sorting | material → area | material → height → area |
| Packing | Find best space | Fill width first |
| Orientation | Try all valid | Choose best for width |
| Grouping | None | By height ranges |
| Rows | 17-23 rows | 8-10 rows |
| Length | 454" | Target: ~210" |

## Implementation Strategy

### Step 1: Replace `_sort_boxes_by_area()`

```python
def _sort_boxes_by_height_and_group(self, boxes):
    """
    Sort by: material → purchasing_doc → height → area
    Group by: height ranges for layer creation
    """
    # Sort
    sorted_boxes = sorted(boxes, key=lambda x: (
        x.get('material', ''),
        x.get('purchasing_doc', ''),
        x['dimensions']['height'],  # Group by height first!
        -(x['dimensions']['width'] * x['dimensions']['length'])
    ))
    
    return sorted_boxes
```

### Step 2: Add `_find_best_orientation()` for CARTON

```python
def _find_best_orientation_carton(self, box, container_width):
    """
    Find orientation that fits most boxes per row
    """
    box_dims = box['dimensions']
    
    orientations = [
        box_dims,  # Normal
        {'width': box_dims['length'], 'length': box_dims['width'], 'height': box_dims['height']},  # Rotate XY
        {'width': box_dims['width'], 'length': box_dims['height'], 'height': box_dims['length']},  # Rotate XZ
    ]
    
    # Calculate boxes per row for each
    best_orientation = box_dims
    max_boxes = 0
    
    for orientation in orientations:
        if orientation['height'] <= self.container['height']:
            boxes_per_row = int(container_width / orientation['width'])
            if boxes_per_row > max_boxes:
                max_boxes = boxes_per_row
                best_orientation = orientation
    
    return best_orientation
```

### Step 3: Add Horizontal-First Packing

```python
def pack_horizontally(self, boxes, layer_y):
    """
    Pack boxes horizontally, filling width before moving to next row
    """
    rows = []
    current_row_boxes = []
    current_x = 0
    
    for box in boxes:
        orientation = self._find_best_orientation_carton(box, self.container['width'])
        box_width = orientation['width']
        
        if current_x + box_width <= self.container['width']:
            # Fits in current row
            box['position'] = {'x': current_x, 'y': layer_y, 'z': 0}
            box['orientation'] = orientation
            current_row_boxes.append(box)
            current_x += box_width
        else:
            # Start new row
            if current_row_boxes:
                rows.append(current_row_boxes)
            current_row_boxes = [box]
            current_x = box_width
            layer_y += max([b.get('height', 0) for b in current_row_boxes])
    
    return rows
```

## Expected Results

- **Rows**: 8-10 rows (vs 17-23 LAFF)
- **Length**: ~210-250" (vs 454" LAFF)
- **Containers**: 1 container (vs 2)
- **Utilization**: 40-45% (vs 33%)
- **Boxes per row**: 3-5 cells (maximize width usage)
- **Row heights**: Consistent 16-35" ranges

## Rationale

Manual layout chia thành 8 rows compact:
- Row 1 (34.5"): 60 boxes in 4 cells
- Row 6-7 (30.5"): 95 boxes each in 5 cells
- Row 8 (17.5"): 56 boxes in 3 cells

LAFF hiện tại:
- Rời rạc hơn: nhiều rows nhỏ
- Không tập trung boxes cùng loại
- Chưa ưu tiên xếp theo width

Giải pháp: Layer-based packing giúp:
- Gom boxes cùng height
- Điền đầy width
- Tạo rows liền mạch
- Giảm khoảng trống

