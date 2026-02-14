# LIO-SAM KITTI 參數調整指南

## 📋 已應用的優化

已根據 `kitti_2011_09_30_drive_0027_synced` bag 檔案進行以下優化：

### 1. ✅ IMU Topic 優化

**變更:**
```yaml
位置: params_kitti.yaml, 行 6
舊值: imuTopic: "imu_raw"
新值: imuTopic: "/imu_correct"
```

**原因:**
- `/imu_correct` 是由 kitti2bag_ros2 轉換工具自動生成的 LIO-SAM 相容格式
- 已經過預處理，更適合 LIO-SAM 使用
- 頻率：~100 Hz (高頻原始 IMU)

**替代方案:**
- 如果仍有問題，可回改為 `/imu_raw` (原始高頻 IMU)

### 2. ✅ LiDAR Ring Channel 啟用

**變更:**
```yaml
位置: params_kitti.yaml, 行 32-33
舊值: useCloudRing: false
新值: useCloudRing: true
```

**原因:**
- 我們的 KITTI bag 包含 Velodyne HDL-64E 點雲
- kitti2bag_ros2 會自動計算並附加 ring 資訊
- 啟用 ring channel 可以顯著改善特徵提取質量

**確認方式:**
```bash
# 檢查點雲是否有 ring 欄位
ros2 topic type /points_raw
# 應該輸出: sensor_msgs/msg/PointCloud2

# 在 RViz2 中檢查
# 1. 添加 PointCloud2 插件
# 2. Style -> Color Transformer 選擇 'ring'
# 如果能看到色彩漸變表示 ring 資訊正確
```

### 3. ✅ 其他已驗證的設定

```yaml
useCloudTime: false        # ✓ 正確 (KITTI 是同步數據)
sensor: kitti              # ✓ 正確
N_SCAN: 64                 # ✓ 正確 (Velodyne HDL-64E)
Horizon_SCAN: 1800         # ✓ 正確 (Velodyne 水平解析度)
lidar_has_ring: true       # ✓ 正確
```

## 🔧 執行 LIO-SAM

```bash
# 終端 1: 播放 KITTI Bag (循環)
source ~/ros2_ws/install/setup.bash
ros2 bag play kitti_2011_09_30_drive_0027_synced --loop

# 終端 2: 執行 LIO-SAM
source ~/ros2_ws/install/setup.bash
ros2 launch lio_sam run_kitti.launch.py

# 終端 3 (可選): 查看 RViz2
source ~/ros2_ws/install/setup.bash
ros2 run rviz2 rviz2 -d ~/ros2_ws/install/lio_sam/share/lio_sam/config/rviz2.rviz
```

## 🐛 如果遇到問題

### 問題 1: "Cannot find frame X" TF 錯誤

**解決方案:**

檢查 TF 樹是否完整：
```bash
# 列出所有 frame
ros2 run tf2_tools view_frames.py

# 檢查 base_link 是否存在
ros2 topic echo /tf | head
```

如果 TF 不完整，修改 LIO-SAM 參數：
```yaml
# params_kitti.yaml
lidarFrame: "velodyne"      # 改為 Velodyne frame
baselinkFrame: "base_link"  # 確保存在
```

### 問題 2: IMU 資訊不匹配

如果看到 "Cannot find IMU data" 錯誤：

```bash
# 檢查可用的 IMU topics
ros2 topic list | grep imu

# 可能有以下選項
/imu_raw       # 高頻原始 IMU
/imu_correct   # LIO-SAM 格式

# 改為使用 /imu_raw
imuTopic: "/imu_raw"
```

### 問題 3: 點雲不完整或沒有 ring

檢查點雲欄位：
```bash
# 列出點雲的所有欄位
ros2 service call /lidar_node/get_point_cloud_info std_srvs/srv/Empty {}

# 或直接在 RViz2 中檢查 PointCloud2 插件
```

如果沒有 ring 資訊，禁用 ring channel：
```yaml
useCloudRing: false
lidar_has_ring: false
```

## 📊 推薦調整步驟

如果 LIO-SAM 運行緩慢或不穩定，按下列順序調整：

### 1️⃣ 降低特徵提取敏感度

```yaml
# params_kitti.yaml
edgeThreshold: 0.5          # 預設：1.0，降低 = 更多特徵
surfThreshold: 0.05         # 預設：0.1

downsampleRate: 4           # 預設：2，增加 = 更少點
```

### 2️⃣ 調整 voxel 過濾大小

```yaml
odometrySurfLeafSize: 0.6        # 預設：0.4，增加 = 更快
mappingCornerLeafSize: 0.4       # 預設：0.2
mappingSurfLeafSize: 0.6         # 預設：0.4
```

### 3️⃣ 調整 CPU 使用

```yaml
numberOfCores: 2              # 預設：4，減少核心數
mappingProcessInterval: 0.2   # 預設：0.15，增加時間間隔
```

## ✅ 驗證輸出

成功執行應看到：

```
[lio_sam_imuPreintegration] Start.
[lio_sam_imageProjection] Start.
[lio_sam_featureExtraction] Start.
[lio_sam_mapOptimization] Start.
```

在 RViz2 中應看到：
- ✅ 點雲逐漸建立全局地圖
- ✅ Odometry 轨跡連續
- ✅ Loop closure 檢測（如果啟用）

## 🔍 監測 Topics

```bash
# 查看所有 LIO-SAM 輸出 topics
ros2 topic list | grep lio_sam

# 監控 odometry 質量
ros2 topic echo /lio_sam/mapping/odometry

# 監控映射進度
ros2 topic hz /lio_sam/mapping/map_incremental
```

## 📝 參考文件

- 完整參數: [params_kitti.yaml](../config/params_kitti.yaml)
- Bag 檔案詳情: [kitti_2011_09_30_drive_0027 數據](../../README.md)
- LIO-SAM 官方: https://github.com/TixiaoShan/LIO-SAM

---

**最後更新**: 2026-02-11
**KITTI 轉換工具**: kitti2bag_ros2
**測試資料集**: 2011_09_30, Drive 0027
