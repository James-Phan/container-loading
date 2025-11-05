"""
FastAPI app với Bin Packing Algorithm
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from laff_bin_packing_3d import LAFFBinPacking3D
from guided_packing_3d import GuidedPackingAlgorithm
from z_first_packing_3d import ZFirstPackingAlgorithm
from simple_index_packing_3d import SimpleIndexPackingAlgorithm
from output_formatter_3d import OutputFormatter3D
import os

app = FastAPI(
    title="Container Layout Optimization - Bin Packing API",
    description="API for Peerless container layout optimization with bin packing algorithm.",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Container dimensions (fixed)
CONTAINER_DIMS = {
    "width": 92.5,
    "length": 473,
    "height": 106
}


class Box(BaseModel):
    code: str = Field(..., example="A")
    dimensions: Dict[str, float] = Field(..., example={"width": 19, "length": 34, "height": 3})
    quantity: int = Field(..., example=1)
    material: str = Field(..., example="BTAHV-H5B0036")
    packing_method: str = Field(..., example="PRE_PACK")
    # Optional fields
    case_pack: str = Field(default="", example="AZ")
    purchasing_doc: str = Field(default="", example="4900145614")
    building_door: str = Field(default="", example="MIL1")
    sort_order: Optional[int] = Field(default=None, description="Optional sort order field")
    
    model_config = ConfigDict(extra="allow")  # Allow extra fields (Pydantic v2 syntax)


class CalculateRequest(BaseModel):
    boxes: List[Box]
    algorithm: Optional[str] = Field(default="laff", description="Packing algorithm: 'laff', 'guided', 'z_first', or 'simple_index'")


class LayoutResult(BaseModel):
    success: bool
    layout: Dict[str, Any]


@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok", "version": "3.0.0", "algorithms": ["laff", "guided", "z_first", "simple_index"]}


@app.get("/api/test-data", summary="Get Test Data")
async def get_test_data():
    """Return test data from test_data_real_3d.json"""
    try:
        import os
        import json
        
        # Load test data file
        file_path = os.path.join(os.path.dirname(__file__), 'test_data_real_3d.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normalize sort_order field: convert to int or None
        # This ensures compatibility with Pydantic Box model
        if 'boxes' in data:
            for box in data['boxes']:
                if 'sort_order' in box:
                    # Convert to int if possible, else set to None
                    try:
                        if box['sort_order'] is None or box['sort_order'] == '':
                            box['sort_order'] = None
                        else:
                            box['sort_order'] = int(box['sort_order'])
                    except (ValueError, TypeError):
                        # If conversion fails, set to None
                        box['sort_order'] = None
                else:
                    # If sort_order field is missing, set to None
                    box['sort_order'] = None
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading test data: {str(e)}")


@app.options("/calculate")
async def calculate_layout_options():
    """Handle CORS preflight request"""
    return {"message": "OK"}

@app.post("/calculate", response_model=LayoutResult, summary="Calculate Container Layout with LAFF 3D Bin Packing")
async def calculate_layout(request: CalculateRequest):
    """
    Calculates the optimal container layout using bin packing algorithms.
    
    Available algorithms:
    - 'laff': LAFF (Largest Area Fit First) - sorts by area, finds largest space
    - 'guided': Guided Packing - uses manual layout template, fills width (X) before height (Z)
    - 'z_first': Z-First Packing - fills height (Z) before width (X) to maximize vertical utilization
    - 'simple_index': Simple Index-Based - packs boxes theo thứ tự index trong array, fill cell-by-cell
    
    Recommended: Use 'guided', 'z_first', or 'simple_index' for better packing efficiency
    """
    try:
        # Convert boxes to list of dicts (Pydantic v2: use model_dump, v1: dict still works)
        try:
            boxes = [box.model_dump() for box in request.boxes]  # Pydantic v2
        except AttributeError:
            boxes = [box.dict() for box in request.boxes]  # Fallback for Pydantic v1
        
        # Choose algorithm
        algorithm = request.algorithm or "laff"
        
        if algorithm == "guided":
            # Use Guided Packing with manual template (X-first)
            manual_template_path = os.path.join(
                os.path.dirname(__file__),
                "manual_layout.json"
            )
            packer = GuidedPackingAlgorithm(CONTAINER_DIMS, manual_template_path)
            containers = packer.pack_boxes(boxes)
        elif algorithm == "z_first":
            # Use Z-First Packing (Z-first, stack vertically before spreading horizontally)
            packer = ZFirstPackingAlgorithm(CONTAINER_DIMS)
            containers = packer.pack_boxes(boxes)
        elif algorithm == "simple_index":
            # Use Simple Index-Based Cell Packing (pack theo thứ tự index, fill cell-by-cell)
            packer = SimpleIndexPackingAlgorithm(CONTAINER_DIMS)
            containers = packer.pack_boxes(boxes)
        else:
            # Use LAFF as default/fallback
            packer = LAFFBinPacking3D(CONTAINER_DIMS)
            containers = packer.pack_boxes(boxes)
        
        # Format output
        formatter = OutputFormatter3D()
        result = formatter.format(containers)
        
        # Add algorithm info to result
        result['algorithm'] = algorithm
        
        return LayoutResult(
            success=True,
            layout=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/algorithm-info", summary="Algorithm Information")
async def algorithm_info():
    """Get information about the LAFF 3D bin packing algorithm"""
    return {
        "algorithm": "LAFF (Largest Area Fit First) 3D Bin Packing",
        "features": [
            "Sort boxes by area (width × length) descending",
            "Place each box in largest available empty space",
            "Split empty spaces after placement (right, front, top)",
            "Pre Pack: vertical stacking only, no rotation",
            "Carton: flexible packing, rotation allowed (90°)",
            "Target utilization: >15%"
        ],
        "buffer_rules": {
            "container_walls": "2.0 inches from container walls",
            "door_clearance": "6.0 inches clearance for door",
            "between_items": "0.5 inches between items",
            "between_packing_methods": "1.0 inches between PRE_PACK and CARTON"
        },
        "container": {
            "width": "92 inches",
            "length": "473 inches",
            "height": "102 inches"
        },
        "packing_methods": {
            "prepack": "A-N (vertical stacking only, stability checked)",
            "carton": "O-K2 (flexible packing, rotation allowed)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
