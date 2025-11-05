# Test Report: Width Utilization Improvements

## Date: 2025-01-XX

## Summary

Đã implement 3 improvements cho Z-First algorithm:
1. **Progressive Dominant Length Relaxation**: Tăng tolerance khi width utilization < 80%
2. **Width-First Gap Filling**: Fill gaps còn lại sau main packing loop
3. **Post-Processing Width Optimization**: Move boxes từ later rows vào gaps

## Test Results

### Overall Statistics
- **Containers used**: 1
- **Boxes packed**: 471
- **Container utilization**: 62.5%
- **Average width utilization**: 76.8%
- **Average height utilization**: 98.2%

### Row-by-Row Analysis

| Row | Cells | Width | Width% | Height | Status | Change | Target |
|-----|-------|-------|--------|--------|--------|--------|--------|
| 1   | 5     | 91.0" | 98.4%  | 106.0" | ✅ OK  | -0.0%  | -      |
| 2   | 2     | 51.0" | 55.1%  | 99.0"  | ⚠️ LOW | +0.0%  | >80%   |
| 3   | 4     | 85.0" | 91.9%  | 103.0" | ✅ OK  | -0.0%  | -      |
| 4   | 4     | 82.0" | 88.6%  | 103.8" | ✅ GOOD | +18.3% | >85% ✅ |
| 5   | 2     | 60.0" | 64.9%  | 105.0" | ⚠️ LOW | -32.4% | -      |
| 6   | 1     | 30.0" | 32.4%  | 105.0" | ⚠️ LOW | +0.0%  | >70%   |
| 7   | 3     | 90.0" | 97.3%  | 105.0" | ✅ OK  | -0.0%  | -      |
| 8   | 3     | 90.0" | 97.3%  | 105.0" | ✅ OK  | N/A    | -      |
| 9   | 2     | 60.0" | 64.9%  | 105.0" | ⚠️ LOW | N/A    | -      |

### Target Rows Analysis

#### Row 2
- **Current**: 51.0" (55.1%)
- **Previous**: 51.0" (55.1%)
- **Change**: +0.0%
- **Status**: ❌ UNCHANGED - Chưa đạt target (>80%)
- **Analysis**: 
  - Progressive relaxation đã trigger (tolerance tăng lên 3.0")
  - Nhưng gap filling không hoạt động (có thể không có remaining boxes hoặc gap < 10.0")
  - Post-processing đã thử optimize Row Y=96.0" (Row 3) nhưng không optimize Row 2

#### Row 4
- **Current**: 82.0" (88.6%)
- **Previous**: 65.0" (70.3%)
- **Change**: +18.3% ✅
- **Status**: ✅ IMPROVED - Đạt target (>85%)
- **Analysis**:
  - Post-processing đã move box J2 (width=17.0") từ Row Y=138.0 vào gap tại Row Y=96.0
  - Width utilization improved from 70.3% → 88.6%
  - Đây là Row 3 trong output, nhưng tương ứng với Row 4 trong analysis

#### Row 6
- **Current**: 30.0" (32.4%)
- **Previous**: 30.0" (32.4%)
- **Change**: +0.0%
- **Status**: ❌ UNCHANGED - Chưa đạt target (>70%)
- **Analysis**:
  - Progressive relaxation đã trigger (tolerance tăng lên 3.0")
  - Secondary length được detect (24.0")
  - Nhưng gap filling và post-processing không cải thiện được

### Improvement Details

#### Progressive Relaxation
- ✅ Hoạt động: Đã detect và tăng tolerance khi width utilization < 80%
- ✅ Log messages: Hiển thị rõ ràng các thay đổi tolerance
- ⚠️ Vấn đề: Tolerance tăng nhưng không cải thiện được Row 2 và Row 6

#### Gap Filling
- ❓ Chưa thấy log messages về gap filling
- ⚠️ Có thể: Gap filling không trigger vì remaining_width < 10.0" hoặc không có remaining boxes

#### Post-Processing Width Optimization
- ✅ Hoạt động: Đã move boxes từ later rows vào gaps
- ✅ Kết quả: Row 4 (Row 3 trong output) improved từ 70.3% → 88.6%
- ⚠️ Vấn đề: Chỉ optimize được 1 row, Row 2 và Row 6 không được optimize

### Issues Identified

1. **Row 2 không được cải thiện**:
   - Progressive relaxation đã trigger nhưng không đủ
   - Gap filling không hoạt động (có thể gap < 10.0" threshold)
   - Post-processing không optimize Row 2 (có thể không có boxes phù hợp từ later rows)

2. **Row 6 không được cải thiện**:
   - Tương tự Row 2
   - Chỉ có 1 cell với width 30.0"
   - Có thể không có boxes nhỏ hơn để fill gap

3. **Row 5 có regression**:
   - Giảm từ 97.3% → 64.9% (-32.4%)
   - Có thể do post-processing đã move boxes đi

### Recommendations

1. **Giảm threshold cho gap filling**: Từ 10.0" xuống 5.0" để fill nhiều gaps hơn
2. **Cải thiện post-processing**: Ưu tiên optimize Row 2, 4, 6 trước
3. **Kiểm tra logic gap filling**: Đảm bảo nó hoạt động với remaining boxes
4. **Fix regression ở Row 5**: Kiểm tra tại sao boxes bị move đi

### Next Steps

1. Test với threshold thấp hơn cho gap filling
2. Thêm logging chi tiết cho gap filling để debug
3. Ưu tiên optimize target rows trong post-processing
4. Kiểm tra và fix regression ở Row 5

