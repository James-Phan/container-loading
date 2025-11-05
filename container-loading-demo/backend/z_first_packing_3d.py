"""
Z-First Packing Algorithm - Fill height (Z-axis) before width (X-axis)

Strategy:
1. Pack boxes stacking vertically (Z-axis: 0→106") before moving horizontally (X-axis: 0→92.5")
2. Maximize height utilization at each X position
3. When Z axis is full, move to next X position
4. Create rows dynamically based on available boxes
"""

from typing import List, Dict, Any
from collections import Counter
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
        
        # OPTION A - PHASE 1: Global Row Planning (Simplified)
        # Instead of processing each sort_order group separately, use "wait and pack more" strategy
        # This allows combining boxes from different groups into same row when possible
        
        # Track position as we pack rows
        current_y = self.BUFFER_RULES['door_clearance']  # Start after door clearance
        row_number = 1
        
        # Track all remaining boxes across all sort_order groups
        all_remaining_counts = {}
        for sort_order in sorted(boxes_by_sort.keys()):
            group_boxes = boxes_by_sort[sort_order]
            for box in group_boxes:
                qty = box.get('quantity', 1)
                if qty == 0:
                    continue
                key = (box.get('code', ''), box.get('material', ''), 
                       box.get('purchasing_doc', ''), box.get('packing_method', ''))
                all_remaining_counts[key] = all_remaining_counts.get(key, 0) + qty
        
        # OPTION A - PHASE 1: Process rows with global view
        # While there are boxes remaining, try to pack rows optimally
        processed_sort_orders = set()
        
        while sum(all_remaining_counts.values()) > 0:
            # OPTION A - PHASE 1: Get available boxes from ALL sort_order groups (prioritize unprocessed)
            # Priority: Process sort_order groups in order, but allow adding boxes from other groups
            available_boxes = []
            current_sort_order = None
            
            # First, try to get boxes from unprocessed sort_order groups (in order)
            for sort_order in sorted(boxes_by_sort.keys()):
                if sort_order in processed_sort_orders:
                    continue  # Already processed this group
                
                group_boxes = boxes_by_sort[sort_order]
                group_remaining = {}
                
                for box in group_boxes:
                    key = (box.get('code', ''), box.get('material', ''), 
                           box.get('purchasing_doc', ''), box.get('packing_method', ''))
                    if key in all_remaining_counts and all_remaining_counts[key] > 0:
                        group_remaining[key] = all_remaining_counts[key]
                
                if group_remaining:
                    current_sort_order = sort_order
                    # Add boxes from this group
                    for box in group_boxes:
                        key = (box.get('code', ''), box.get('material', ''), 
                               box.get('purchasing_doc', ''), box.get('packing_method', ''))
                        if key in group_remaining and group_remaining[key] > 0:
                            box_copy = box.copy()
                            box_copy['quantity'] = group_remaining[key]
                            available_boxes.append(box_copy)
                    break  # Use first unprocessed group
            
            # OPTION A - PHASE 1: If no boxes from unprocessed groups, try processed groups
            if not available_boxes:
                # No more boxes from unprocessed groups, try processed groups
                for sort_order in sorted(boxes_by_sort.keys()):
                    group_boxes = boxes_by_sort[sort_order]
                    for box in group_boxes:
                        key = (box.get('code', ''), box.get('material', ''), 
                               box.get('purchasing_doc', ''), box.get('packing_method', ''))
                        if key in all_remaining_counts and all_remaining_counts[key] > 0:
                            box_copy = box.copy()
                            box_copy['quantity'] = all_remaining_counts[key]
                            available_boxes.append(box_copy)
                            if current_sort_order is None:
                                current_sort_order = sort_order
                            if len(available_boxes) >= 10:  # Limit to avoid too many
                                break
                    if len(available_boxes) >= 10:
                        break
            
            if not available_boxes:
                break
            
            total_remaining = sum(all_remaining_counts.values())
            sort_order_str = f"sort_order={current_sort_order}" if current_sort_order else "mixed"
            print(f"Row {row_number}: {len(available_boxes)} box types, {total_remaining} boxes available ({sort_order_str})")
            
            # Pack boxes in this row using Z-first strategy
            # OPTION C: Pass all_remaining_boxes to pack_row_z_first for enhanced gap filling
            placed_boxes = self.pack_row_z_first(
                available_boxes, current_y, self.container['height'], self.container['width'],
                all_remaining_boxes=self.get_all_remaining_boxes_list(all_remaining_counts, boxes_by_sort)
            )
            
            if not placed_boxes:
                # Mark current sort_order as processed if no boxes placed
                if current_sort_order:
                    processed_sort_orders.add(current_sort_order)
                break
            
            # Calculate dominant_length and tolerance from placed_boxes for gap filling
            # Get dominant length from placed boxes (most common length)
            if placed_boxes:
                length_counts = {}
                for box in placed_boxes:
                    box_l = box['dimensions']['length']
                    length_counts[box_l] = length_counts.get(box_l, 0) + 1
                dominant_length = max(length_counts.items(), key=lambda x: x[1])[0] if length_counts else 34.0
                tolerance = 2.0  # Default tolerance for gap filling
            else:
                dominant_length = 34.0
                tolerance = 2.0
            
            # Check row width utilization - if low, try adding more boxes from other groups
            max_x = max(box['position']['x'] + box['dimensions']['width'] 
                       for box in placed_boxes) if placed_boxes else 0
            width_utilization = (max_x / self.container['width'] * 100) if self.container['width'] > 0 else 0.0
            
            # OPTION A - PHASE 1: If width utilization < 80%, try to add more boxes from other groups
            if width_utilization < 80.0:
                # Try to add boxes from other sort_order groups
                additional_boxes = []
                for sort_order in sorted(boxes_by_sort.keys()):
                    if sort_order == current_sort_order:
                        continue  # Skip current group
                    group_boxes = boxes_by_sort[sort_order]
                    for box in group_boxes:
                        key = (box.get('code', ''), box.get('material', ''), 
                               box.get('purchasing_doc', ''), box.get('packing_method', ''))
                        if key in all_remaining_counts and all_remaining_counts[key] > 0:
                            box_copy = box.copy()
                            box_copy['quantity'] = min(all_remaining_counts[key], 10)  # Limit to avoid too many
                            additional_boxes.append(box_copy)
                            if len(additional_boxes) >= 5:  # Limit additional boxes
                                break
                    if len(additional_boxes) >= 5:
                        break
                
                if additional_boxes:
                    # OPTION A - PHASE 1 FIX: Use fill_row_gaps() instead of pack_row_z_first()
                    # This merges boxes into gaps of existing row instead of creating new row
                    placed_boxes = self.fill_row_gaps(
                        placed_boxes, additional_boxes, current_y,
                        self.container['width'], self.container['height'],
                        dominant_length, tolerance
                    )
                    print(f"  -> Filled row gaps with {len([b for b in placed_boxes if b not in placed_boxes[:len(placed_boxes)-len(additional_boxes)]])} boxes from other groups")
            
            # Check if row is too short and retry with alternative dominant_length
            max_z = max(box['position']['z'] + box['dimensions']['height']
                       for box in placed_boxes) if placed_boxes else 0
            
            if max_z < self.container['height'] * 0.5 and len(placed_boxes) < len(available_boxes) * 0.3:
                print(f"  WARNING: Row too short ({max_z:.1f}\"), retrying with alternative dominant_length")
                # Get top dominant_length candidates
                top_lengths = self.get_top_dominant_lengths(available_boxes, top_n=3)
                # Skip first (already tried), try alternatives
                retried = False
                for alt_length in top_lengths[1:]:  # Skip first (already tried)
                    print(f"  -> Retrying with dominant_length={alt_length:.1f}\"")
                    placed_boxes_retry = self.pack_row_z_first(
                        available_boxes, current_y, self.container['height'], self.container['width'],
                        dominant_length=alt_length
                    )
                    if placed_boxes_retry:
                        max_z_retry = max(box['position']['z'] + box['dimensions']['height']
                                        for box in placed_boxes_retry)
                        # Accept retry if it's better (higher or more boxes)
                        if max_z_retry > max_z or len(placed_boxes_retry) > len(placed_boxes):
                            placed_boxes = placed_boxes_retry
                            max_z = max_z_retry
                            retried = True
                            print(f"  -> Retry successful: height={max_z:.1f}\", boxes={len(placed_boxes)}")
                            break
                if not retried:
                    print(f"  -> Retry did not improve, keeping original result")
            
            # Remove placed boxes from all_remaining_counts
            placed_by_type = {}
            for placed_box in placed_boxes:
                code = placed_box.get('code', 'UNKNOWN')
                material = placed_box.get('material', '')
                key = None
                for sort_order in sorted(boxes_by_sort.keys()):
                    group_boxes = boxes_by_sort[sort_order]
                    for orig_box in group_boxes:
                        if orig_box.get('code') == code and orig_box.get('material') == material:
                            key = (orig_box.get('code', ''), orig_box.get('material', ''),
                                   orig_box.get('purchasing_doc', ''), orig_box.get('packing_method', ''))
                            break
                    if key:
                        break
                
                if key:
                    placed_by_type[key] = placed_by_type.get(key, 0) + 1
            
            for key, count in placed_by_type.items():
                if key in all_remaining_counts:
                    all_remaining_counts[key] -= count
                    if all_remaining_counts[key] < 0:
                        all_remaining_counts[key] = 0
            
            print(f"  -> Placed {len(placed_boxes)} boxes")
            print(f"  -> Remaining: {sum(all_remaining_counts.values())} boxes")
            
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
            
            # Mark current sort_order as processed if all boxes from that group are placed
            if current_sort_order:
                group_remaining = sum(all_remaining_counts.get(
                    (box.get('code', ''), box.get('material', ''), 
                     box.get('purchasing_doc', ''), box.get('packing_method', '')), 0)
                    for box in boxes_by_sort[current_sort_order])
                if group_remaining == 0:
                    processed_sort_orders.add(current_sort_order)
            
            # Safety check: don't exceed container length
            if current_y >= self.container['length']:
                print(f"WARNING: Stopping due to container length limit")
                break
        
        # PHASE 2: Post-processing optimization - move cells from later rows to earlier rows
        self.containers = self.optimize_rows_by_moving_cells(self.containers)
        
        # PHASE 3: Post-processing cell-level height optimization
        self.containers = self.optimize_cell_heights(self.containers)
        
        # PHASE 4: Post-processing width utilization optimization
        self.containers = self.optimize_row_width_utilization(self.containers)
        
        # OPTION A - PHASE 3: Row Consolidation
        self.containers = self.consolidate_rows(self.containers)
        
        # Re-optimize after consolidation
        self.containers = self.optimize_cell_heights(self.containers)
        self.containers = self.optimize_row_width_utilization(self.containers)
        
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
                threshold = 5.0  # Minimum remaining width to consider optimization (reduced from 10.0)
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
                        # Relaxed condition: only check container_height (removed row_max_height restriction)
                        if cell_width <= remaining_width and cell_height <= container_height:
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
    
    def optimize_cell_heights(self, containers: List[Dict]) -> List[Dict]:
        """
        Post-processing: Fill incomplete cells by moving boxes from later rows
        
        Strategy:
        - Group boxes by rows (Y position) and cells (X position)
        - Identify incomplete cells (< 80% height) in each row
        - Try to move boxes from later rows into incomplete cells
        - Only move if boxes fit AND improve cell height utilization
        
        Args:
            containers: List of containers with packed boxes
            
        Returns:
            List[Dict]: Optimized containers with improved cell heights
        """
        if not containers:
            return containers
        
        for container in containers:
            boxes = container.get('boxes', [])
            if not boxes:
                continue
            
            container_height = container['dimensions']['height']
            
            # Group boxes into rows based on Y position
            rows_dict = {}
            tolerance_y = 0.5
            
            for box in boxes:
                y_pos = box['position']['y']
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
                
                # OPTION A - PHASE 2.3: Enhance optimize_cell_heights - change threshold to 0.95 (95%)
                # Detect incomplete cells in this row
                incomplete_cells = self.detect_incomplete_cells(
                    row_boxes, container_height, threshold=0.95
                )
                
                if not incomplete_cells:
                    continue  # All cells are complete, skip
                
                # OPTION A - PHASE 2.3: Search boxes from ALL rows, not just later rows
                # Also search from earlier rows (reverse order) to fill cells more aggressively
                all_row_indices = list(range(len(sorted_rows_y)))
                # Try later rows first (original logic), then earlier rows
                search_order = list(range(i + 1, len(sorted_rows_y))) + list(range(i - 1, -1, -1))
                
                for j in search_order:
                    if j == i:
                        continue  # Skip current row
                    
                    other_row_y = sorted_rows_y[j]
                    other_row_boxes = rows_dict.get(other_row_y, [])
                    
                    if not other_row_boxes:
                        continue
                    
                    # OPTION A - PHASE 2.3: Prefer smallest boxes to fill gaps
                    # Sort boxes by height (ascending) to prefer smallest boxes
                    other_row_boxes_sorted = sorted(other_row_boxes,
                                                   key=lambda b: min(orient['height'] 
                                                                   for orient in self.get_all_orientations(b)))
                    
                    # Try to move boxes from other row to incomplete cells
                    boxes_to_move = []
                    for incomplete_cell in incomplete_cells:
                        if incomplete_cell['remaining_height'] < 3.0:  # Reduced from 5.0
                            continue  # Skip if too little space
                        
                        # Find boxes from other row that can fit in incomplete cell
                        for box in other_row_boxes_sorted:
                            if box in [b['box'] for b in boxes_to_move]:
                                continue  # Already marked for moving
                            
                            # Check all orientations
                            for orientation in self.get_all_orientations(box):
                                box_h = orientation['height']
                                box_w = orientation['width']
                                
                                # Check if fits in incomplete cell
                                if (box_h <= incomplete_cell['remaining_height'] and
                                    box_w <= incomplete_cell['width']):
                                    # Can fit - mark for moving
                                    boxes_to_move.append({
                                        'box': box,
                                        'cell': incomplete_cell,
                                        'orientation': orientation,
                                        'target_z': incomplete_cell['height']
                                    })
                                    # Update cell height for next boxes
                                    incomplete_cell['height'] += box_h
                                    incomplete_cell['remaining_height'] -= box_h
                                    break
                        
                        # OPTION A - PHASE 2.3: Continue until cell is full (95%+) or no boxes fit
                        if incomplete_cell['remaining_height'] < 3.0:
                            incomplete_cells = [c for c in incomplete_cells 
                                              if c['remaining_height'] >= 3.0]
                            if not incomplete_cells:
                                break
                    
                    # Move boxes to current row cells
                    if boxes_to_move:
                        for move_info in boxes_to_move:
                            box = move_info['box']
                            cell = move_info['cell']
                            orientation = move_info['orientation']
                            target_z = move_info['target_z']
                            
                            # Update box position and dimensions
                            box['position']['x'] = cell['x']
                            box['position']['y'] = row_y
                            box['position']['z'] = target_z
                            box['dimensions'] = orientation
                            
                            # Move box to current row
                            row_boxes.append(box)
                            other_row_boxes.remove(box)
                            
                            print(f"  -> Moved box to fill cell: height={orientation['height']:.1f}\" "
                                  f"from row Y={other_row_y:.1f} to cell at Y={row_y:.1f}, X={cell['x']:.1f}")
                        
                        # Update rows_dict
                        rows_dict[other_row_y] = other_row_boxes
                        rows_dict[row_y] = row_boxes
                        
                        if not incomplete_cells:
                            break  # All cells filled, move to next row
        
        return containers
    
    def get_all_remaining_boxes_list(self, all_remaining_counts: Dict, boxes_by_sort: Dict) -> List[Dict]:
        """
        OPTION C: Get all remaining boxes from all sort_order groups
        
        Args:
            all_remaining_counts: Dictionary tracking remaining counts by box key
            boxes_by_sort: Dictionary grouping boxes by sort_order
            
        Returns:
            List of all remaining boxes (expanded by quantity)
        """
        all_remaining = []
        for sort_order in sorted(boxes_by_sort.keys()):
            group_boxes = boxes_by_sort[sort_order]
            for box in group_boxes:
                key = (box.get('code', ''), box.get('material', ''), 
                       box.get('purchasing_doc', ''), box.get('packing_method', ''))
                if key in all_remaining_counts and all_remaining_counts[key] > 0:
                    qty = all_remaining_counts[key]
                    for _ in range(qty):
                        all_remaining.append(box.copy())
        return all_remaining
    
    def detect_width_gaps(self, placed_boxes: List[Dict], container_width: float) -> List[Dict]:
        """
        OPTION A: Detect gaps in row based on placed boxes
        
        Args:
            placed_boxes: List of boxes already placed in row
            container_width: Container width
            
        Returns:
            List of gaps: [{'x': start_x, 'width': gap_width}, ...]
        """
        if not placed_boxes:
            return [{'x': 0.0, 'width': container_width}]
        
        # Sort boxes by X position
        boxes_sorted = sorted(placed_boxes, key=lambda b: b['position']['x'])
        
        gaps = []
        current_x = 0.0
        
        for box in boxes_sorted:
            box_x = box['position']['x']
            box_width = box['dimensions']['width']
            
            # Gap before this box
            if box_x > current_x:
                gaps.append({
                    'x': current_x,
                    'width': box_x - current_x
                })
            
            current_x = max(current_x, box_x + box_width)
        
        # Gap after last box
        if current_x < container_width:
            gaps.append({
                'x': current_x,
                'width': container_width - current_x
            })
        
        return gaps
    
    def fill_row_gaps(self, placed_boxes: List[Dict], additional_boxes: List[Dict],
                      row_y: float, container_width: float, container_height: float,
                      dominant_length: float, tolerance: float) -> List[Dict]:
        """
        OPTION A: Fill gaps in existing row with additional boxes
        
        Strategy:
        - Detect gaps in row (spaces between cells)
        - Try to pack additional boxes into gaps
        - Maintain sort_order priority
        
        Args:
            placed_boxes: List of boxes already placed in row
            additional_boxes: List of boxes to add to gaps
            row_y: Y position of row
            container_width: Container width
            container_height: Container height
            dominant_length: Dominant length for row
            tolerance: Length tolerance
            
        Returns:
            Updated placed_boxes with additional boxes filled in gaps
        """
        if not additional_boxes:
            return placed_boxes
        
        # Detect gaps
        gaps = self.detect_width_gaps(placed_boxes, container_width)
        
        if not gaps:
            return placed_boxes  # No gaps to fill
        
        # Sort gaps by size (largest first)
        gaps_sorted = sorted(gaps, key=lambda g: g['width'], reverse=True)
        
        # Create a copy of additional_boxes to modify
        remaining_boxes = additional_boxes[:]
        
        # Try to fill each gap
        for gap in gaps_sorted:
            if gap['width'] < 5.0:  # Skip small gaps
                continue
            
            # Find boxes that fit in gap
            for box in remaining_boxes[:]:  # Copy list to modify during iteration
                best_orientation = None
                best_fit_width = 0
                
                for orientation in self.get_all_orientations(box):
                    box_w = orientation['width']
                    box_l = orientation['length']
                    box_h = orientation['height']
                    
                    # Check if fits in gap (relaxed constraints for gap filling)
                    if (box_w <= gap['width'] and
                        abs(box_l - dominant_length) <= tolerance * 2.0 and  # Relaxed for gap filling
                        box_h <= container_height):
                        if box_w > best_fit_width:
                            best_orientation = orientation
                            best_fit_width = box_w
                
                if best_orientation:
                    # Place box in gap
                    placed_box = {
                        'code': box.get('code', 'UNKNOWN'),
                        'dimensions': best_orientation,
                        'position': {
                            'x': gap['x'],
                            'y': row_y,
                            'z': 0.0  # Start at bottom, will stack later if needed
                        },
                        'material': box.get('material', ''),
                        'packing_method': box.get('packing_method', 'CARTON')
                    }
                    placed_boxes.append(placed_box)
                    remaining_boxes.remove(box)
                    
                    # Update gap
                    gap['x'] += best_fit_width
                    gap['width'] -= best_fit_width
                    
                    if gap['width'] < 5.0:
                        break  # Gap filled
            
            # If no more boxes fit, break
            if not remaining_boxes:
                break
        
        return placed_boxes
    
    def consolidate_rows(self, containers: List[Dict]) -> List[Dict]:
        """
        OPTION A - PHASE 3: Row Consolidation
        
        After packing, consolidate rows to minimize number of rows.
        Merge rows if can combine without breaking constraints.
        
        Strategy:
        - Scan all rows after packing
        - For each row pair (i, j) where i < j:
          - Check if can merge row j into row i
          - Calculate total width if merge: sum(widths) ≤ container_width?
          - Calculate total height: max(heights) ≤ container_height?
          - Check sort_order compatibility
        - If mergeable: Merge row j into row i, remove row j
        
        Args:
            containers: List of containers with packed boxes
            
        Returns:
            List[Dict]: Consolidated containers with minimized rows
        """
        if not containers:
            return containers
        
        for container in containers:
            boxes = container.get('boxes', [])
            if not boxes:
                continue
            
            container_width = container['dimensions']['width']
            container_height = container['dimensions']['height']
            
            # Group boxes into rows based on Y position
            rows_dict = {}
            tolerance_y = 0.5
            
            for box in boxes:
                y_pos = box['position']['y']
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
            
            # OPTION A - PHASE 3: Try to merge rows
            rows_merged = True
            iteration = 0
            max_iterations = len(sorted_rows_y)  # Prevent infinite loop
            
            while rows_merged and iteration < max_iterations:
                rows_merged = False
                iteration += 1
                
                # Try to merge each row pair
                for i in range(len(sorted_rows_y) - 1):
                    if i >= len(sorted_rows_y) - 1:
                        break
                    
                    row_i_y = sorted_rows_y[i]
                    row_i_boxes = rows_dict[row_i_y]
                    
                    if not row_i_boxes:
                        continue
                    
                    # Calculate row i dimensions
                    row_i_max_x = max(box['position']['x'] + box['dimensions']['width'] 
                                     for box in row_i_boxes)
                    row_i_max_z = max(box['position']['z'] + box['dimensions']['height'] 
                                     for box in row_i_boxes)
                    row_i_width = row_i_max_x
                    
                    # Try to merge with later rows
                    for j in range(i + 1, len(sorted_rows_y)):
                        if j >= len(sorted_rows_y):
                            break
                        
                        row_j_y = sorted_rows_y[j]
                        row_j_boxes = rows_dict[row_j_y]
                        
                        if not row_j_boxes:
                            continue
                        
                        # Calculate row j dimensions
                        row_j_max_x = max(box['position']['x'] + box['dimensions']['width'] 
                                         for box in row_j_boxes)
                        row_j_max_z = max(box['position']['z'] + box['dimensions']['height'] 
                                         for box in row_j_boxes)
                        row_j_width = row_j_max_x
                        
                        # Check if can merge:
                        # 1. Total width ≤ container_width
                        total_width = row_i_width + row_j_width
                        if total_width > container_width:
                            continue
                        
                        # 2. Max height ≤ container_height
                        max_height = max(row_i_max_z, row_j_max_z)
                        if max_height > container_height:
                            continue
                        
                        # 3. Check sort_order compatibility (simplified - allow merge if compatible)
                        # For now, allow merge if rows have similar structure
                        # TODO: Add more sophisticated sort_order compatibility check
                        
                        # Merge row j into row i
                        # Update X positions of row j boxes to append to row i
                        for box in row_j_boxes:
                            box['position']['x'] += row_i_width
                            box['position']['y'] = row_i_y  # Move to row i Y position
                            # Z position stays the same
                        
                        # Move boxes from row j to row i
                        row_i_boxes.extend(row_j_boxes)
                        rows_dict[row_i_y] = row_i_boxes
                        del rows_dict[row_j_y]
                        
                        # Remove row j from sorted list
                        sorted_rows_y.remove(row_j_y)
                        
                        rows_merged = True
                        print(f"  -> Merged row Y={row_j_y:.1f}\" into row Y={row_i_y:.1f}\" "
                              f"(total width: {total_width:.1f}\", height: {max_height:.1f}\")")
                        
                        break  # Break inner loop to restart from beginning
                    
                    if rows_merged:
                        break  # Break outer loop to restart from beginning
        
        return containers
    
    def optimize_row_width_utilization(self, containers: List[Dict]) -> List[Dict]:
        """
        Post-processing: Improve width utilization by moving boxes into gaps
        
        Strategy:
        - Group boxes by rows (Y position)
        - For each row, calculate width utilization
        - If < 90%, try to move boxes from later rows into gaps
        - Only move if improves overall utilization
        
        Args:
            containers: List of containers with packed boxes
            
        Returns:
            List[Dict]: Optimized containers with improved width utilization
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
            tolerance_y = 0.5
            
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
            
            # IMPROVEMENT 3.1: Sort rows by width utilization (lowest first) to prioritize optimization
            # This ensures Row 2, 4, 6 (with lowest utilization) are optimized first
            rows_with_utilization = []
            for row_y, row_boxes in rows_dict.items():
                if not row_boxes:
                    continue
                max_x = max(box['position']['x'] + box['dimensions']['width'] 
                           for box in row_boxes)
                width_utilization = (max_x / container_width * 100) if container_width > 0 else 0.0
                remaining_width = container_width - max_x
                rows_with_utilization.append({
                    'y': row_y,
                    'boxes': row_boxes,
                    'width_utilization': width_utilization,
                    'remaining_width': remaining_width
                })
            
            # Sort by width utilization (lowest first), then by remaining_width (largest first)
            rows_with_utilization.sort(key=lambda r: (r['width_utilization'], -r['remaining_width']))
            
            # Process rows with lowest width utilization first
            for row_info in rows_with_utilization:
                row_y = row_info['y']
                row_boxes = row_info['boxes']
                width_utilization = row_info['width_utilization']
                remaining_width = row_info['remaining_width']
                
                # Only optimize if width utilization < 90%
                if width_utilization >= 90.0:
                    continue
                
                # Only optimize if remaining_width > threshold
                threshold = 5.0
                if remaining_width < threshold:
                    continue
                
                print(f"  -> Row Y={row_y:.1f}\" width utilization {width_utilization:.1f}% < 90%, "
                      f"remaining width: {remaining_width:.1f}\"")
                
                # Find row index in sorted_rows_y for scanning later rows
                sorted_rows_y = sorted(rows_dict.keys())
                i = sorted_rows_y.index(row_y)
                row_width = max(box['position']['x'] + box['dimensions']['width'] 
                               for box in row_boxes)
                
                # Scan later rows for boxes that can fit in gap
                boxes_moved = []
                for j in range(i + 1, len(sorted_rows_y)):
                    later_row_y = sorted_rows_y[j]
                    later_row_boxes = rows_dict.get(later_row_y, [])
                    
                    if not later_row_boxes:
                        continue
                    
                    # Try to move boxes from later row into gap
                    for box in later_row_boxes[:]:  # Copy list to modify during iteration
                        if remaining_width < threshold:
                            break
                        
                        best_orientation = None
                        best_width = 0
                        
                        # Check all orientations for this box
                        for orientation in self.get_all_orientations(box):
                            box_w = orientation['width']
                            box_h = orientation['height']
                            
                            # Check if fits in remaining gap
                            if box_w <= remaining_width and box_h <= container_height:
                                # Prefer larger width to maximize utilization
                                if box_w > best_width:
                                    best_orientation = orientation
                                    best_width = box_w
                        
                        if best_orientation:
                            # Move box to current row gap
                            box['position']['x'] = row_width
                            box['position']['y'] = row_y
                            box['position']['z'] = 0.0  # Start new column at bottom
                            box['dimensions'] = best_orientation
                            
                            # Move box to current row
                            row_boxes.append(box)
                            later_row_boxes.remove(box)
                            boxes_moved.append(box)
                            
                            # Update row statistics
                            row_width += best_width
                            remaining_width -= best_width
                            
                            print(f"    -> Moved box {box.get('code', 'UNKNOWN')} "
                                  f"(width={best_width:.1f}\") from row Y={later_row_y:.1f} "
                                  f"to gap at Y={row_y:.1f}, remaining: {remaining_width:.1f}\"")
                    
                    # Update rows_dict
                    rows_dict[later_row_y] = later_row_boxes
                    rows_dict[row_y] = row_boxes
                    
                    if remaining_width < threshold:
                        break
                
                if boxes_moved:
                    new_max_x = max(box['position']['x'] + box['dimensions']['width'] 
                                   for box in row_boxes)
                    new_width_utilization = (new_max_x / container_width * 100) if container_width > 0 else 0.0
                    print(f"  -> Row Y={row_y:.1f}\" width utilization improved: "
                          f"{width_utilization:.1f}% -> {new_width_utilization:.1f}%")
                    
                    # Update rows_dict to reflect changes
                    rows_dict[row_y] = row_boxes
        
        return containers
    
    def determine_dominant_length(self, boxes: List[Dict], container_width: float = None) -> float:
        """
        Determine dominant length for row packing
        
        MEDIUM PRIORITY 2: Width-Aware Selection
        Strategy: Chọn length cho phép maximize width utilization, không chỉ box count
        
        Args:
            boxes: List of boxes to analyze
            container_width: Optional container width for width utilization calculation
            
        Returns:
            float: Dominant length value
        """
        # Count quantity and unique boxes for each possible length
        length_counts = {}
        length_width_data = {}  # Store width data for each length
        
        for box in boxes:
            for orientation in self.get_all_orientations(box):
                length = orientation['length']
                width = orientation['width']
                
                if length not in length_counts:
                    length_counts[length] = {'count': 0, 'boxes': set()}
                    length_width_data[length] = {'widths': [], 'total_width': 0.0}
                
                # Đếm quantity
                count = box.get('quantity', 1)
                length_counts[length]['count'] += count
                length_counts[length]['boxes'].add(box.get('code', ''))
                
                # Store width data (for each box instance)
                for _ in range(count):
                    length_width_data[length]['widths'].append(width)
                    length_width_data[length]['total_width'] += width
        
        if not length_counts:
            return 34.0  # Default fallback
        
        # MEDIUM PRIORITY 2: Calculate width utilization score for each length
        if container_width and container_width > 0:
            length_scores = {}
            
            for length, count_data in length_counts.items():
                box_count = count_data['count']
                unique_boxes = len(count_data['boxes'])
                
                # Calculate width utilization
                widths = sorted(length_width_data[length]['widths'], reverse=True)
                total_width = sum(widths)
                
                # Estimate width utilization (simplified: sum of widths / container_width)
                # In reality, boxes are placed side by side, so we calculate how many fit
                estimated_width_util = min(100.0, (total_width / container_width) * 100)
                
                # Normalize box count score (0-1 scale)
                max_count = max(lc['count'] for lc in length_counts.values())
                box_count_score = box_count / max_count if max_count > 0 else 0
                
                # Combined score: width utilization (60%) + box count (40%)
                width_util_score = estimated_width_util / 100.0
                combined_score = (width_util_score * 0.6) + (box_count_score * 0.4)
                
                length_scores[length] = {
                    'score': combined_score,
                    'width_util': estimated_width_util,
                    'box_count': box_count,
                    'unique_boxes': unique_boxes
                }
            
            # Select length with best score
            best_length = max(length_scores.items(), key=lambda x: x[1]['score'])
            
            # Fallback to original logic if no length gives >70% width utilization
            if best_length[1]['width_util'] < 70.0:
                # Use original quantity-based selection
                most_boxes = max(length_counts.items(), 
                               key=lambda x: (x[1]['count'], len(x[1]['boxes'])))
                return most_boxes[0]
            
            return best_length[0]
        else:
            # Fallback to original logic if no container_width provided
            most_boxes = max(length_counts.items(), 
                           key=lambda x: (x[1]['count'], len(x[1]['boxes'])))
            return most_boxes[0]
    
    def get_top_dominant_lengths(self, boxes: List[Dict], top_n: int = 3) -> List[float]:
        """
        Get top N dominant length candidates for row packing
        
        Args:
            boxes: List of boxes to analyze
            top_n: Number of top candidates to return (default: 3)
            
        Returns:
            List[float]: List of dominant lengths sorted by priority (best first)
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
        
        if not length_counts:
            return [34.0]  # Default fallback
        
        # Sort by priority: (quantity, number of unique boxes)
        sorted_lengths = sorted(length_counts.items(), 
                              key=lambda x: (x[1]['count'], len(x[1]['boxes'])), 
                              reverse=True)
        
        # Return top N lengths
        return [length for length, _ in sorted_lengths[:top_n]]
    
    def pack_row_z_first(self, boxes: List[Dict], row_y: float, container_height: float, 
                         container_width: float, dominant_length: float = None,
                         all_remaining_boxes: List[Dict] = None) -> List[Dict]:
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
            dominant_length: Optional dominant length to use (if None, will calculate)
            
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
        
        # Determine dominant length for this row (use provided or calculate)
        if dominant_length is None:
            # MEDIUM PRIORITY 2: Pass container_width for width-aware selection
            dominant_length = self.determine_dominant_length(boxes_sorted, container_width)
        
        # MEDIUM PRIORITY 1: Multiple Dominant Lengths
        # Get top 2-3 dominant lengths to allow more boxes in row
        top_lengths = self.get_top_dominant_lengths(boxes_sorted, top_n=3)
        primary_length = dominant_length
        secondary_length = None
        
        # Choose secondary length if it's significantly different and has good box count
        for alt_length in top_lengths:
            if abs(alt_length - primary_length) > 3.0:  # Significantly different
                # Count boxes that match this length
                alt_count = sum(1 for box in boxes_sorted 
                              for orient in self.get_all_orientations(box)
                              if abs(orient['length'] - alt_length) <= 2.0)
                if alt_count >= len(boxes_sorted) * 0.3:  # At least 30% of boxes
                    secondary_length = alt_length
                    print(f"  -> Using multiple dominant lengths: primary={primary_length:.1f}\", secondary={secondary_length:.1f}\"")
                    break
        
        allowed_lengths = [primary_length]
        if secondary_length:
            allowed_lengths.append(secondary_length)
        
        # Expand all boxes by quantity
        expanded_boxes = []
        for box in boxes_sorted:
            qty = int(box.get('quantity', 1))
            if qty <= 0:
                continue
            for _ in range(qty):
                expanded_boxes.append(box.copy())
        
        # IMPROVEMENT 1: Keep original expanded boxes for re-filtering
        original_expanded_boxes = expanded_boxes.copy()
        
        # MEDIUM PRIORITY 1: Filter boxes with multiple dominant lengths
        # This allows boxes matching either primary or secondary length
        # DYNAMIC TOLERANCE: Start strict, increase if too restrictive
        tolerance = 2.0 if secondary_length else 1.0  # Slightly relaxed for multi-length
        
        def filter_boxes_with_multiple_lengths(boxes_list, allowed_lengths_list, tol):
            """Helper function to filter boxes matching any of the allowed lengths"""
            filtered = []
            for box in boxes_list:
                valid_orientations = []
                best_match = None
                best_length = None
                
                # Try to find match with any allowed length
                for orientation in self.get_all_orientations(box):
                    box_l = orientation['length']
                    
                    # Check against each allowed length
                    for allowed_l in allowed_lengths_list:
                        length_diff = abs(box_l - allowed_l)
                        
                        if box_l == allowed_l:
                            # Exact match - prefer this
                            valid_orientations.append(orientation)
                        elif length_diff <= tol:
                            # Within tolerance
                            if best_match is None or length_diff < abs(best_match['length'] - best_length):
                                best_match = orientation
                                best_length = allowed_l
                
                # If have exact matches, use them
                if valid_orientations:
                    filtered.append(box)
                elif best_match:
                    # Use closest match within tolerance
                    filtered.append(box)
            return filtered
        
        # For backward compatibility, keep old function name
        def filter_boxes_with_tolerance(boxes_list, dom_length, tol):
            """Helper function to filter boxes with given tolerance (single length)"""
            return filter_boxes_with_multiple_lengths(boxes_list, [dom_length], tol)
        
        # MEDIUM PRIORITY 1: Filter with multiple dominant lengths
        filtered_boxes = filter_boxes_with_multiple_lengths(expanded_boxes, allowed_lengths, tolerance)
        
        # Check if filter is too restrictive
        original_count = len(expanded_boxes)
        filtered_count = len(filtered_boxes)
        
        if filtered_count < original_count * 0.5:
            print(f"  WARNING: Only {filtered_count}/{original_count} boxes pass filter, increasing tolerance to 3.0\"")
            tolerance = 3.0
            filtered_boxes = filter_boxes_with_multiple_lengths(expanded_boxes, allowed_lengths, tolerance)
            filtered_count = len(filtered_boxes)
        
        # Final fallback: use all boxes if still too few
        if filtered_count < 10:
            print(f"  WARNING: Too few boxes ({filtered_count}), using all boxes without filter")
            filtered_boxes = expanded_boxes
            tolerance = 10.0
        
        # Update expanded_boxes to use filtered list
        expanded_boxes = filtered_boxes
        
        # Track position in row - START FILLING Z FIRST
        current_x = 0.0
        current_z = 0.0
        column_max_width = 0.0  # Track max width in current column
        
        # IMPROVEMENT 1: Progressive relaxation tracking
        placed_boxes_count = 0
        secondary_length_tried = False
        
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
            
            # MEDIUM PRIORITY 1: Try all orientations matching any allowed length
            # Priority: 1) Primary length, 2) Secondary length, 3) Width utilization
            for orientation in self.get_all_orientations(box):
                box_l = orientation['length']
                
                # Check if matches any allowed length
                matches_primary = abs(box_l - primary_length) <= tolerance
                matches_secondary = secondary_length and abs(box_l - secondary_length) <= tolerance
                
                if not (matches_primary or matches_secondary):
                    continue
                
                # Determine length match priority (0 = primary, 1 = secondary)
                length_match_priority = 0 if matches_primary else 1
                
                box_w = orientation['width']
                box_h = orientation['height']  # Z-axis height
                
                # Check if fits in container dimensions
                if box_w > container_width or box_h > container_height:
                    continue
                
                # Check if fits at current position (KEY: check Z first!)
                if current_z + box_h <= container_height and current_x + box_w <= container_width:
                    # MEDIUM PRIORITY 3: Enhanced orientation selection with width priority
                    # Calculate score: width utilization (70%) + length match (30%)
                    # But prioritize primary length > secondary length
                    
                    # Width score (normalized, prefer larger width)
                    width_score = box_w / container_width if container_width > 0 else 0
                    
                    # Length match score (0.0 = primary, 0.5 = secondary, 1.0 = mismatch)
                    length_match_score = 0.0 if length_match_priority == 0 else 0.5
                    
                    # Combined score: higher is better
                    # Dynamic weights: if width utilization < 70%, prioritize width more
                    width_utilization = (current_x / container_width * 100) if container_width > 0 else 0.0
                    if width_utilization < 70.0 and placed_boxes_count >= 10:
                        # Prioritize width more when utilization is low
                        width_weight = 0.9
                        length_weight = 0.1
                    else:
                        # Normal weights
                        width_weight = 0.7
                        length_weight = 0.3
                    
                    combined_score = (width_score * width_weight) + (length_match_score * length_weight)
                    
                    # Convert to deviation-style score (lower is better)
                    deviation = 1.0 - combined_score
                    
                    # Choose orientation with best score (lowest deviation)
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
                    
                    # MEDIUM PRIORITY 1: Check if matches any allowed length
                    matches_primary = abs(box_l - primary_length) <= tolerance
                    matches_secondary = secondary_length and abs(box_l - secondary_length) <= tolerance
                    
                    if not (matches_primary or matches_secondary):
                        continue
                    
                    length_match_priority = 0 if matches_primary else 1
                    
                    box_w = orientation['width']
                    box_h = orientation['height']
                    
                    if box_w > container_width or box_h > container_height:
                        continue
                    
                    if current_z + box_h <= container_height and current_x + box_w <= container_width:
                        # MEDIUM PRIORITY 3: Enhanced orientation selection (same as above)
                        width_score = box_w / container_width if container_width > 0 else 0
                        length_match_score = 0.0 if length_match_priority == 0 else 0.5
                        
                        width_utilization = (current_x / container_width * 100) if container_width > 0 else 0.0
                        if width_utilization < 70.0 and placed_boxes_count >= 10:
                            width_weight = 0.9
                            length_weight = 0.1
                        else:
                            width_weight = 0.7
                            length_weight = 0.3
                        
                        combined_score = (width_score * width_weight) + (length_match_score * length_weight)
                        deviation = 1.0 - combined_score
                        
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
                placed_boxes_count += 1
                
                # Update position for next box
                box_w = best_orientation['width']
                box_h = best_orientation['height']
                
                # KEY: Increase Z first (stack up)
                current_z += box_h
                column_max_width = max(column_max_width, box_w)
                
                # IMPROVEMENT 1.1: Track width utilization for progressive relaxation
                current_width = max(b['position']['x'] + b['dimensions']['width'] 
                                  for b in placed_boxes) if placed_boxes else 0.0
                width_utilization = (current_width / container_width * 100) if container_width > 0 else 0.0
                
                # IMPROVEMENT 1.2: Progressive relaxation logic
                # Check every 10 boxes or at 25% progress
                check_interval = max(10, len(expanded_boxes) // 4)
                if placed_boxes_count % check_interval == 0 or placed_boxes_count == len(expanded_boxes) // 4:
                    if width_utilization < 80.0 and tolerance < 3.0:
                        # Increase tolerance progressively
                        # Note: This will affect orientation checking for remaining boxes
                        old_tolerance = tolerance
                        tolerance = min(3.0, tolerance + 1.0)
                        print(f"  -> Width utilization {width_utilization:.1f}% < 80%, increasing tolerance from {old_tolerance:.1f}\" to {tolerance:.1f}\"")
                        # Note: Don't re-filter expanded_boxes during loop to avoid iterator issues
                        # New tolerance will be applied in orientation checking logic
                
                # IMPROVEMENT 1.3: Try secondary dominant lengths if still low utilization
                # Note: This is logged but not applied during loop to avoid iterator issues
                # Secondary length boxes will be available in gap filling phase
                if width_utilization < 70.0 and tolerance >= 3.0 and not secondary_length_tried:
                    # Check if we've processed at least 25% of boxes
                    if placed_boxes_count >= len(expanded_boxes) * 0.25:
                        top_lengths = self.get_top_dominant_lengths(original_expanded_boxes, top_n=3)
                        # Try secondary dominant_length (skip the one already used)
                        for alt_length in top_lengths:
                            if abs(alt_length - dominant_length) > 1.0:  # Different from current
                                print(f"  -> Low width utilization detected, secondary length {alt_length:.1f}\" available for gap filling")
                                secondary_length_tried = True
                                break
                
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
        
        # OPTION A - PHASE 2: Active Cell Height Filling
        # Change threshold from 0.8 (80%) to 0.95 (95%) to force fill cells to maximum height
        incomplete_cells = self.detect_incomplete_cells(
            placed_boxes, container_height, threshold=0.95
        )
        
        if incomplete_cells and len(placed_boxes) < len(expanded_boxes):
            # Count how many of each box type were placed
            placed_counts = Counter((b.get('code', ''), b.get('material', '')) 
                                   for b in placed_boxes)
            expanded_counts = Counter((b.get('code', ''), b.get('material', '')) 
                                     for b in expanded_boxes)
            
            # Get boxes that haven't been fully placed yet
            remaining_boxes = []
            for box in expanded_boxes:
                key = (box.get('code', ''), box.get('material', ''))
                if expanded_counts[key] > placed_counts.get(key, 0):
                    remaining_boxes.append(box)
                    placed_counts[key] = placed_counts.get(key, 0) + 1  # Track usage
            
            # OPTION A - PHASE 2.2: Forced cell filling with smallest boxes first
            # Sort remaining boxes by height (ascending) to prefer smallest boxes for filling gaps
            remaining_boxes_sorted = sorted(remaining_boxes, 
                                          key=lambda b: min(orient['height'] 
                                                          for orient in self.get_all_orientations(b)))
            
            # Try to backfill each incomplete cell
            for cell in incomplete_cells:
                if cell['remaining_height'] < 3.0:  # Skip if too little space left (reduced from 5.0)
                    continue
                
                cell_x = cell['x']
                cell_y = row_y
                # Calculate current top Z position from existing boxes in this cell
                cell_boxes = cell['boxes']
                cell_current_z = max(box['position']['z'] + box['dimensions']['height'] 
                                    for box in cell_boxes) if cell_boxes else 0.0
                remaining_h = container_height - cell_current_z
                
                # OPTION A - PHASE 2.2: Use greedy algorithm - try smallest boxes first
                # Try to find boxes that fit in remaining height
                for box in remaining_boxes_sorted[:]:  # Copy list to modify during iteration
                    best_orientation = None
                    best_fit_height = 0
                    
                    # Check all orientations for this box
                    for orientation in self.get_all_orientations(box):
                        box_h = orientation['height']
                        box_w = orientation['width']
                        box_l = orientation['length']
                        
                        # OPTION A - PHASE 2.2: Relaxed constraint - allow boxes from different lengths
                        # if cell height is very low (< 50% container_height), allow more flexibility
                        cell_height_util = (cell_current_z / container_height * 100) if container_height > 0 else 0
                        length_tolerance = tolerance * 2.0 if cell_height_util < 50.0 else tolerance
                        
                        # Check if fits in remaining space
                        if (box_h <= remaining_h and 
                            box_w <= cell['width'] and
                            abs(box_l - dominant_length) <= length_tolerance):
                            # Prefer largest height that still fits to maximize utilization
                            if box_h > best_fit_height:
                                best_orientation = orientation
                                best_fit_height = box_h
                    
                    if best_orientation:
                        # Place box in incomplete cell
                        placed_box = {
                            'code': box.get('code', 'UNKNOWN'),
                            'dimensions': best_orientation,
                            'position': {
                                'x': cell_x,
                                'y': cell_y,
                                'z': cell_current_z  # Stack on top of existing boxes
                            },
                            'material': box.get('material', ''),
                            'packing_method': box.get('packing_method', 'CARTON')
                        }
                        placed_boxes.append(placed_box)
                        cell_current_z += best_orientation['height']
                        remaining_h = container_height - cell_current_z
                        remaining_boxes_sorted.remove(box)
                        
                        # OPTION A - PHASE 2.2: Continue until cell is full (95%+) or no boxes fit
                        if remaining_h < 3.0:  # Cell is full enough
                            break
        
        # IMPROVEMENT 2: Width-First Gap Filling
        # Calculate remaining width gap
        if placed_boxes:
            max_x = max(box['position']['x'] + box['dimensions']['width'] 
                       for box in placed_boxes)
            remaining_width = container_width - max_x
            width_utilization = (max_x / container_width * 100) if container_width > 0 else 0.0
            
            # OPTION C - ENHANCED: Search all remaining boxes from all rows if available
            # Use all_remaining_boxes if provided, otherwise use remaining_boxes from current row
            if remaining_width >= 5.0 and width_utilization < 90.0:
                print(f"  -> Gap filling: detected gap {remaining_width:.1f}\" (width utilization: {width_utilization:.1f}%)")
                
                # OPTION C: Get remaining boxes from all rows (not just current row)
                if all_remaining_boxes:
                    # Use all remaining boxes from all rows
                    placed_counts = Counter((b.get('code', ''), b.get('material', '')) 
                                           for b in placed_boxes)
                    gap_filling_boxes = []
                    for box in all_remaining_boxes:
                        # Check if box hasn't been placed in this row
                        key = (box.get('code', ''), box.get('material', ''))
                        if key not in placed_counts:
                            gap_filling_boxes.append(box)
                            placed_counts[key] = placed_counts.get(key, 0) + 1  # Track usage
                    print(f"  -> Gap filling: found {len(gap_filling_boxes)} remaining boxes from all rows to fill gap")
                else:
                    # Fallback to original logic: only boxes from current row
                    placed_counts = Counter((b.get('code', ''), b.get('material', '')) 
                                           for b in placed_boxes)
                    source_boxes = original_expanded_boxes
                    expanded_counts = Counter((b.get('code', ''), b.get('material', '')) 
                                             for b in source_boxes)
                    
                    # Get boxes that haven't been fully placed yet
                    gap_filling_boxes = []
                    for box in source_boxes:
                        key = (box.get('code', ''), box.get('material', ''))
                        if expanded_counts[key] > placed_counts.get(key, 0):
                            gap_filling_boxes.append(box)
                            placed_counts[key] = placed_counts.get(key, 0) + 1  # Track usage
                    print(f"  -> Gap filling: found {len(gap_filling_boxes)} remaining boxes to fill gap")
                
                # Sort remaining boxes by width (ascending) - prefer smaller boxes to fill gaps better
                # But we want to maximize width utilization, so prefer larger width that still fits
                def get_fitting_width_score(box):
                    """Get max width of orientations that fit in remaining gap"""
                    fitting_widths = [orient['width'] for orient in self.get_all_orientations(box)
                                     if orient['width'] <= remaining_width and orient['height'] <= container_height]
                    if fitting_widths:
                        return max(fitting_widths)
                    return 0.0  # No fitting orientations
                
                def get_max_width(box):
                    """Get max width of any orientation"""
                    widths = [orient['width'] for orient in self.get_all_orientations(box)]
                    return max(widths) if widths else 0.0
                
                gap_filling_boxes.sort(key=lambda b: (
                    -get_fitting_width_score(b),
                    get_max_width(b)
                ), reverse=True)
                
                # Fill gap with boxes
                current_gap_x = max_x
                boxes_filled = 0
                for box in gap_filling_boxes:
                    if remaining_width < 3.0:  # Gap too small to fill (reduced from 5.0)
                        break
                    
                    best_orientation = None
                    best_width = 0
                    
                    # Try all orientations - find one that fits and maximizes width
                    for orientation in self.get_all_orientations(box):
                        box_w = orientation['width']
                        box_h = orientation['height']
                        
                        # Check if fits in remaining gap
                        if box_w <= remaining_width and box_h <= container_height:
                            # Prefer larger width to maximize utilization
                            if box_w > best_width:
                                best_orientation = orientation
                                best_width = box_w
                    
                    if best_orientation:
                        # Place box in gap
                        placed_box = {
                            'code': box.get('code', 'UNKNOWN'),
                            'dimensions': best_orientation,
                            'position': {
                                'x': current_gap_x,
                                'y': row_y,
                                'z': 0.0  # Start new column at bottom
                            },
                            'material': box.get('material', ''),
                            'packing_method': box.get('packing_method', 'CARTON')
                        }
                        placed_boxes.append(placed_box)
                        
                        # Update gap position
                        current_gap_x += best_width
                        remaining_width -= best_width
                        
                        boxes_filled += 1
                        print(f"  -> Gap filling: placed box {box.get('code', 'UNKNOWN')} "
                              f"(width={best_width:.1f}\"), remaining gap: {remaining_width:.1f}\"")
                
                if boxes_filled > 0:
                    final_max_x = max(box['position']['x'] + box['dimensions']['width'] 
                                     for box in placed_boxes)
                    final_width_utilization = (final_max_x / container_width * 100) if container_width > 0 else 0.0
                    print(f"  -> Gap filling: filled {boxes_filled} boxes, width utilization: {width_utilization:.1f}% -> {final_width_utilization:.1f}%")
                elif len(gap_filling_boxes) > 0:
                    print(f"  -> Gap filling: no boxes fit in gap {remaining_width:.1f}\"")
        
        return placed_boxes
    
    def detect_incomplete_cells(self, placed_boxes: List[Dict], 
                               container_height: float, 
                               threshold: float = 0.8) -> List[Dict]:
        """
        Detect cells that haven't reached minimum height threshold
        
        Groups boxes by X position (cells/columns) and identifies cells with
        height < threshold * container_height.
        
        Args:
            placed_boxes: List of placed boxes
            container_height: Maximum container height
            threshold: Minimum height ratio (default: 0.8 = 80%)
            
        Returns:
            List[Dict]: [{x, height, remaining_height, boxes, width}, ...]
                       List of incomplete cells with their properties
        """
        # Group boxes by X position (cells)
        cells_dict = {}
        tolerance_x = 0.5
        
        for box in placed_boxes:
            x_pos = box['position']['x']
            # Find existing cell or create new
            cell_key = None
            for key in cells_dict.keys():
                if abs(key - x_pos) <= tolerance_x:
                    cell_key = key
                    break
            if cell_key is None:
                cell_key = x_pos
                cells_dict[cell_key] = []
            cells_dict[cell_key].append(box)
        
        # Calculate height for each cell
        incomplete_cells = []
        min_height = container_height * threshold
        
        for cell_x, cell_boxes in cells_dict.items():
            if not cell_boxes:
                continue
            
            cell_height = max(box['position']['z'] + box['dimensions']['height'] 
                             for box in cell_boxes)
            
            if cell_height < min_height:
                # Calculate cell width
                cell_width = max(box['position']['x'] + box['dimensions']['width'] 
                               for box in cell_boxes) - min(box['position']['x'] 
                                                           for box in cell_boxes)
                
                incomplete_cells.append({
                    'x': cell_x,
                    'height': cell_height,
                    'remaining_height': container_height - cell_height,
                    'boxes': cell_boxes,
                    'width': cell_width
                })
        
        return incomplete_cells
    
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
