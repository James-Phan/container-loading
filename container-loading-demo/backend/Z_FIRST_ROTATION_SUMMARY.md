# Z-FIRST ROTATION RULES - SUMMARY VÀ REQUIREMENTS

## 📐 RULES CƠ BẢN

### PRE_PACK
**Rule:** Mặt có **chiều rộng (width) × chiều cao (height) KHÔNG được tiếp xúc với sàn**

**Nghĩa là:** Không được có mặt (W×H) hoặc (H×W) chạm sàn  
**Constraint:** Original height và width không được cùng chạm sàn

### CARTON
**Rule:** Mặt có **chiều cao (height) KHÔNG được tiếp xúc với sàn**

**Nghĩa là:** Bất kỳ mặt nào có dimension "original height" KHÔNG được nằm trên sàn  
**Constraint:** Original height luôn phải là chiều cao (vertical dimension)

---

## ✅ IMPLEMENTATION HIỆN TẠI - PRE_PACK

**File:** `z_first_packing_3d.py` lines 388-395

**Current code (cần update):**
```python
if packing_method == 'PRE_PACK':
    w, l, h = box['dimensions']['width'], box['dimensions']['length'], box['dimensions']['height']
    return [
        {'width': w, 'length': l, 'height': h},  # (w×l) chạm sàn ✓
        {'width': l, 'length': w, 'height': h},  # (l×w) chạm sàn - xoay 90° ✓
        {'width': l, 'length': h, 'height': w},  # (l×h) chạm sàn ✓
        {'width': h, 'length': l, 'height': w}   # (h×l) chạm sàn - xoay 90° ✓
    ]
```

**Should be updated to:**
```python
if packing_method == 'PRE_PACK':
    w, l, h = box['dimensions']['width'], box['dimensions']['length'], box['dimensions']['height']
    
    orientations = [
        {'width': w, 'length': l, 'height': h},  # (W×L, H) - Always allowed
        {'width': l, 'length': w, 'height': h},  # (L×W, H) - Always allowed
    ]
    
    # Only add swap orientations if Height > Length
    if h > l:
        orientations.append({'width': l, 'length': h, 'height': w})  # (L×H, W)
        orientations.append({'width': h, 'length': l, 'height': w})  # (H×L, W)
    
    return orientations
```

### Orientations được phép:

**Luôn cho phép (2 orientations):**
1. **`(W×L, H)`** - Original: width × length chạm sàn ✓
2. **`(L×W, H)`** - Rotate 90°: length × width chạm sàn ✓

**Chỉ khi Height > Length (thêm 2 orientations):**
3. **`(L×H, W)`** - Swap: length × height chạm sàn ✓ (chỉ khi H > L)
4. **`(H×L, W)`** - Swap + Rotate: height × length chạm sàn ✓ (chỉ khi H > L)

### Validation theo rule mới:

**Rule:** Swap orientations (L×H, W) và (H×L, W) chỉ hợp lệ khi **Height > Length**

**Example 1: Box 19" × 34" × 6"** (H=6, L=34)
- ✓ `(W×L, H)` = (19×34, 6) - Original
- ✓ `(L×W, H)` = (34×19, 6) - Rotate 90°
- ✗ `(L×H, W)` - KHÔNG vì H=6 < L=34
- ✗ `(H×L, W)` - KHÔNG vì H=6 < L=34
- **→ Chỉ có 2 orientations hợp lệ**

**Example 2: Box 17" × 19" × 25"** (H=25, L=19)  
- ✓ `(W×L, H)` = (17×19, 25) - Original
- ✓ `(L×W, H)` = (19×17, 25) - Rotate 90°
- ✓ `(L×H, W)` = (19×25, 17) - Swap (H > L)
- ✓ `(H×L, W)` = (25×19, 17) - Swap + Rotate
- **→ Có đủ 4 orientations**

---

## ✅ IMPLEMENTATION HIỆN TẠI - CARTON

**File:** `z_first_packing_3d.py` lines 397-401

```python
else:  # CARTON
    w, l, h = box['dimensions']['width'], box['dimensions']['length'], box['dimensions']['height']
    return [
        {'width': w, 'length': l, 'height': h},  # Đứng, hướng gốc
        {'width': l, 'length': w, 'height': h}   # Đứng, xoay 90°
    ]
```

### 2 Orientations được phép:

1. **`(W×L, H)`** - Original: width × length chạm sàn, height đứng ✓
2. **`(L×W, H)`** - Rotate 90°: length × width chạm sàn, height đứng ✓

### Validation:

- ✓ `(W×L, H)` - original height H đứng, KHÔNG chạm sàn ✓
- ✓ `(L×W, H)` - original height H đứng, KHÔNG chạm sàn ✓

### ❓ Có thiếu orientation (W×H, L)?

**Rule:** Mặt có original height không được chạm sàn  
**Orientation (W×H, L):** width×height chạm sàn, length đứng

- Original height được swap thành length (đứng)
- Length được swap thành height (chạm sàn)
- Width giữ nguyên

**→ Original height KHÔNG chạm sàn → HỢP LỆ!**

**Vậy có nên thêm orientation này?**

---

## 🔧 CÁCH THUẬT TOÁN CHỌN ORIENTATION

### Logic Selection (z_first_packing_3d.py lines 231-259)

