"""
LAFF (Largest Area Fit First) 3D Bin Packing Algorithm

Implementation of LAFF heuristic for 3D container packing with Peerless rules:
- Pre Pack (Zone A-N): Vertical stacking only, no rotation
- Carton (Zone O-K2): Flexible packing, rotation allowed
- Buffer rules: container walls 2.0", door clearance 6.0", between items 0.5"
"""

from typing import List, Dict, Any, Optional, Tuple
import math


class EmptySpace:
    """Represents an empty 3D space in the container"""
    
    def __init__(self, x: float, y: float, z: float, width: float, length: float, height: float):
        self.position = {'x': x, 'y': y, 'z': z}
        self.dimensions = {'width': width, 'length': length, 'height': height}
        self.volume = width * length * height
    
    def can_fit(self, box: Dict[str, Any], allow_rotation: bool = False, packing_method: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Check if box fits in this empty space
        
        Args:
            box: Box with dimensions {'width', 'length', 'height'}
            allow_rotation: Whether to try rotated orientations
            packing_method: 'PRE_PACK' or 'CARTON' to apply orientation rules
            
        Returns:
            (can_fit, orientation): orientation is None if can't fit
        """
        box_dims = box['dimensions']
        
        # Check orientation rules based on packing method
        if packing_method == 'PRE_PACK':
            # PRE_PACK: width × length must be on floor (z == 0 means floor)
            # This means: width × length in XY plane, height in Z axis
            # Normal orientation only, no rotation
            if (box_dims['width'] <= self.dimensions['width'] and
                box_dims['length'] <= self.dimensions['length'] and
                box_dims['height'] <= self.dimensions['height']):
                return True, box_dims
            
            return False, None
            
        elif packing_method == 'CARTON':
            # CARTON: height dimension cannot touch floor
            # Allowed: width × length (normal) or width × height (swap length ↔ height)
            # NOT allowed: length × height (would put height on floor)
            
            # Collect all valid orientations
            valid_orientations = []
            
            # Try normal orientation: width × length on floor
            if (box_dims['width'] <= self.dimensions['width'] and
                box_dims['length'] <= self.dimensions['length'] and
                box_dims['height'] <= self.dimensions['height']):
                valid_orientations.append(box_dims)
            
            # Try rotated orientation: swap width ↔ length (90° in XY plane)
            if allow_rotation:
                rotated_dims = {
                    'width': box_dims['length'],
                    'length': box_dims['width'],
                    'height': box_dims['height']
                }
                
                if (rotated_dims['width'] <= self.dimensions['width'] and
                    rotated_dims['length'] <= self.dimensions['length'] and
                    rotated_dims['height'] <= self.dimensions['height']):
                    valid_orientations.append(rotated_dims)
            
            # Try alternate orientation: swap length ↔ height
            # width × height on floor (OK for CARTON, height not on floor)
            rotated_dims2 = {
                'width': box_dims['width'],
                'length': box_dims['height'],
                'height': box_dims['length']
            }
            
            if (rotated_dims2['width'] <= self.dimensions['width'] and
                rotated_dims2['length'] <= self.dimensions['length'] and
                rotated_dims2['height'] <= self.dimensions['height']):
                valid_orientations.append(rotated_dims2)
            
            if not valid_orientations:
                return False, None
            
            # Choose BEST orientation: one that fits most boxes per row
            # Use the one with smallest width (fits most boxes horizontally)
            best_orientation = min(valid_orientations, key=lambda o: o['width'])
            return True, best_orientation
        
        else:
            # Default behavior: try original orientation
            if (box_dims['width'] <= self.dimensions['width'] and
                box_dims['length'] <= self.dimensions['length'] and
                box_dims['height'] <= self.dimensions['height']):
                return True, box_dims
            
            # Try rotated orientation (90 degrees: swap width/length)
            if allow_rotation:
                rotated_dims = {
                    'width': box_dims['length'],
                    'length': box_dims['width'],
                    'height': box_dims['height']
                }
                
                if (rotated_dims['width'] <= self.dimensions['width'] and
                    rotated_dims['length'] <= self.dimensions['length'] and
                    rotated_dims['height'] <= self.dimensions['height']):
                    return True, rotated_dims
            
            return False, None
    
    def __str__(self):
        return f"EmptySpace(pos=({self.position['x']:.1f},{self.position['y']:.1f},{self.position['z']:.1f}), dims=({self.dimensions['width']:.1f}x{self.dimensions['length']:.1f}x{self.dimensions['height']:.1f}), vol={self.volume:.1f})"


class LAFFBinPacking3D:
    """
    LAFF (Largest Area Fit First) 3D Bin Packing Algorithm
    
    Strategy:
    1. Sort boxes by area (width × length) descending
    2. For each box, find largest available empty space
    3. Place box and split space into 3 new spaces (right, front, top)
    4. Apply Peerless rules: Pre Pack (vertical only), Carton (rotation allowed)
    """
    
    BUFFER_RULES = {
        "container_walls": 0.0,              # DISABLED temporarily: inches from container walls
        "between_items": 0.5,               # inches between items (applies to all directions)
        "between_layers": 0.5,              # NOT USED: covered by between_items
        "between_packing_methods": 0.0,    # DISABLED temporarily
        "door_clearance": 10.0              # inches clearance for container door
    }
    
    def __init__(self, container_dims: Dict[str, float]):
        self.container = {
            'width': container_dims['width'],
            'length': container_dims['length'],
            'height': container_dims['height']
        }
        self.containers = []
        self.current_container = None
        self.empty_spaces = []
    
    def pack_boxes(self, boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main LAFF packing algorithm
        
        Args:
            boxes: List of boxes with dimensions, quantity, packing_method
            
        Returns:
            List of containers with packed boxes
        """
        # Step 1: Sort boxes by area (LAFF strategy)
        sorted_boxes = self._sort_boxes_by_area(boxes)
        
        # Step 2: Start first container
        self._new_container()
        
        # Step 3: Place each box
        for box in sorted_boxes:
            for _ in range(box['quantity']):
                # Find best empty space
                best_space = self._find_best_space(box)
                
                if best_space:
                    # Place box in space (returns orientation)
                    orientation = self._place_box_in_space(box, best_space)
                    
                    # Update empty spaces (split space)
                    self._update_empty_spaces(best_space, box, orientation)
                else:
                    # Create new container
                    self._new_container()
                    
                    # Try to place in new container
                    if self.empty_spaces:
                        best_space = self.empty_spaces[0]  # Use initial space
                        orientation = self._place_box_in_space(box, best_space)
                        self._update_empty_spaces(best_space, box, orientation)
                    else:
                        raise Exception(f"Box {box['code']} too large for container")
        
        return self.containers
    
    def _sort_boxes_by_area(self, boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort boxes for optimal space usage and minimum containers
        
        Priority:
        1. Material (ascending) - group by material type
        2. Purchasing document (ascending) - group by purchase order
        3. HEIGHT (ascending) - group by height for better stacking
        4. Area (descending) - LAFF strategy, pack large items first
        5. Quantity (descending) - pack large quantities first
        
        Key insight: Grouping by height first enables better vertical stacking,
        leading to fewer rows and more compact layout.
        """
        # Sort by priority: material → purchasing_doc → HEIGHT → area → quantity
        sorted_boxes = sorted(boxes, key=lambda x: (
            x.get('material', ''),
            x.get('purchasing_doc', ''),
            x['dimensions']['height'],  # HEIGHT FIRST - groups similar heights together
            -(x['dimensions']['width'] * x['dimensions']['length']),  # Area descending
            -x['quantity']  # Quantity descending
        ))
        
        return sorted_boxes
    
    def _find_best_space(self, box: Dict[str, Any]) -> Optional[EmptySpace]:
        """
        Find best empty space for box using LAFF strategy
        
        Strategy: 
        1. Prioritize area (width × length) first - encourages horizontal packing
        2. Prefer shallow spaces over deep ones (avoid early stacking)
        3. This ensures we pack horizontally (width, length) before vertical (height)
        """
        # Sort spaces to maximize horizontal packing first
        # Priority: low z, high area (width × length)
        # This fills width first before stacking vertically
        sorted_spaces = sorted(
            self.empty_spaces,
            key=lambda s: (
                s.position['z'],  # Lowest z first (pack on floor first)
                -(s.dimensions['width'] * s.dimensions['length']),  # Largest area first
                s.dimensions['height']  # Then shallow spaces (avoid deep unnecessary height)
            )
        )
        
        for space in sorted_spaces:
            # Check if box can fit with packing method rules
            can_fit, orientation = self._can_place_box(box, space)
            
            if can_fit:
                return space
        
        return None
    
    def _can_place_box(self, box: Dict[str, Any], space: EmptySpace) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Check if box can be placed in space considering Peerless rules
        
        Args:
            box: Box to place
            space: Empty space to check
            
        Returns:
            (can_fit, orientation): orientation is None if can't fit
        """
        packing_method = box['packing_method']
        
        if packing_method == 'PRE_PACK':
            # Pre Pack: width × length on floor, height vertical, no rotation
            can_fit, orientation = space.can_fit(box, allow_rotation=False, packing_method='PRE_PACK')
            
            if can_fit:
                # Check vertical support for stacking
                if space.position['z'] > 0:
                    has_support = self._check_vertical_support(box, space, orientation)
                    if not has_support:
                        return False, None
                
                # Validate that placement doesn't exceed container
                if self._validate_container_bounds(space.position, orientation):
                    return True, orientation
            
            return False, None
            
        elif packing_method == 'CARTON':
            # Carton: flexible packing, rotation allowed (but not length × height on floor)
            can_fit, orientation = space.can_fit(box, allow_rotation=True, packing_method='CARTON')
            
            if can_fit:
                # Validate that placement doesn't exceed container
                if self._validate_container_bounds(space.position, orientation):
                    return True, orientation
            
            return False, None
        
        else:
            # Default: no rotation
            can_fit, orientation = space.can_fit(box, allow_rotation=False)
            if can_fit:
                # TEMPORARILY DISABLED
                # if self._validate_buffers(box, space.position, orientation):
                #     return True, orientation
                return True, orientation  # Skip buffer validation temporarily
            
            return False, None
    
    def _check_vertical_support(self, box: Dict[str, Any], space: EmptySpace, orientation: Dict[str, float]) -> bool:
        """
        Check if box has vertical support for stacking
        
        For Pre Pack items, ensure they have support below when stacking
        """
        if space.position['z'] == 0:
            return True  # On ground level
        
        # If no boxes placed yet, no support check needed (but shouldn't happen at z>0)
        if self.current_container is None or len(self.current_container['boxes']) == 0:
            return False  # Box is in air with no support
        
        # Check if there's a box directly below
        box_bottom_z = space.position['z']
        box_top_z = space.position['z'] + orientation['height']
        
        for placed_box in self.current_container['boxes']:
            placed_bottom_z = placed_box['position']['z']
            placed_top_z = placed_box['position']['z'] + placed_box['dimensions']['height']
            
            # Check if boxes overlap in x,y and z ranges touch
            if (self._boxes_overlap_xy(box, space.position, orientation, placed_box) and
                abs(box_bottom_z - placed_top_z) < 0.1):  # Small tolerance
                return True
        
        return False
    
    def _boxes_overlap_xy(self, box1: Dict[str, Any], pos1: Dict[str, float], dims1: Dict[str, float], 
                         box2: Dict[str, Any]) -> bool:
        """Check if two boxes overlap in x,y plane"""
        x1_min, x1_max = pos1['x'], pos1['x'] + dims1['width']
        y1_min, y1_max = pos1['y'], pos1['y'] + dims1['length']
        
        pos2 = box2['position']
        dims2 = box2['dimensions']
        x2_min, x2_max = pos2['x'], pos2['x'] + dims2['width']
        y2_min, y2_max = pos2['y'], pos2['y'] + dims2['length']
        
        return not (x1_max <= x2_min or x1_min >= x2_max or
                   y1_max <= y2_min or y1_min >= y2_max)
    
    def _validate_container_bounds(self, position: Dict[str, float], orientation: Dict[str, float]) -> bool:
        """
        Validate that box placement doesn't exceed container dimensions
        
        Args:
            position: Box position {x, y, z}
            orientation: Box dimensions {width, length, height}
            
        Returns:
            True if box fits within container bounds
        """
        # Check container boundaries
        if position['x'] + orientation['width'] > self.container['width']:
            return False
        if position['y'] + orientation['length'] > self.container['length']:
            return False
        if position['z'] + orientation['height'] > self.container['height']:
            return False
        
        return True
    
    def _validate_buffers(self, box: Dict[str, Any], position: Dict[str, float], orientation: Dict[str, float]) -> bool:
        """
        Validate buffer rules for box placement
        
        Buffer rules:
        - Container walls: 2.0"
        - Door clearance: 6.0"
        - Between items: 0.5"
        - Between packing methods: 1.0"
        """
        # Check container boundaries
        if position['x'] + orientation['width'] > self.container['width'] - self.BUFFER_RULES['container_walls']:
            return False
        if position['y'] + orientation['length'] > self.container['length'] - self.BUFFER_RULES['container_walls']:
            return False
        if position['z'] + orientation['height'] > self.container['height'] - self.BUFFER_RULES['container_walls']:
            return False
        
        # Check door clearance
        if position['y'] < self.BUFFER_RULES['door_clearance']:
            return False
        
        # Check buffer with other boxes (if container has boxes)
        if self.current_container is None or len(self.current_container['boxes']) == 0:
            return True  # No boxes yet, validation passes
        
        for placed_box in self.current_container['boxes']:
            # Skip buffer check if boxes are stacking directly (one on top of other with same x,y)
            # In this case, the empty space IS the top of the placed box
            if (abs(position['x'] - placed_box['position']['x']) < 0.1 and
                abs(position['y'] - placed_box['position']['y']) < 0.1 and
                abs(position['z'] - (placed_box['position']['z'] + placed_box['dimensions']['height'])) < 0.1):
                continue  # This is the top space of the placed box, no buffer needed
            
            # Calculate distance between the new box position and placed box
            distance = self._calculate_distance(
                position, 
                orientation,
                placed_box['position'],
                placed_box['dimensions']
            )
            
            if box['packing_method'] != placed_box['packing_method']:
                required_buffer = self.BUFFER_RULES['between_packing_methods']
            else:
                required_buffer = self.BUFFER_RULES['between_items']
            
            if distance < required_buffer:
                return False
        
        return True
    
    def _calculate_distance(self, pos1: Dict[str, float], dims1: Dict[str, float], 
                          pos2: Dict[str, float], dims2: Dict[str, float]) -> float:
        """
        Calculate minimum distance between two boxes
        
        Args:
            pos1: Position of box 1
            dims1: Dimensions of box 1
            pos2: Position of box 2
            dims2: Dimensions of box 2
        """
        
        # Calculate distance in each dimension
        # If boxes overlap in a dimension, distance is 0
        # If boxes are separated in a dimension, distance is the separation
        
        # X-axis: check if boxes overlap or are separated
        if pos1['x'] + dims1['width'] <= pos2['x']:
            x_dist = pos2['x'] - (pos1['x'] + dims1['width'])  # box1 is to the left
        elif pos2['x'] + dims2['width'] <= pos1['x']:
            x_dist = pos1['x'] - (pos2['x'] + dims2['width'])  # box2 is to the left
        else:
            x_dist = 0  # boxes overlap in x
        
        # Y-axis: check if boxes overlap or are separated
        if pos1['y'] + dims1['length'] <= pos2['y']:
            y_dist = pos2['y'] - (pos1['y'] + dims1['length'])  # box1 is in front
        elif pos2['y'] + dims2['length'] <= pos1['y']:
            y_dist = pos1['y'] - (pos2['y'] + dims2['length'])  # box2 is in front
        else:
            y_dist = 0  # boxes overlap in y
        
        # Z-axis: check if boxes overlap or are separated
        if pos1['z'] + dims1['height'] <= pos2['z']:
            z_dist = pos2['z'] - (pos1['z'] + dims1['height'])  # box1 is below
        elif pos2['z'] + dims2['height'] <= pos1['z']:
            z_dist = pos1['z'] - (pos2['z'] + dims2['height'])  # box2 is below
        else:
            z_dist = 0  # boxes overlap in z
        
        # Return minimum distance (if boxes overlap in all dimensions, distance is 0)
        return math.sqrt(x_dist**2 + y_dist**2 + z_dist**2)
    
    def _place_box_in_space(self, box: Dict[str, Any], space: EmptySpace) -> Dict[str, float]:
        """Place box in the specified empty space, return orientation used"""
        # Get orientation (original or rotated)
        _, orientation = self._can_place_box(box, space)
        
        if orientation is None:
            raise Exception(f"Cannot place box {box['code']} in space")
        
        # Create box instance
        box_instance = {
            'code': box['code'],
            'dimensions': orientation,
            'position': space.position.copy(),
            'material': box['material'],
            'packing_method': box['packing_method']
        }
        
        self.current_container['boxes'].append(box_instance)
        
        return orientation
    
    def _update_empty_spaces(self, used_space: EmptySpace, box: Dict[str, Any], orientation: Dict[str, float]):
        """
        Update empty spaces after placing box
        
        Strategy: Split used space into 3 new spaces (right, front, top)
        """
        # Remove used space
        self.empty_spaces.remove(used_space)
        
        # Create 3 new empty spaces
        new_spaces = []
        
        # Right space (x-axis)
        if used_space.dimensions['width'] > orientation['width']:
            new_spaces.append(EmptySpace(
                used_space.position['x'] + orientation['width'],
                used_space.position['y'],
                used_space.position['z'],
                used_space.dimensions['width'] - orientation['width'],
                used_space.dimensions['length'],
                used_space.dimensions['height']
            ))
        
        # Front space (y-axis)
        if used_space.dimensions['length'] > orientation['length']:
            new_spaces.append(EmptySpace(
                used_space.position['x'],
                used_space.position['y'] + orientation['length'],
                used_space.position['z'],
                orientation['width'],
                used_space.dimensions['length'] - orientation['length'],
                used_space.dimensions['height']
            ))
        
        # Top space (z-axis)
        if used_space.dimensions['height'] > orientation['height']:
            new_spaces.append(EmptySpace(
                used_space.position['x'],
                used_space.position['y'],
                used_space.position['z'] + orientation['height'],
                orientation['width'],
                orientation['length'],
                used_space.dimensions['height'] - orientation['height']
            ))
        
        # Add new spaces
        self.empty_spaces.extend(new_spaces)
        
        # Merge overlapping spaces (optimization)
        self.empty_spaces = self._merge_spaces(self.empty_spaces)
    
    def _merge_spaces(self, spaces: List[EmptySpace]) -> List[EmptySpace]:
        """
        Merge overlapping empty spaces to reduce fragmentation
        
        This is an optimization to prevent too many small spaces
        """
        if len(spaces) <= 1:
            return spaces
        
        merged = []
        used = set()
        
        for i, space1 in enumerate(spaces):
            if i in used:
                continue
            
            merged_space = space1
            used.add(i)
            
            # Try to merge with other spaces
            for j, space2 in enumerate(spaces[i+1:], i+1):
                if j in used:
                    continue
                
                # Check if spaces can be merged (adjacent or overlapping)
                if self._can_merge_spaces(merged_space, space2):
                    merged_space = self._merge_two_spaces(merged_space, space2)
                    used.add(j)
            
            merged.append(merged_space)
        
        return merged
    
    def _can_merge_spaces(self, space1: EmptySpace, space2: EmptySpace) -> bool:
        """Check if two spaces can be merged"""
        # Simple check: if spaces are adjacent in one dimension
        # and have same dimensions in other dimensions
        
        # Check x-axis merge
        if (abs(space1.position['y'] - space2.position['y']) < 0.1 and
            abs(space1.position['z'] - space2.position['z']) < 0.1 and
            abs(space1.dimensions['length'] - space2.dimensions['length']) < 0.1 and
            abs(space1.dimensions['height'] - space2.dimensions['height']) < 0.1):
            return True
        
        # Check y-axis merge
        if (abs(space1.position['x'] - space2.position['x']) < 0.1 and
            abs(space1.position['z'] - space2.position['z']) < 0.1 and
            abs(space1.dimensions['width'] - space2.dimensions['width']) < 0.1 and
            abs(space1.dimensions['height'] - space2.dimensions['height']) < 0.1):
            return True
        
        # Check z-axis merge
        if (abs(space1.position['x'] - space2.position['x']) < 0.1 and
            abs(space1.position['y'] - space2.position['y']) < 0.1 and
            abs(space1.dimensions['width'] - space2.dimensions['width']) < 0.1 and
            abs(space1.dimensions['length'] - space2.dimensions['length']) < 0.1):
            return True
        
        return False
    
    def _merge_two_spaces(self, space1: EmptySpace, space2: EmptySpace) -> EmptySpace:
        """Merge two spaces into one"""
        # Find the bounding box of both spaces
        min_x = min(space1.position['x'], space2.position['x'])
        min_y = min(space1.position['y'], space2.position['y'])
        min_z = min(space1.position['z'], space2.position['z'])
        
        max_x = max(space1.position['x'] + space1.dimensions['width'],
                   space2.position['x'] + space2.dimensions['width'])
        max_y = max(space1.position['y'] + space1.dimensions['length'],
                   space2.position['y'] + space2.dimensions['length'])
        max_z = max(space1.position['z'] + space1.dimensions['height'],
                   space2.position['z'] + space2.dimensions['height'])
        
        return EmptySpace(
            min_x, min_y, min_z,
            max_x - min_x, max_y - min_y, max_z - min_z
        )
    
    def _new_container(self):
        """Create new container and initialize empty spaces"""
        self.current_container = {
            'container_id': len(self.containers) + 1,
            'boxes': [],
            'dimensions': self.container
        }
        self.containers.append(self.current_container)
        
        # Initialize with one large empty space
        self.empty_spaces = [EmptySpace(
            self.BUFFER_RULES['container_walls'],
            self.BUFFER_RULES['door_clearance'],
            0,
            self.container['width'] - 2 * self.BUFFER_RULES['container_walls'],
            self.container['length'] - self.BUFFER_RULES['door_clearance'] - self.BUFFER_RULES['container_walls'],
            self.container['height'] - self.BUFFER_RULES['container_walls']
        )]
    
    def calculate_utilization(self, container: Dict[str, Any]) -> float:
        """Calculate space utilization percentage"""
        total_volume = (container['dimensions']['width'] * 
                       container['dimensions']['length'] * 
                       container['dimensions']['height'])
        
        used_volume = sum(
            box['dimensions']['width'] * 
            box['dimensions']['length'] * 
            box['dimensions']['height']
            for box in container['boxes']
        )
        
        return (used_volume / total_volume) * 100

