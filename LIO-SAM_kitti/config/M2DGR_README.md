# LIO-SAM M2DGR 數據集配置說明

## 📌 概述

此配置專為 **M2DGR (Multi-modal, Multi-scenario SLAM Dataset)** 數據集優化，支持使用 RoboSense RS-LiDAR-32 激光雷達數據運行 LIO-SAM。

## 🔧 M2DGR 數據集信息

### 傳感器配置
- **LiDAR**: RoboSense RS-LiDAR-32 (32線)
- **IMU**: 6軸或9軸 IMU
- **相機**: Intel RealSense D435i (可選)
- **其他**: UWB, Event Camera

### ROS 話題映射

| 傳感器 | M2DGR 話題 | LIO-SAM 使用 |
|--------|-----------|-------------|
| 點雲 | `/rslidar_points` | ✅ 必需 |
| IMU | `/imu` | ✅ 必需 |
| 里程計 | `/odom` | ⚠️ 可選 |
| TF | `/tf` | ⚠️ 需要檢查 |
| 相機 | `/camera/color/image_raw` | ❌ 不使用 |
| 深度 | `/camera/aligned_depth_to_color/image_raw` | ❌ 不使用 |

## ⚠️ 重要注意事項

### 1. IMU 要求檢查

LIO-SAM **要求 9軸 IMU** (加速度 + 角速度 + 姿態)。M2DGR 部分序列可能只提供 6軸 IMU 數據。

**檢查 IMU 數據**：
```bash
ros2 bag info your_m2dgr.bag
ros2 topic echo /imu --once
```

確認 IMU 消息包含：
- ✅ `linear_acceleration` (x, y, z)
- ✅ `angular_velocity` (x, y, z)
- ✅ `orientation` (x, y, z, w) - **必須有有效值**

如果 `orientation` 全為零或無效，LIO-SAM **無法正常工作**。

### 2. 點雲格式檢查

確認點雲數據包含**環號 (ring)** 信息：

```bash
ros2 topic echo /rslidar_points --once
```

檢查 `fields` 是否包含 `ring` 字段。如果沒有，需要預處理添加。

### 3. 外參標定

**當前配置使用默認外參** (IMU 與 LiDAR 重合)。如果 M2DGR 提供了實際外參，需要修改：

```yaml
# config/params_m2dgr.yaml
extrinsicTrans: [x, y, z]        # IMU 到 LiDAR 的平移
extrinsicRot: [r11, r12, r13,    # IMU 到 LiDAR 的旋轉矩陣
               r21, r22, r23,
               r31, r32, r33]
```

查找 M2DGR 外參文件 (通常為 `calib.yaml` 或 `extrinsic.yaml`)。

## 🚀 使用方法

### 方法 1：使用專用 Launch 文件

```bash
# 編譯（如果還未編譯）
cd ~/ros2_ws
colcon build --packages-select lio_sam --symlink-install
source install/setup.bash

# 播放 M2DGR bag 文件
ros2 bag play your_m2dgr_bag/

# 在另一個終端運行 LIO-SAM
ros2 launch lio_sam run_m2dgr.launch.py
```

### 方法 2：使用標準 Launch 文件 + 指定配置

```bash
ros2 launch lio_sam run.launch.py \
    config_file:=/home/jimmyrtioms/ros2_ws/src/LIO-SAM/config/params_m2dgr.yaml
```

## 📊 參數調優

### 場景適配

M2DGR 包含多種場景，可能需要針對性調整：

#### 室內場景 (Indoor)
```yaml
odometrySurfLeafSize: 0.2        # 更精細
mappingCornerLeafSize: 0.1
mappingSurfLeafSize: 0.2
surroundingKeyframeSearchRadius: 30.0  # 更小範圍
```

#### 室外場景 (Outdoor)
```yaml
odometrySurfLeafSize: 0.4        # 當前默認值
mappingCornerLeafSize: 0.2
mappingSurfLeafSize: 0.4
surroundingKeyframeSearchRadius: 50.0
```

#### 手持場景 (Handheld)
```yaml
z_tollerance: 1000.0             # 允許6自由度運動
rotation_tollerance: 1000.0
surroundingkeyframeAddingDistThreshold: 0.5  # 更頻繁的關鍵幀
```

### IMU 噪聲參數

當前使用默認值，建議根據 M2DGR 提供的 IMU 規格書調整：

```yaml
imuAccNoise: <從規格書獲取>
imuGyrNoise: <從規格書獲取>
imuAccBiasN: <從規格書獲取>
imuGyrBiasN: <從規格書獲取>
```

## 🐛 常見問題排查

### 問題 1：點雲無法處理
**現象**：LIO-SAM 啟動但不輸出地圖
**原因**：點雲缺少 ring 信息
**解決**：使用 M2DGR 官方提供的預處理腳本添加 ring

### 問題 2：IMU 初始化失敗
**現象**：`[ERROR] IMU orientation not available`
**原因**：6軸 IMU 無 orientation 數據
**解決**：檢查數據集是否包含 9軸 IMU，或使用其他 SLAM 算法（如 FAST-LIO2）

### 問題 3：軌跡漂移嚴重
**現象**：建圖質量差，軌跡不準確
**可能原因**：
1. 外參標定不準確
2. IMU 噪聲參數不匹配
3. 點雲時間戳不同步

**調試步驟**：
```bash
# 1. 檢查 TF 樹
ros2 run tf2_tools view_frames

# 2. 查看點雲頻率
ros2 topic hz /rslidar_points

# 3. 查看 IMU 頻率
ros2 topic hz /imu

# 4. 檢查時間戳同步
ros2 topic echo /rslidar_points/header/stamp
ros2 topic echo /imu/header/stamp
```

### 問題 4：閉環檢測失效
**調整參數**：
```yaml
loopClosureEnableFlag: true
historyKeyframeSearchRadius: 10.0    # 減小搜索半徑
historyKeyframeFitnessScore: 0.5     # 放寬閾值
```

## 📁 M2DGR 數據集下載

官方網站：https://github.com/SJTU-ViSYS/M2DGR

推薦序列（帶9軸IMU）：
- `gate_01` - 戶外場景
- `street_01` - 街道場景
- `building_01` - 建築物內部

## 🔗 相關資源

- [LIO-SAM 原始論文](https://github.com/TixiaoShan/LIO-SAM)
- [M2DGR 數據集論文](https://arxiv.org/abs/2112.13659)
- [RoboSense RS-LiDAR 文檔](http://www.robosense.ai/)

## 📝 配置文件位置

- **配置文件**: `config/params_m2dgr.yaml`
- **Launch 文件**: `launch/run_m2dgr.launch.py`
- **本說明**: `config/M2DGR_README.md`

## ✅ 快速檢查清單

在運行之前，確認：
- [ ] M2DGR bag 文件包含 `/rslidar_points` 話題
- [ ] M2DGR bag 文件包含 `/imu` 話題且為 9軸
- [ ] 點雲數據包含 ring 字段
- [ ] 已修改外參為實際標定值
- [ ] 已根據場景調整參數
- [ ] 編譯並 source 了工作空間

---

**最後更新**: 2026-02-10
**維護者**: jimmyrtioms
