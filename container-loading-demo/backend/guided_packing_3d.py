"""
Guided Packing Algorithm - Sử dụng manual layout template

Strategy:
1. Parse manual_layout.json để lấy row structure
2. Group boxes theo height ranges tương ứng với row heights
3. Pack theo template của từng row
4. Optimize orientation cho CARTON boxes để maximize boxes per row
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import os
import random
import copy
from laff_bin_packing_3d import LAFFBinPacking3D, EmptySpace


class GuidedPackingAlgorithm(LAFFBinPacking3D):
    """
    Guided Packing sử dụng manual layout template
    
    Inherits from LAFF để tái sử dụng các utility methods.
    Override packing logic để theo pattern từ manual layout.
    """
    
    def __init__(self, container_dims: Dict[str, float], manual_template_path: Optional[str] = None):
        super().__init__(container_dims)
        self.manual_template = None
        if manual_template_path:
            self.load_manual_template(manual_template_path)
    
    def load_manual_template(self, template_path: str):
        """
        Load structure từ manual_layout.json
        
        Returns:
            Dict với row templates (height, box_count, cells)
        """
        if not os.path.exists(template_path):
            print(f"Warning: Template not found at {template_path}")
            return
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.manual_template = data.get('manual_packing_reference', {})
        print(f"Loaded manual template: {self.manual_template.get('total_rows', 0)} rows, "
              f"total_length: {self.manual_template.get('total_length_used', 0)}\"")
    
    def get_row_structure(self) -> List[Dict]:
        """
        Trích xuất row structure từ template
        
        Returns:
            List[Dict]: Row templates với row number, height, box_count, cells
        """
        if not self.manual_template:
            return []
        
        return self.manual_template.get('rows', [])
    
    def group_boxes_by_height(self, boxes: List[Dict], row_structure: List[Dict]) -> Dict[str, List[Dict]]:
        """
        KHÔNG phân boxes trước
        
        Thay vào đó, pack tuần tự row by row từ boxes pool
        Mỗi row sẽ tự lấy boxes từ pool khi pack
        """
        groups = {}
        for row in row_structure:
            row_id = f"row_{row['row']}"
            groups[row_id] = {
                'row': row,
                'boxes': boxes  # All boxes available for each row
            }
        return groups
    
    def pack_boxes_guided(self, boxes: List[Dict]) -> List[Dict[str, Any]]:
        """
        Pack boxes row by row, removing packed boxes from pool
        """
        # Get row structure from template
        row_structure = self.get_row_structure()
        
        if not row_structure:
            # Fallback to LAFF if no template
            print("No template found, falling back to LAFF")
            return super().pack_boxes(boxes)
        
        # Initialize container
        self._new_container()
        
        # Track remaining boxes counts (to prevent duplicates)
        # Format: {(code, material, purchasing_doc, packing_method): remaining_qty}
        remaining_counts = {}
        for box in boxes:
            qty = box.get('quantity', 1)
            if qty == 0:
                continue
            key = (box.get('code', ''), box.get('material', ''), 
                   box.get('purchasing_doc', ''), box.get('packing_method', ''))
            remaining_counts[key] = qty
        
        print(f"DEBUG: Total unique boxes: {len(remaining_counts)}")
        print(f"DEBUG: Total quantity: {sum(remaining_counts.values())}")
        
        # Track position as we pack rows
        current_y = self.BUFFER_RULES['door_clearance']  # Start after door clearance
        
        # Pack each row - create rows dynamically
        row_number = 1
        
        while True:
            # Check if any boxes remain
            total_remaining = sum(remaining_counts.values())
            if total_remaining == 0:
                break
            
            # Get available boxes
            available_boxes = []
            for box in boxes:
                key = (box.get('code', ''), box.get('material', ''), 
                       box.get('purchasing_doc', ''), box.get('packing_method', ''))
                if key in remaining_counts and remaining_counts[key] > 0:
                    # Create box copy with current remaining quantity
                    box_copy = box.copy()
                    qty = remaining_counts[key]
                    box_copy['quantity'] = qty
                    available_boxes.append(box_copy)
            
            if not available_boxes:
                break
            
            row_y = current_y
            print(f"Row {row_number}: {len(available_boxes)} box types, {total_remaining} boxes available")
            
            # Pack boxes in this row
            placed_boxes = self.pack_row_horizontally(
                available_boxes, row_y, self.container['height'], self.container['width']
            )
            
            if not placed_boxes:
                # No boxes could be placed, stop
                break
            
            # Remove placed boxes from remaining_counts
            placed_by_type = {}
            for placed_box in placed_boxes:
                code = placed_box.get('code', 'UNKNOWN')
                material = placed_box.get('material', '')
                # Find original box to get purchasing_doc and packing_method
                key = None
                for orig_box in boxes:
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
            
            remaining_after = sum(remaining_counts.values())
            print(f"  -> Placed {len(placed_boxes)} boxes")
            print(f"  -> Remaining: {remaining_after} boxes")
            
            # Add placed boxes to container
            for box in placed_boxes:
                self.current_container['boxes'].append(box)
            
            # Calculate max height in this row (for visualization only)
            max_z = max(box['position']['z'] + box['dimensions']['height'] 
                       for box in placed_boxes) if placed_boxes else 0
            
            # Calculate actual Y position used by this row
            # Y-axis (length): All boxes in same row have same Y position
            # Z-axis (height): Boxes are stacked vertically
            # Length of row in Y-axis = max length dimension of any box in this row
            max_length = max(box['dimensions']['length'] for box in placed_boxes) if placed_boxes else 34.0
            current_y += max_length
            
            print(f"  -> Row height: {max_z:.1f}\" Z-axis, Y position now: {current_y:.1f}\"")
            
            row_number += 1
            
            # Safety check: don't exceed container length
            if current_y >= self.container['length']:
                print(f"WARNING: Stopping due to container length limit")
                break
        
        return self.containers
    
    def determine_dominant_length(self, boxes: List[Dict]) -> float:
        """
        Determine dominant length for row packing
        
        Priority:
        1. Most common length across all possible orientations
        2. Length that allows packing most boxes
        
        Args:
            boxes: List of boxes to analyze
            
        Returns:
            float: Dominant length value
        """
        # Count frequency of each possible length
        length_counts = {}
        for box in boxes:
            for orientation in self.get_all_orientations(box):
                length = orientation['length']
                length_counts[length] = length_counts.get(length, 0) + 1
        
        # Priority 1: Most common length
        if length_counts:
            most_common_length = max(length_counts, key=length_counts.get)
            return most_common_length
        
        return 34.0  # Default fallback
    
    def pack_row_horizontally(self, boxes: List[Dict], row_y: float, container_height: float, 
                              container_width: float) -> List[Dict]:
        """
        Pack row using Simple Layer Packing
        
        Strategy:
        1. Fill X-axis first (left to right: 0 → 92.5")
        2. When X full → increase Z (stack up), reset X
        3. When Z full → stop (row is full)
        
        This ensures proper row distribution instead of packing all into 1 row
        
        Returns:
            List[Dict]: Placed boxes
        """
        placed_boxes = []
        
        # Sort boxes by (packing_method_priority, material, purchasing_doc, height, area, quantity)
        # Priority: PRE_PACK (0) before CARTON (1) - GLOBAL level
        packing_method_priority = {'PRE_PACK': 0, 'CARTON': 1}
        boxes_sorted = sorted(boxes, key=lambda b: (
            packing_method_priority.get(b.get('packing_method', 'CARTON'), 1),  # PRE_PACK=0 first globally
            b.get('material', ''), 
            b.get('purchasing_doc', ''),
            -b.get('quantity', 1),                # Quantity descending - FIX: prioritize quantity
            b['dimensions']['height'],           # Height for better stacking
            -(b['dimensions']['width'] * b['dimensions']['length']),  # Area descending
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
        
        # Track position in row
        current_x = 0.0
        current_z = 0.0
        row_height = 0.0  # Max Z at current X-level
        
        for box in expanded_boxes:
            # Calculate average dimensions from placed boxes
            if placed_boxes:
                avg_length = sum(b['dimensions']['length'] for b in placed_boxes) / len(placed_boxes)
                avg_width = sum(b['dimensions']['width'] for b in placed_boxes) / len(placed_boxes)
            else:
                # First box in row - use dominant_length as initial target
                avg_length = dominant_length
                avg_width = None
            
            # Try to find best orientation that fits
            best_orientation = None
            best_score = float('inf')
            fits_current = False
            
            # Try all orientations and pick the one with minimum deviation from average dimensions
            for orientation in self.get_all_orientations(box):
                box_w = orientation['width']
                box_h = orientation['height']  # Z-axis height
                box_l = orientation['length']
                
                # Check if fits in container dimensions
                if box_w > container_width or box_h > container_height:
                    continue
                
                # Check if fits at current position
                if current_x + box_w <= container_width and current_z + box_h <= container_height:
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
            
            # If doesn't fit at current position, try next level (increase Z, reset X)
            if not fits_current:
                # Try to move to next level if we have vertical space
                if row_height > current_z:
                    current_x = 0.0
                    current_z = row_height
                    row_height = 0.0
                    
                    # Try again at new level - pick minimum deviation
                    for orientation in self.get_all_orientations(box):
                        box_w = orientation['width']
                        box_h = orientation['height']
                        box_l = orientation['length']
                        
                        if box_w > container_width or box_h > container_height:
                            continue
                        
                        if current_x + box_w <= container_width and current_z + box_h <= container_height:
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
                
                current_x += box_w
                row_height = max(row_height, current_z + box_h)
                
                # Check if need to go to next level
                if current_x >= container_width:
                    current_x = 0.0
                    current_z = row_height
                    row_height = 0.0
            else:
                # Can't fit this box in current row
                # Check if same material/purchasing_doc group
                if placed_boxes:
                    first_box_material = placed_boxes[0].get('material', '')
                    first_box_doc = placed_boxes[0].get('purchasing_doc', '')
                    current_material = box.get('material', '')
                    current_doc = box.get('purchasing_doc', '')
                    
                    if (current_material == first_box_material and 
                        current_doc == first_box_doc):
                        # Same group but doesn't fit - skip to next row
                        break
                    elif best_orientation and best_orientation['length'] != dominant_length:
                        # Different group but orientation doesn't match dominant_length
                        # Try to place anyway if it fits
                        if best_orientation and fits_current:
                            # Place box despite length mismatch
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
                            
                            box_w = best_orientation['width']
                            box_h = best_orientation['height']
                            
                            current_x += box_w
                            row_height = max(row_height, current_z + box_h)
                            
                            if current_x >= container_width:
                                current_x = 0.0
                                current_z = row_height
                                row_height = 0.0
                        else:
                            break
                    else:
                        break
                else:
                    # No boxes placed yet, just break
                    break
        
        return placed_boxes
    
    
    
    
    def get_all_orientations(self, box: Dict) -> List[Dict]:
        """
        Generate tất cả orientations hợp lệ cho box
        
        CARTON: 2 orientations (luôn đứng, chỉ xoay trái/phải)
        PRE_PACK: 4 orientations (mặt width×height không chạm sàn)
        
        Returns:
            List[Dict]: [{width, length, height}, ...]
        """
        w, l, h = box['dimensions']['width'], box['dimensions']['length'], box['dimensions']['height']
        packing_method = box.get('packing_method', 'CARTON')
        
        if packing_method == 'PRE_PACK':
            # PRE_PACK: 4 orientations - loại trừ mặt (width × height) chạm sàn
            return [
                {'width': w, 'length': l, 'height': h},  # (w×l) chạm sàn
                {'width': l, 'length': w, 'height': h},  # (l×w) chạm sàn - xoay 90°
                {'width': l, 'length': h, 'height': w},  # (l×h) chạm sàn
                {'width': h, 'length': l, 'height': w}   # (h×l) chạm sàn - xoay 90°
            ]
        else:
            # CARTON: 2 orientations - luôn đứng theo height, chỉ xoay trái/phải
            return [
                {'width': w, 'length': l, 'height': h},  # Đứng, hướng gốc
                {'width': l, 'length': w, 'height': h}   # Đứng, xoay 90°
            ]
    
    def optimize_box_orientation(self, box: Dict, available_width: float) -> Optional[Dict[str, float]]:
        """
        Tìm orientation tốt nhất cho box
        
        Strategy:
        - PRE_PACK: No rotation, use original
        - CARTON: Try all valid orientations, choose one that fits most boxes per row
        
        Returns:
            Dict với {width, length, height} hoặc None if can't fit
        """
        packing_method = box.get('packing_method', 'CARTON')
        box_dims = box['dimensions']
        
        if packing_method == 'PRE_PACK':
            # PRE_PACK: width × length on floor, no rotation
            if box_dims['width'] <= available_width:
                return box_dims.copy()
            return None
        
        # CARTON: Try multiple orientations
        orientations = []
        
        # Normal orientation
        if box_dims['width'] <= available_width:
            orientations.append({
                'width': box_dims['width'],
                'length': box_dims['length'],
                'height': box_dims['height']
            })
        
        # Rotated 90° in XY plane: swap width ↔ length
        if box_dims['length'] <= available_width:
            orientations.append({
                'width': box_dims['length'],
                'length': box_dims['width'],
                'height': box_dims['height']
            })
        
        # Select best orientation (smallest width = most boxes per row)
        if orientations:
            best = min(orientations, key=lambda o: o['width'])
            return best
        
        return None
    
    def pack_boxes(self, boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main packing method
        
        Pack all boxes into rows sequentially, no multi-pass for now
        """
        if not self.manual_template:
            return super().pack_boxes(boxes)
        
        # Simple: just pack once with guided algorithm
        containers = self.pack_boxes_guided(boxes)
        
        return containers
    
    def _pack_single_pass(self, boxes: List[Dict], shuffle: bool = False, seed: Optional[int] = None) -> Optional[Dict]:
        """
        Single packing pass với option shuffle boxes
        """
        # Reset containers state for this pass
        self.containers = []
        
        if shuffle and seed is not None:
            boxes = self.shuffle_within_material_groups(boxes, seed)
        
        # Pack với guided algorithm (existing logic)
        containers = self.pack_boxes_guided(boxes)
        
        if not containers or not containers[0].get('boxes'):
            return None
        
        # Get all boxes from all containers (sometimes creates multiple)
        all_placed_boxes = []
        for container in containers:
            all_placed_boxes.extend(container.get('boxes', []))
        
        if not all_placed_boxes:
            return None
        
        # Calculate results from first container only
        total_boxes = len(containers[0]['boxes'])
        max_y = max(box['position']['y'] + box['dimensions']['length'] 
                   for box in containers[0]['boxes']) if containers[0]['boxes'] else 0
        length_used = max_y - self.BUFFER_RULES['door_clearance']
        
        return {
            'total_boxes': total_boxes,
            'length_used': length_used,
            'containers': containers
        }
    
    def shuffle_within_material_groups(self, boxes: List[Dict], seed: int) -> List[Dict]:
        """
        Shuffle boxes trong cùng material/purchasing_doc group
        
        Giữ nguyên material order, chỉ shuffle internal
        """
        random.seed(seed)
        
        # Group by material/purchasing_doc
        groups = {}
        for box in boxes:
            key = (box.get('material', ''), box.get('purchasing_doc', ''))
            if key not in groups:
                groups[key] = []
            groups[key].append(box)
        
        # Shuffle each group
        shuffled = []
        for key in sorted(groups.keys()):
            group = groups[key]
            random.shuffle(group)
            shuffled.extend(group)
        
        return shuffled

