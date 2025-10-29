"""
Output Formatter cho 3D Bin Packing - Format giống hình mẫu
"""

from typing import List, Dict, Any
from collections import Counter


class OutputFormatter3D:
    """Format output thành cấu trúc grid như hình mẫu"""
    
    def __init__(self):
        self.box_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                         'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                         'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'J2', 'K2']
    
    def format(self, containers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert packed containers thành grid layout
        
        Output như hình:
        Row 1 (Height 34.5"):
          Cell 1: 1A+1B+3C+9D+1E+5F (60 boxes)
          Cell 2: 3F+13G+1H+1I (18 boxes)
          ...
        """
        result = {
            'containers': [],
            'total_boxes': 0,
            'total_containers': len(containers),
            'overall_utilization': 0,
            'utilization': 0  # Add this field
        }
        
        total_utilization = 0
        
        for container in containers:
            grid = self._create_grid_from_boxes(container['boxes'])
            rows = self._group_into_rows(grid)
            
            container_utilization = self._calculate_utilization(container)
            
            result['containers'].append({
                'container_id': container['container_id'],
                'rows': rows,
                'total_boxes': len(container['boxes']),
                'utilization': container_utilization,
                'dimensions': container['dimensions']
            })
            
            result['total_boxes'] += len(container['boxes'])
            total_utilization += container_utilization
        
        if len(containers) > 0:
            result['overall_utilization'] = total_utilization / len(containers)
            result['utilization'] = total_utilization / len(containers)  # Add this line
        
        return result
    
    def _create_grid_from_boxes(self, boxes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Tạo grid structure từ danh sách boxes
        
        Group boxes theo vị trí x, y để tạo cells
        """
        # Group boxes by x, y position to create cells
        cells = {}
        
        for box in boxes:
            # Round position to create grid cells (grid size ~20")
            cell_x = round(box['position']['x'] / 20) * 20
            cell_y = round(box['position']['y'] / 20) * 20
            
            cell_key = f"{cell_x},{cell_y}"
            
            if cell_key not in cells:
                cells[cell_key] = {
                    'boxes': [],
                    'position': {'x': cell_x, 'y': cell_y},
                    'columns': []  # Will be populated based on box codes
                }
            
            cells[cell_key]['boxes'].append(box)
        
        # Add column information based on box codes
        for cell_key, cell in cells.items():
            cell['columns'] = sorted(set(box['code'] for box in cell['boxes']))
        
        return cells
    
    def _group_into_rows(self, cells: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group cells into rows based on height"""
        rows = []
        
        # Group cells by similar y position (front-to-back)
        y_positions = sorted(set(cell['position']['y'] for cell in cells.values()))
        
        for y_pos in y_positions:
            row_cells = [cell for cell in cells.values() 
                        if cell['position']['y'] == y_pos]
            
            # Calculate row height (max of cells in this row)
            # NOTE: Each cell may have stacked boxes at multiple z-levels
            # For each cell, calculate the maximum z-position + height of all boxes
            row_height = 0
            for cell in row_cells:
                if not cell['boxes']:
                    continue
                
                # Find the top of the tallest stack in this cell
                max_z_with_height = 0
                for box in cell['boxes']:
                    top_z = box['position']['z'] + box['dimensions']['height']
                    max_z_with_height = max(max_z_with_height, top_z)
                
                # Cell height = distance from z=0 to top of tallest box
                cell_height = max_z_with_height
                row_height = max(row_height, cell_height)
            
            # Format cells
            formatted_cells = []
            for i, cell in enumerate(sorted(row_cells, key=lambda c: c['position']['x'])):
                content = self._aggregate_boxes(cell['boxes'])
                
                # Calculate cell dimensions from boxes
                if cell['boxes']:
                    # Calculate actual span of boxes in this cell
                    min_x = min(box['position']['x'] for box in cell['boxes'])
                    max_x = max(box['position']['x'] + box['dimensions']['width'] for box in cell['boxes'])
                    min_y = min(box['position']['y'] for box in cell['boxes'])
                    max_y = max(box['position']['y'] + box['dimensions']['length'] for box in cell['boxes'])
                    
                    cell_width = max_x - min_x
                    cell_length = max_y - min_y
                else:
                    cell_width = 20
                    cell_length = 20
                
                # Calculate actual cell position from real box positions
                actual_min_x = min(box['position']['x'] for box in cell['boxes']) if cell['boxes'] else cell['position']['x']
                actual_min_y = min(box['position']['y'] for box in cell['boxes']) if cell['boxes'] else cell['position']['y']
                
                # Calculate cell height
                cell_height = 0
                if cell['boxes']:
                    min_z = min(box['position']['z'] for box in cell['boxes'])
                    max_z = max(box['position']['z'] + box['dimensions']['height'] for box in cell['boxes'])
                    cell_height = max_z - min_z
                
                # Get detailed box information
                boxes_info = []
                for box in cell['boxes']:
                    boxes_info.append({
                        'code': box['code'],
                        'dimensions': box['dimensions'],
                        'position': box['position']
                    })
                
                formatted_cells.append({
                    'cell': i + 1,
                    'content': content['text'],
                    'total_boxes': content['count'],
                    'columns': cell['columns'],
                    'position': {'x': actual_min_x, 'y': actual_min_y},  # Use actual position
                    'items': content['breakdown'],
                    'dimensions': {
                        'width': round(cell_width, 1),
                        'length': round(cell_length, 1),
                        'height': round(cell_height, 1)
                    },
                    'boxes': boxes_info  # Detailed box information
                })
            
            rows.append({
                'row': len(rows) + 1,
                'height': round(row_height, 1),
                'cells': formatted_cells
            })
        
        return rows
    
    def _aggregate_boxes(self, boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate boxes thành format: 1A+1B+3C+9D
        """
        code_counts = Counter([box['code'] for box in boxes])
        
        # Sort by box order (A -> K2)
        sorted_codes = sorted(code_counts.items(), 
                            key=lambda x: self._box_order(x[0]))
        
        text = "+".join([f"{count}{code}" for code, count in sorted_codes])
        
        return {
            'text': text,
            'count': len(boxes),
            'breakdown': dict(sorted_codes)
        }
    
    def _calculate_utilization(self, container: Dict[str, Any]) -> float:
        """Calculate space utilization % based on actual bounding box"""
        if not container['boxes']:
            return 0.0
        
        used_volume = sum(
            box['dimensions']['width'] * 
            box['dimensions']['length'] * 
            box['dimensions']['height']
            for box in container['boxes']
        )
        
        # Calculate actual bounding box of used space
        if container['boxes']:
            min_x = min(box['position']['x'] for box in container['boxes'])
            max_x = max(box['position']['x'] + box['dimensions']['width'] for box in container['boxes'])
            min_y = min(box['position']['y'] for box in container['boxes'])
            max_y = max(box['position']['y'] + box['dimensions']['length'] for box in container['boxes'])
            min_z = min(box['position']['z'] for box in container['boxes'])
            max_z = max(box['position']['z'] + box['dimensions']['height'] for box in container['boxes'])
            
            actual_width = max_x - min_x
            actual_length = max_y - min_y
            actual_height = max_z - min_z
            
            actual_volume = actual_width * actual_length * actual_height
        else:
            actual_volume = 1  # Avoid division by zero
        
        # Return utilization based on actual used space vs bounding box
        if actual_volume > 0:
            return round((used_volume / actual_volume) * 100, 2)
        else:
            return 0.0
    
    def _box_order(self, code: str) -> int:
        """Convert box code to order number (A=1, B=2, ..., K2=37)"""
        return self.box_order.index(code) if code in self.box_order else 999
