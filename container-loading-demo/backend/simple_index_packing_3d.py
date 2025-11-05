"""
Simple Index-Based Cell Packing Algorithm

Strategy:
1. Process boxes theo thứ tự index trong array (từ trên xuống dưới)
2. Xoay boxes để tối ưu (chiếm ít không gian nhất)
3. Pack cell-by-cell: fill height (Z) đến tối đa trước khi chuyển sang cell tiếp theo
4. Fill width (X) của row đến tối đa trước khi chuyển sang row mới
"""

from typing import List, Dict, Any, Optional
from laff_bin_packing_3d import LAFFBinPacking3D


class SimpleIndexPackingAlgorithm(LAFFBinPacking3D):
    """
    Simple Index-Based Cell Packing Algorithm
    
    Strategy:
    - Process boxes theo thứ tự index trong array (không sort)
    - Xoay boxes để tối ưu (volume nhỏ nhất)
    - Pack cell-by-cell: fill height (Z) đến tối đa trước khi chuyển sang cell tiếp theo
    - Fill width (X) của row đến tối đa trước khi chuyển sang row mới
    """
    
    def __init__(self, container_dims: Dict[str, float]):
        super().__init__(container_dims)
    
    def pack_boxes(self, boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pack boxes using simple index-based cell packing
        
        Args:
            boxes: List of boxes to pack (theo thứ tự index trong array)
            
        Returns:
            List[Dict]: Container với packed boxes
        """
        # Initialize container
        self._new_container()
        
        # Step 1: Expand boxes by quantity (giữ nguyên thứ tự index)
        expanded_boxes = []
        for idx, box in enumerate(boxes):
            qty = int(box.get('quantity', 1))
            if qty <= 0:
                continue
            for _ in range(qty):
                box_copy = box.copy()
                box_copy['_original_index'] = idx  # Track original index
                expanded_boxes.append(box_copy)
        
        print(f"Total boxes to pack: {len(expanded_boxes)}")
        
        # Step 2: Pack cell-by-cell
        container_width = self.container['width']
        container_height = self.container['height']
        container_length = self.container['length']
        
        # Start position
        current_x = 0.0
        current_y = self.BUFFER_RULES['door_clearance']  # Start after door clearance
        current_z = 0.0
        current_cell_width = 0.0
        
        placed_boxes = []
        
        # Track row info for moving to next row
        row_max_length = 0.0  # Max length (Y dimension) in current row
        
        # Process boxes theo thứ tự index
        for box in expanded_boxes:
            # Find best orientation
            best_orientation = self.find_best_orientation(
                box, container_width, container_height, container_length
            )
            
            if not best_orientation:
                # Box không fit vào container với bất kỳ orientation nào
                print(f"  WARNING: Box {box.get('code', 'UNKNOWN')} does not fit in container")
                continue
            
            box_width = best_orientation['width']
            box_length = best_orientation['length']
            box_height = best_orientation['height']
            
            # Check if fits in current cell
            fits_current_cell = (
                current_z + box_height <= container_height and
                current_x + box_width <= container_width
            )
            
            if not fits_current_cell:
                # Current cell is full, move to next cell
                if current_z >= container_height * 0.95:  # Cell is almost full
                    # Move to next cell
                    current_x += current_cell_width if current_cell_width > 0 else 0
                    current_z = 0.0
                    current_cell_width = 0.0
                    
                    # Check if row is full
                    if current_x + box_width > container_width:
                        # Row is full, move to next row
                        current_y += row_max_length if row_max_length > 0 else 34.0  # Default length
                        current_x = 0.0
                        current_z = 0.0
                        current_cell_width = 0.0
                        row_max_length = 0.0
                elif current_x + box_width > container_width:
                    # Box doesn't fit in current row width, move to next row
                    current_y += row_max_length if row_max_length > 0 else 34.0  # Default length
                    current_x = 0.0
                    current_z = 0.0
                    current_cell_width = 0.0
                    row_max_length = 0.0
                
                # Check if still doesn't fit after moving
                if current_x + box_width > container_width:
                    # Box too wide for container, skip
                    print(f"  WARNING: Box {box.get('code', 'UNKNOWN')} (width={box_width:.1f}\") too wide for container (width={container_width:.1f}\")")
                    continue
            
            # Place box at current position
            placed_box = {
                'code': box.get('code', 'UNKNOWN'),
                'dimensions': best_orientation,
                'position': {
                    'x': current_x,
                    'y': current_y,
                    'z': current_z
                },
                'material': box.get('material', ''),
                'packing_method': box.get('packing_method', 'CARTON')
            }
            placed_boxes.append(placed_box)
            
            # Update position
            current_z += box_height
            current_cell_width = max(current_cell_width, box_width)
            row_max_length = max(row_max_length, box_length)
            
            # Check if cell is full
            if current_z >= container_height * 0.95:  # Cell is almost full
                # Move to next cell
                current_x += current_cell_width
                current_z = 0.0
                current_cell_width = 0.0
                
                # Check if row is full
                if current_x >= container_width * 0.95:  # Row is almost full
                    # Move to next row
                    current_y += row_max_length
                    current_x = 0.0
                    current_z = 0.0
                    current_cell_width = 0.0
                    row_max_length = 0.0
        
        # Add placed boxes to container
        self.current_container['boxes'] = placed_boxes
        
        print(f"Packed {len(placed_boxes)} boxes")
        
        return [self.current_container]
    
    def get_all_orientations(self, box: Dict[str, Any]) -> List[Dict[str, float]]:
        """
        Get all 6 possible orientations for a box
        
        Args:
            box: Box dict với dimensions
            
        Returns:
            List of orientation dicts (width, length, height)
        """
        dims = box['dimensions']
        w = dims['width']
        l = dims['length']
        h = dims['height']
        
        # All 6 orientations
        orientations = [
            {'width': w, 'length': l, 'height': h},  # Original
            {'width': l, 'length': w, 'height': h},  # Rotate 90° in XY
            {'width': w, 'length': h, 'height': l},  # Swap length ↔ height
            {'width': h, 'length': w, 'height': l},  # Rotate + swap
            {'width': l, 'length': h, 'height': w},  # Rotate + swap
            {'width': h, 'length': l, 'height': w}   # Full rotation
        ]
        
        return orientations
    
    def find_best_orientation(self, box: Dict[str, Any], container_width: float,
                             container_height: float, container_length: float) -> Optional[Dict[str, float]]:
        """
        Tìm orientation tối ưu cho box
        
        Strategy:
        - Thử tất cả 6 orientations
        - Chọn orientation:
          - Fit vào container (width <= container_width, height <= container_height, length <= container_length)
          - Volume nhỏ nhất (chiếm ít không gian nhất)
          - Nếu cùng volume → height nhỏ nhất (để stack tốt hơn)
        
        Args:
            box: Box dict với dimensions
            container_width: Container width
            container_height: Container height
            container_length: Container length
            
        Returns:
            Dict với orientation tối ưu (width, length, height) hoặc None nếu không fit
        """
        best_orientation = None
        best_volume = float('inf')
        best_height = float('inf')
        
        # Get all possible orientations
        all_orientations = self.get_all_orientations(box)
        
        for orientation in all_orientations:
            width = orientation['width']
            length = orientation['length']
            height = orientation['height']
            
            # Check if fits in container
            if (width <= container_width and
                height <= container_height and
                length <= container_length):
                
                volume = width * length * height
                
                # Prefer smaller volume
                if volume < best_volume:
                    best_orientation = orientation
                    best_volume = volume
                    best_height = height
                elif volume == best_volume:
                    # If same volume, prefer smaller height (better for stacking)
                    if height < best_height:
                        best_orientation = orientation
                        best_height = height
        
        return best_orientation
