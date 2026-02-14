# LIO-SAM KITTI 參數調整指南

## 📋 已應用的優化

已根據 `kitti_2011_09_30_drive_0027_synced` bag 檔案進行以下優化：

### 1. ✅ IMU Topic 優化

**變更:**
```yaml
位置: config/params.yaml, 行 6
舊值: imuTopic: "imu_raw"
新值: imuTopic: "imu_raw"
```

**原因:**
- `imu_raw` 為 KITTI 原始 IMU 資料
- 以 kitti2bag_ros2 產出的 bag 內容為準

### 2. ✅ LiDAR Ring/Time 欄位處理

**說明:**
- 若 KITTI 點雲沒有 `ring` 或 `time` 欄位，本專案會自動估算
- `ring` 由垂直角度計算，`time` 以掃描角度估算（10Hz）

### 3. ✅ 其他已驗證的設定

```yaml
sensor: velodyne           # ✓ 正確
N_SCAN: 64                 # ✓ 正確 (Velodyne HDL-64E)
Horizon_SCAN: 2083         # ✓ 依 KITTI 轉換設定
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
# config/params.yaml
lidarFrame: "lidar_link"     # 改為 Velodyne frame
baselinkFrame: "base_link"  # 確保存在
```

### 問題 2: IMU 資訊不匹配

如果看到 "Cannot find IMU data" 錯誤：

```bash
# 檢查可用的 IMU topics
ros2 topic list | grep imu

# 可能有以下選項
/imu_raw       # 高頻原始 IMU

# 改為使用 imu_raw
imuTopic: "imu_raw"
```

### 問題 3: 點雲不完整或沒有 ring/time

檢查點雲欄位：
```bash
# 列出點雲的所有欄位
ros2 service call /lidar_node/get_point_cloud_info std_srvs/srv/Empty {}

# 或直接在 RViz2 中檢查 PointCloud2 插件
```

若點雲沒有 `ring` 或 `time` 欄位，會使用內建估算流程，請確認 `sensor` 設為 `velodyne`。

## 📊 推薦調整步驟

如果 LIO-SAM 運行緩慢或不穩定，按下列順序調整：

### 1️⃣ 降低特徵提取敏感度

```yaml
# config/params.yaml
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

- 完整參數: [config/params.yaml](config/params.yaml)
- Bag 檔案詳情: [kitti_2011_09_30_drive_0027 數據](../../README.md)
- LIO-SAM 官方: https://github.com/TixiaoShan/LIO-SAM

---

**最後更新**: 2026-02-11
**KITTI 轉換工具**: kitti2bag_ros2
**測試資料集**: 2011_09_30, Drive 0027