```python
# Với mỗi box:
1. Try TẤT CẢ orientations từ get_all_orientations()
2. Filter: chỉ giữ orientations có 
   - box_w ≤ container_width 
   - box_h ≤ container_height
3. Check fit tại current position:
   - current_z + box_h ≤ container_height 
   - current_x + box_w ≤ container_width
4. Tính deviation từ average dimensions:
   - Nếu đã có boxes placed: 
     deviation = |box_l - avg_length| + |box_w - avg_width|
   - Nếu box đầu tiên: 
     deviation = |box_l - avg_length| 
     (prefer larger width if same)
5. Chọn orientation có MIN deviation
```

### Strategy:

- **Match dimensions** với boxes đã placed để tạo consistency trong row
- **Maximize spatial consistency** - các boxes có cùng length/width sẽ được xếp cạnh nhau
- Cải thiện utilization của row space

---

## 📊 PHÂN TÍCH: CÓ NÊN THÊM ORIENTATION (W×H) CHO CARTON?

### Example: Box J2 (30" × 17" × 5")

**Orientations hiện tại:**
- `(30×17, 5)`: width=30" → floor(92.5/30) = **3 boxes/row**
- `(17×30, 5)`: width=17" → floor(92.5/17) = **5 boxes/row** ✓ BEST

**Nếu thêm `(30×5, 17)` (swap length↔height):**
- `(30×5, 17)`: width=30", height=17" → floor(92.5/30) = **3 boxes/row**
- Không cải thiện

**Nếu thêm `(5×17, 30)` (swap và rotate):**
- `(5×17, 30)`: width=5", height=30" → floor(92.5/5) = **18 boxes/row**
- Nhưng height=30" > container height=106" → KHÔNG fit

**→ Với box này, 2 orientations hiện tại đã đủ**

### Example khác: Box có height nhỏ hơn (20×15×10)

**Orientations hiện tại:**
- `(20×15, 10)`: width=20" → floor(92.5/20) = **4 boxes/row**
- `(15×20, 10)`: width=15" → floor(92.5/15) = **6 boxes/row** ✓ BEST

**Nếu thêm `(20×10, 15)` (swap length↔height):**
- `(20×10, 15)`: width=20" → **4 boxes/row**

**Nếu thêm `(10×15, 20)` (swap và rotate):**
- `(10×15, 20)`: width=10" → floor(92.5/10) = **9 boxes/row**
- height=20" ≤ 106" → **CÓ THỂ FIT!**
- Original height=10 đứng → **HỢP LỆ!**

**→ CÓ THỂ cần thêm orientation này**

---

## ❓ QUYẾT ĐỊNH: CÓ THÊM ORIENTATION CHO CARTON?

### Option 1: Giữ nguyên (2 orientations)
```python
# CARTON: Chỉ 2 orientations
return [
    {'width': w, 'length': l, 'height': h},  # (W×L, H)
    {'width': l, 'length': w, 'height': h}   # (L×W, H)
]
```
✓ Đơn giản, đủ cho hầu hết cases  
✗ Có thể thiếu tối ưu trong một số cases

### Option 2: Thêm 1 orientation (3 orientations)
```python
# CARTON: 3 orientations
return [
    {'width': w, 'length': l, 'height': h},   # (W×L, H)
    {'width': l, 'length': w, 'height': h},   # (L×W, H)  
    {'width': w, 'length': h, 'height': l}   # (W×H, L) - swap length↔height
]
```
✓ Tối ưu hơn cho nhiều cases  
✓ Tuân thủ rule: original height không chạm sàn  
✗ Phức tạp hơn, tăng computation

---

## 📋 TÓM TẮT

| Box Type | Rule | Current Orientations | Status | Recommendation |
|----------|------|---------------------|---------|----------------|
| **PRE_PACK** | Mặt (W×H) không chạm sàn | 2-4 orientations (phụ thuộc H > L) | 🔄 CẦN UPDATE | Add constraint Height > Length |
| **CARTON** | Mặt có height không chạm sàn | 2 orientations | ✅ ĐÚNG | Giữ nguyên |

### Kết luận:

1. **PRE_PACK implementation** - 🔄 CẦN UPDATE: Thêm ràng buộc Height > Length cho swap orientations
2. **CARTON implementation** - ✅ ĐÚNG, giữ nguyên 2 orientations
3. **Row Consistency** - 🔄 CẦN CẢI THIỆN: Force tất cả cells dùng cùng dominant length

---

## 🎯 NEXT STEPS

### Implementations cần làm:

#### 1. Update PRE_PACK get_all_orientations() 
- Thêm check `if h > l` trước khi add swap orientations
- Giảm số orientations từ 4 → 2-4 (tùy box dimensions)

#### 2. Improve Row Consistency
- Filter boxes theo dominant_length trước khi pack
- Chỉ cho phép orientations match dominant_length
- Result: All cells trong row có cùng length

#### 3. Enhance determine_dominant_length()
- Chọn length cho phép pack NHIỀU BOXES NHẤT
- Đếm quantity và số box types cho mỗi length
- Maximize: `(count, num_unique_boxes)`

### Expected Impact:

**Before:**
- Row 1: 3 cells (inconsistent lengths: L=19, L=34)
- Utilization: 75.8%

**After:**  
- Row 1: 4 cells (all L=34 consistent)
- Utilization: Higher (>80%)

### Testing Plan:
- ✅ Test PRE_PACK boxes với H ≤ L → chỉ 2 orientations
- ✅ Test PRE_PACK boxes với H > L → 4 orientations  
- ✅ Test row consistency → all cells same length
- ✅ Compare utilization before/after
