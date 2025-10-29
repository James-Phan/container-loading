"""
Z-First Packing Algorithm - Fill height (Z-axis) before width (X-axis)

Strategy:
1. Pack boxes stacking vertically (Z-axis: 0→106") before moving horizontally (X-axis: 0→92.5")
2. Maximize height utilization at each X position
3. When Z axis is full, move to next X position
4. Create rows dynamically based on available boxes
"""

from typing import List, Dict, Any
from laff_bin_packing_3d import LAFFBinPacking3D


class ZFirstPackingAlgorithm(LAFFBinPacking3D):
    """
    Z-First Packing: Fill height (Z-axis) before width (X-axis)
    
    Strategy:
    - Start at (x=0, z=0)
    - Stack boxes vertically (increase Z)
    - When Z full (≥106") → move right (increase X, reset Z)
    - When X full (≥92.5") → move to next row (increase Y)
    
    Inherits from LAFFBinPacking3D for base functionality.
    """
    
    def __init__(self, container_dims: Dict[str, float]):
        super().__init__(container_dims)
    
    def pack_boxes(self, boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pack boxes using Z-first strategy
        
        Args:
            boxes: List of boxes to pack
            
        Returns:
            List[Dict]: Container with packed boxes
        """
        # Initialize container
        self._new_container()
        
        # Sort boxes first (same logic as in pack_row_z_first)
        packing_method_priority = {'PRE_PACK': 0, 'CARTON': 1}
        boxes_sorted = sorted(boxes, key=lambda b: (
            packing_method_priority.get(b.get('packing_method', 'CARTON'), 1),
            b.get('sort_order', 999),
            -b.get('quantity', 1),
            b['dimensions']['height'],
            -(b['dimensions']['width'] * b['dimensions']['length']),
        ))
        
        # Group boxes by sort_order - process each group separately
        boxes_by_sort = {}
        for box in boxes_sorted:
            sort_order = box.get('sort_order', 999)
            if sort_order not in boxes_by_sort:
                boxes_by_sort[sort_order] = []
            boxes_by_sort[sort_order].append(box)
        
        print(f"DEBUG: Total unique boxes: {len(boxes)}")
        total_qty = sum(box.get('quantity', 1) for box in boxes)
        print(f"DEBUG: Total quantity: {total_qty}")
        print(f"DEBUG: Sort order groups: {sorted(boxes_by_sort.keys())}")
        
        # Track position as we pack rows
        current_y = self.BUFFER_RULES['door_clearance']  # Start after door clearance
        row_number = 1
        
        # Process each sort_order group sequentially
        for sort_order in sorted(boxes_by_sort.keys()):
            group_boxes = boxes_by_sort[sort_order]
            
            # Track remaining boxes counts for this group
            remaining_counts = {}
            for box in group_boxes:
                qty = box.get('quantity', 1)
                if qty == 0:
                    continue
                key = (box.get('code', ''), box.get('material', ''), 
                       box.get('purchasing_doc', ''), box.get('packing_method', ''))
                remaining_counts[key] = qty
            
            # Pack rows for this group
            while sum(remaining_counts.values()) > 0:
                # Get available boxes from this group
                available_boxes = []
                for box in group_boxes:
                    key = (box.get('code', ''), box.get('material', ''), 
                           box.get('purchasing_doc', ''), box.get('packing_method', ''))
                    if key in remaining_counts and remaining_counts[key] > 0:
                        box_copy = box.copy()
                        box_copy['quantity'] = remaining_counts[key]
                        available_boxes.append(box_copy)
                
                if not available_boxes:
                    break
                
                total_remaining = sum(remaining_counts.values())
                print(f"Row {row_number}: {len(available_boxes)} box types, {total_remaining} boxes available (sort_order={sort_order})")
                
                # Pack boxes in this row using Z-first strategy
                placed_boxes = self.pack_row_z_first(
                    available_boxes, current_y, self.container['height'], self.container['width']
                )
                
                if not placed_boxes:
                    break
                
                # Remove placed boxes from remaining_counts
                placed_by_type = {}
                for placed_box in placed_boxes:
                    code = placed_box.get('code', 'UNKNOWN')
                    material = placed_box.get('material', '')
                    key = None
                    for orig_box in group_boxes:
                        if orig_box.get('code') == code and orig_box.get('material') == material:
                            key = (orig_box.get('code', ''), orig_box.get('material', ''),
                                   orig_box.get('purchasing_doc', ''), orig_box.get('packing_method', ''))
                            break
                    if key:
                        placed_by_type[key] = placed_by_type.get(key, 0) + 1
                
                for key, count in placed_by_type.items():
                    if key in remaining_counts:
                        remaining_counts[key] -= count
                        if remaining_counts[key] < 0:
                            remaining_counts[key] = 0
                
                print(f"  -> Placed {len(placed_boxes)} boxes")
                print(f"  -> Remaining: {sum(remaining_counts.values())} boxes")
                
                # Add placed boxes to container
                for box in placed_boxes:
                    self.current_container['boxes'].append(box)
                
                # Calculate max height in this row (for visualization only)
                max_z = max(box['position']['z'] + box['dimensions']['height'] 
                           for box in placed_boxes) if placed_boxes else 0
                
                # Calculate actual Y position used by this row
                max_length = max(box['dimensions']['length'] for box in placed_boxes) if placed_boxes else 34.0
                current_y += max_length
                
                print(f"  -> Row height: {max_z:.1f}\" Z-axis, Y position now: {current_y:.1f}\"")
                
                row_number += 1
                
                # Safety check: don't exceed container length
                if current_y >= self.container['length']:
                    print(f"WARNING: Stopping due to container length limit")
                    break
        
        # PHASE 2: Post-processing optimization - move cells from later rows to earlier rows
        self.containers = self.optimize_rows_by_moving_cells(self.containers)
        
        return self.containers
    
    def optimize_rows_by_moving_cells(self, containers: List[Dict]) -> List[Dict]:
        """
        Post-processing: Move cells from later rows to earlier rows if space available
        
        Strategy:
        - Group boxes by rows (based on Y position)
        - For each row, calculate remaining_width = container_width - sum(cell_widths)
        - Scan later rows, find cells that can fit in earlier rows
        - Move boxes (update X positions) from later rows to earlier rows
        
        Args:
            containers: List of containers with packed boxes
            
        Returns:
            List[Dict]: Optimized containers
        """
        if not containers:
            return containers
        
        for container in containers:
            boxes = container.get('boxes', [])
            if not boxes:
                continue
            
            container_width = container['dimensions']['width']
            container_height = container['dimensions']['height']
            
            # Group boxes into rows based on Y position (with tolerance)
            rows_dict = {}
            tolerance_y = 0.5  # Tolerance for grouping by Y
            
            for box in boxes:
                y_pos = box['position']['y']
                # Find existing row or create new one
                row_key = None
                for key in rows_dict.keys():
                    if abs(key - y_pos) <= tolerance_y:
                        row_key = key
                        break
                
                if row_key is None:
                    row_key = y_pos
                    rows_dict[row_key] = []
                
                rows_dict[row_key].append(box)
            
            # Sort rows by Y position (top to bottom)
            sorted_rows_y = sorted(rows_dict.keys())
            
            # Process each row from top to bottom
            for i, row_y in enumerate(sorted_rows_y):
                row_boxes = rows_dict[row_y]
                
                # Calculate row width and remaining space
                if not row_boxes:
                    continue
                
                # Group boxes in this row by X position (cells)
                cells_dict = {}
                tolerance_x = 0.5  # Tolerance for grouping by X
                
                for box in row_boxes:
                    x_pos = box['position']['x']
                    cell_key = None
                    for key in cells_dict.keys():
                        if abs(key - x_pos) <= tolerance_x:
                            cell_key = key
                            break
                    
                    if cell_key is None:
                        cell_key = x_pos
                        cells_dict[cell_key] = []
                    
                    cells_dict[cell_key].append(box)
                
                # Calculate current row width
                max_x_in_row = max(box['position']['x'] + box['dimensions']['width'] 
                                 for box in row_boxes)
                row_width = max_x_in_row
                remaining_width = container_width - row_width
                
                # Only optimize if remaining_width > threshold
                threshold = 10.0  # Minimum remaining width to consider optimization
                if remaining_width < threshold:
                    continue
                
                # Find row max height (for checking if cell can fit)
                row_max_height = max(box['position']['z'] + box['dimensions']['height'] 
                                   for box in row_boxes) if row_boxes else 0
                
                # Scan later rows for cells that can fit
                for j in range(i + 1, len(sorted_rows_y)):
                    later_row_y = sorted_rows_y[j]
                    later_row_boxes = rows_dict.get(later_row_y, [])
                    
                    if not later_row_boxes:
                        continue
                    
                    # Group boxes in later row by X position
                    later_cells_dict = {}
                    for box in later_row_boxes:
                        x_pos = box['position']['x']
                        cell_key = None
                        for key in later_cells_dict.keys():
                            if abs(key - x_pos) <= tolerance_x:
                                cell_key = key
                                break
                        
                        if cell_key is None:
                            cell_key = x_pos
                            later_cells_dict[cell_key] = []
                        
                        later_cells_dict[cell_key].append(box)
                    
                    # Try to move cells from later row
                    cells_to_remove = []
                    for cell_x, cell_boxes in sorted(later_cells_dict.items()):
                        if not cell_boxes:
                            continue
                        
                        # Calculate cell dimensions
                        cell_width = max(box['position']['x'] + box['dimensions']['width'] 
                                       for box in cell_boxes) - min(box['position']['x'] 
                                                                    for box in cell_boxes)
                        cell_height = max(box['position']['z'] + box['dimensions']['height'] 
                                        for box in cell_boxes)
                        
                        # Check if cell can fit in current row
                        if cell_width <= remaining_width and cell_height <= container_height:
                            # Check if cell fits within row height (optional - can be relaxed)
                            if cell_height <= row_max_height or row_max_height == 0:
                                # Move cell to current row
                                new_x = row_width
                                
                                for box in cell_boxes:
                                    # Update X position to append to current row
                                    box['position']['x'] = new_x + (box['position']['x'] - cell_x)
                                    # Update Y position to match current row
                                    box['position']['y'] = row_y
                                    # Z position stays the same (vertical stacking)
                                
                                # Move boxes to current row
                                row_boxes.extend(cell_boxes)
                                cells_to_remove.append(cell_x)
                                
                                # Update row statistics
                                row_width += cell_width
                                remaining_width -= cell_width
                                row_max_height = max(row_max_height, cell_height)
                                
                                print(f"  -> Moved cell (width={cell_width:.1f}\") from row Y={later_row_y:.1f} to row Y={row_y:.1f}")
                    
                    # Remove moved cells from later row
                    for cell_x in cells_to_remove:
                        cells_to_remove_boxes = later_cells_dict[cell_x]
                        later_row_boxes = [b for b in later_row_boxes if b not in cells_to_remove_boxes]
                        rows_dict[later_row_y] = later_row_boxes
                    
                    # Stop if row is full
                    if remaining_width < threshold:
                        break
        
        return containers
    
    def determine_dominant_length(self, boxes: List[Dict]) -> float:
        """
        Determine dominant length for row packing
        
        Strategy: Try các lengths, đếm boxes có thể pack được
        Chọn length cho phép pack NHIỀU BOXES NHẤT (quantity + unique boxes)
        
        Args:
            boxes: List of boxes to analyze
            
        Returns:
            float: Dominant length value
        """
        # Count quantity and unique boxes for each possible length
        length_counts = {}
        for box in boxes:
            for orientation in self.get_all_orientations(box):
                length = orientation['length']
                if length not in length_counts:
                    length_counts[length] = {'count': 0, 'boxes': set()}
                
                # Đếm quantity
                count = box.get('quantity', 1)
                length_counts[length]['count'] += count
                length_counts[length]['boxes'].add(box.get('code', ''))
        
        # Chọn length có thể pack được nhiều boxes nhất
        # Priority: (quantity, number of unique boxes)
        if length_counts:
            most_boxes = max(length_counts.items(), 
                           key=lambda x: (x[1]['count'], len(x[1]['boxes'])))
            return most_boxes[0]
        
        return 34.0  # Default fallback
    
    def pack_row_z_first(self, boxes: List[Dict], row_y: float, container_height: float, 
                         container_width: float) -> List[Dict]:
        """
        Pack row using Z-first strategy
        
        Strategy:
        1. Fill Z-axis first (bottom to top: 0 → 106")
        2. When Z full → increase X (move right), reset Z
        3. When X full → stop (row is full)
        
        This maximizes height utilization before spreading horizontally.
        
        Args:
            boxes: List of boxes to pack
            row_y: Y position for this row
            container_height: Max height (Z-axis)
            container_width: Max width (X-axis)
            
        Returns:
            List[Dict]: Placed boxes
        """
        placed_boxes = []
        
        # Sort boxes by (packing_method_priority, sort_order, quantity, height, area)
        # Priority: PRE_PACK (0) before CARTON (1) - GLOBAL level
        # Then sort by sort_order (ascending) - replaces material + purchasing_doc
        packing_method_priority = {'PRE_PACK': 0, 'CARTON': 1}
        boxes_sorted = sorted(boxes, key=lambda b: (
            packing_method_priority.get(b.get('packing_method', 'CARTON'), 1),  # PRE_PACK=0 first globally
            b.get('sort_order', 999),                                             # sort_order ascending
            -b.get('quantity', 1),                                                # Quantity descending
            b['dimensions']['height'],                                             # Height for better stacking
            -(b['dimensions']['width'] * b['dimensions']['length']),               # Area descending
        ))
        
        # Determine dominant length for this row
        dominant_length = self.determine_dominant_length(boxes_sorted)
        
        # Expand all boxes by quantity
        expanded_boxes = []
        for box in boxes_sorted:
            qty = int(box.get('quantity', 1))
            if qty <= 0:
                continue
            for _ in range(qty):
                expanded_boxes.append(box.copy())
        
        # Filter boxes: Only keep boxes that have orientations matching dominant_length
        # This ensures row consistency - all cells use same length
        tolerance = 1.0  # inches - allow small deviation
        filtered_boxes = []
        for box in expanded_boxes:
            valid_orientations = []
            best_match = None
            
            # Try to find exact match first, then closest match within tolerance
            for orientation in self.get_all_orientations(box):
                length_diff = abs(orientation['length'] - dominant_length)
                
                if orientation['length'] == dominant_length:
                    # Exact match - prefer this
                    valid_orientations.append(orientation)
                elif length_diff <= tolerance and (best_match is None or length_diff < abs(best_match['length'] - dominant_length)):
                    best_match = orientation
            
            # If have exact matches, use them
            if valid_orientations:
                filtered_boxes.append(box)
            elif best_match:
                # Use closest match within tolerance
                filtered_boxes.append(box)
        
        # Update expanded_boxes to use filtered list
        expanded_boxes = filtered_boxes
        
        # Track position in row - START FILLING Z FIRST
        current_x = 0.0
        current_z = 0.0
        column_max_width = 0.0  # Track max width in current column
        
        for box in expanded_boxes:
            # PHASE 1 FIX: Check if row is full BEFORE trying to pack box
            if current_x >= container_width:
                break  # Row is truly full - no more space
            
            # Calculate average dimensions from placed boxes
            if placed_boxes:
                avg_length = sum(b['dimensions']['length'] for b in placed_boxes) / len(placed_boxes)
                avg_width = sum(b['dimensions']['width'] for b in placed_boxes) / len(placed_boxes)
            else:
                # First box in row - use dominant_length as initial target
                avg_length = dominant_length
                avg_width = None
            
            best_orientation = None
            best_score = float('inf')
            fits_current = False
            
            # Try all orientations and pick the one with minimum deviation from average dimensions
            # FILTER: Only consider orientations that match dominant_length (with tolerance)
            for orientation in self.get_all_orientations(box):
                box_l = orientation['length']
                # Only consider orientations matching dominant_length
                if abs(box_l - dominant_length) > tolerance:
                    continue
                
                box_w = orientation['width']
                box_h = orientation['height']  # Z-axis height
                
                # Check if fits in container dimensions
                if box_w > container_width or box_h > container_height:
                    continue
                
                # Check if fits at current position (KEY: check Z first!)
                if current_z + box_h <= container_height and current_x + box_w <= container_width:
                    # Calculate deviation from average dimensions
                    if avg_width is not None:
                        # Both length and width known - match both
                        length_dev = abs(box_l - avg_length)
                        width_dev = abs(box_w - avg_width)
                        deviation = length_dev + width_dev
                    else:
                        # Only length known (first box) - match length, prefer larger width
                        deviation = abs(box_l - avg_length)
                        # Tie-break: prefer larger width
                        if deviation == 0:
                            deviation -= box_w * 0.01  # Small bonus for larger width
                    
                    # Choose orientation with minimum deviation
                    if deviation < best_score:
                        best_orientation = orientation
                        best_score = deviation
                        fits_current = True
            
            # If doesn't fit at current Z position, move to next column (X)
            if not fits_current:
                current_x += column_max_width
                current_z = 0.0
                column_max_width = 0.0
                
                # Try again at new column
                for orientation in self.get_all_orientations(box):
                    box_l = orientation['length']
                    # Only consider orientations matching dominant_length
                    if abs(box_l - dominant_length) > tolerance:
                        continue
                    
                    box_w = orientation['width']
                    box_h = orientation['height']
                    
                    if box_w > container_width or box_h > container_height:
                        continue
                    
                    if current_z + box_h <= container_height and current_x + box_w <= container_width:
                        # Calculate deviation from average dimensions
                        if avg_width is not None:
                            length_dev = abs(box_l - avg_length)
                            width_dev = abs(box_w - avg_width)
                            deviation = length_dev + width_dev
                        else:
                            deviation = abs(box_l - avg_length)
                            if deviation == 0:
                                deviation -= box_w * 0.01
                        
                        # Choose orientation with minimum deviation
                        if deviation < best_score:
                            best_orientation = orientation
                            best_score = deviation
                            fits_current = True
            
            # Place box if we found a fit
            if best_orientation and fits_current:
                placed_box = {
                    'code': box.get('code', 'UNKNOWN'),
                    'dimensions': best_orientation,
                    'position': {
                        'x': current_x,
                        'y': row_y,
                        'z': current_z
                    },
                    'material': box.get('material', ''),
                    'packing_method': box.get('packing_method', 'CARTON')
                }
                placed_boxes.append(placed_box)
                
                # Update position for next box
                box_w = best_orientation['width']
                box_h = best_orientation['height']
                
                # KEY: Increase Z first (stack up)
                current_z += box_h
                column_max_width = max(column_max_width, box_w)
                
                # If Z exceeds height, move to next column (X)
                if current_z >= container_height:
                    current_x += column_max_width
                    current_z = 0.0
                    column_max_width = 0.0
                    
                    # PHASE 1 FIX: Check if row is full after moving to next column
                    if current_x >= container_width:
                        break  # Row is full after column move
            else:
                # PHASE 1 FIX: Box doesn't fit - SKIP it and continue with next box
                # Instead of breaking early, we skip this box and try the next one
                # This allows the row to fill more completely before moving to next row
                continue
        
        return placed_boxes
    
    def get_all_orientations(self, box: Dict) -> List[Dict]:
        """
        Generate tất cả orientations hợp lệ cho box
        
        CARTON: 2 orientations (luôn đứng, chỉ xoay trái/phải)
        PRE_PACK: 2-4 orientations (mặt width×height không chạm sàn)
                  - Swap orientations (L×H, W) và (H×L, W) chỉ hợp lệ khi Height > Length
        
        Args:
            box: Box dict with dimensions and packing_method
            
        Returns:
            List[Dict]: [{width, length, height}, ...]
        """
        w, l, h = box['dimensions']['width'], box['dimensions']['length'], box['dimensions']['height']
        packing_method = box.get('packing_method', 'CARTON')
        
        if packing_method == 'PRE_PACK':
            # PRE_PACK: Luôn cho phép 2 orientations cơ bản
            orientations = [
                {'width': w, 'length': l, 'height': h},  # (W×L, H) - Always allowed
                {'width': l, 'length': w, 'height': h},  # (L×W, H) - Always allowed
            ]
            
            # Only add swap orientations if Height > Length
            if h > l:
                orientations.append({'width': l, 'length': h, 'height': w})  # (L×H, W)
                orientations.append({'width': h, 'length': l, 'height': w})  # (H×L, W)
            
            return orientations
        else:
            # CARTON: 2 orientations - luôn đứng theo height, chỉ xoay trái/phải
            return [
                {'width': w, 'length': l, 'height': h},  # Đứng, hướng gốc
                {'width': l, 'length': w, 'height': h}   # Đứng, xoay 90°
            ]
