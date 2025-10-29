# LAFF 3D Bin Packing Algorithm - Requirements

## Overview

LAFF (Largest Area Fit First) 3D bin packing algorithm for Peerless container layout optimization.

## Container Specifications

- **Dimensions**: 92" (width) × 473" (length) × 102" (height)
- **Total Volume**: 4,390,232 cubic inches

## Buffer Rules

- **Container walls**: 0.0" (temporarily disabled for testing)
- **Door clearance**: 10.0" from container door
- **Between items**: 0.5" minimum spacing between items (all directions)
- **Between packing methods**: 0.0" (temporarily disabled)

## Orientation Rules

### PRE_PACK (Zone A-N)

**Constraint**: Face with WIDTH × HEIGHT **CANNOT** touch the floor.

**Meaning**: The floor contact face must be WIDTH × LENGTH

- Box is placed vertically (height dimension is vertical)
- **NO rotation allowed** (width × length always down)
- Supports vertical stacking
- Check vertical support when stacking above other boxes

**Example**:
- Box dimensions: width=19", length=34", height=6"
- Floor contact: 19" × 34" face (width × length)
- Height: 6" (vertical dimension)

### CARTON (Zone O-K2)

**Constraint**: Face with HEIGHT **CANNOT** touch the floor.

**Meaning**: The floor contact face cannot contain the height dimension

- Allowed orientations:
  - WIDTH × LENGTH (normal orientation)
  - WIDTH × HEIGHT (rotated 90° on length-axis, swap length ↔ height)
  - **NOT allowed**: LENGTH × HEIGHT (would put height dimension on floor)

- Rotation 90° allowed (swap width ↔ length only, keep height)
- More flexible packing

**Example**:
- Box dimensions: width=24", length=16", height=9"
- Allowed:
  - Floor: 24" × 16" (normal)
  - Floor: 24" × 9" (rotate, swap length↔height)
- **NOT allowed**:
  - Floor: 16" × 9" (would put height=24" down)

## Sorting Strategy

Boxes must be sorted in this priority order:

1. **Material** (ascending)
2. **Purchasing Document** (ascending)
3. **Area** (descending: width × length)
4. **Quantity** (descending: pack large quantities first)

**Rationale**: Group by material and purchase order to optimize logistics and minimize box types per container.

## Rotation Optimization for CARTON

**Goal**: Maximize boxes per row by choosing best orientation

**Strategy**:
1. Try ALL valid orientations for CARTON boxes
2. Calculate how many boxes fit in container width for each orientation
3. Choose orientation that fits **MOST boxes per row**

**Example - J2 box (30"×17"×5") in container (92.5" wide)**:
- Normal orientation: 30" width → floor(92.5/30) = **3 boxes/row**
- Rotated (swap width↔length): 17" width → floor(92.5/17) = **5 boxes/row** ✓ **BEST**
- Rotated (swap length↔height): 5" width → floor(92.5/5) = **18 boxes/row**, but height=30" > container height=106" ✓ Also good if fits

**Rotation Decision Logic**:
```
For CARTON box with dimensions (W, L, H):
1. Try W×L on floor (height H)
2. Try L×W on floor (height H) - rotate 90° in XY plane
3. Try W×H on floor (height L) - rotate 90° along length axis
4. Try L×H on floor? NO - would put height dimension on floor (INVALID)

Among valid orientations:
- Calculate: boxes_per_row = floor(container_width / box_width_on_floor)
- Choose orientation with MAX boxes_per_row
```

**Key Benefit**: Same manual layout uses 210" length vs algorithm 466" length because manual rotates boxes optimally.

## Algorithm Strategy

### LAFF (Largest Area Fit First)

1. **Sort boxes** by material → purchasing_doc → area (descending)
2. **For each box**:
   - Find largest available empty space that fits
   - Place box in space (apply orientation rules)
   - Split used space into 3 new spaces: right, front, top
3. **Continue** until all boxes placed or container full

### Space Prioritization

When selecting among multiple available spaces:

1. Prioritize by **area** (width × length) - encourages horizontal packing
2. Then by **height** (prefer shallow over deep) - avoid early vertical stacking
3. Check orientation rules before placement
4. Validate container boundaries

## Output Format

### Grid Layout

```
Row 1 (Height 34.5"):
  Cell 1: 1A+1B+3C+9D+1E+5F (60 boxes)
  Cell 2: 3F+13G+1H+1I (18 boxes)
  ...
```

### Row Definition

- **Row**: A horizontal layer at same Y position (front-to-back)
- **Cell**: A group of boxes at same X,Y position (may have multiple Z levels)
- **Height**: Maximum height of all boxes in cells within this row
- **Columns**: Box codes present in this cell

### Calculation Rules

- Row height = **MAX** of cell heights (NOT sum)
- Each cell may contain stacked boxes (multiple Z levels)
- Cells are grouped by Y position to form rows
- Cells in a row sorted by X position (left-to-right)

## Constraints

### Container Limits

- ✓ Total height used ≤ 102" (container height)
- ✓ Total length used ≤ 473" (container length)
- ✓ Total width used ≤ 92" (container width)
- ✓ No box exceeds container boundaries

### Positioning Rules

- Start position: x=0, y=10 (door clearance), z=0
- Each box position must validate against container dimensions
- Box dimensions after placement: `position + dimensions ≤ container_dimensions`

## Success Criteria

1. **All boxes fit**: No box exceeds container dimensions
2. **Row heights valid**: All row heights ≤ 102"
3. **Total length valid**: Cumulative length ≤ 473"
4. **Orientation correct**: PRE_PACK and CARTON rules followed
5. **Sorting correct**: Boxes sorted by material → purchasing_doc → area
6. **Utilization**: ≥ 15% (used volume / container volume)
7. **Container count**: Minimize containers used (ideally 1-2)

## Test Data Reference

**Input File**: `test_data_real_3d.json`

- Total boxes: 470
- PRE_PACK items: A-N (19 types)
- CARTON items: C2-K2 (9 types)
- Mixed materials: BTAHV, HATHP, BGTAP, FAGNP

## Error Handling

- If box cannot fit in any space, create new container
- If box exceeds container dimensions, raise error
- If no valid orientation, skip box (log warning)
- If vertical support missing for PRE_PACK, reject placement

