# KITTI to ROS2 Bag Converter

完整功能的 KITTI 資料集轉 ROS2 bag 格式轉換工具，支援 IMU、GPS、LiDAR 和相機資料。

## 功能特色

- ✅ **ROS2 原生支援** - 使用 `rosbag2_py` 和 `rclpy`
- ✅ **完整感測器支援**:
  - IMU (高頻率原始數據)
  - GPS (位置 + 速度)
  - Velodyne LiDAR (含 ring channel)
  - 相機 (灰階 + 彩色, 左 + 右)
  - TF 轉換 (static + dynamic)
- ✅ **支援多種資料集**:
  - KITTI Raw Synced
  - KITTI Odometry (灰階/彩色)
- ✅ **LIO-SAM 相容** - 輸出 `/imu_correct` topic

## 安裝

### 1. 依賴項

```bash
# 安裝 pykitti
pip install pykitti

# ROS2 依賴 (應該已安裝)
sudo apt-get install ros-humble-cv-bridge ros-humble-rosbag2-py
```

### 2. 編譯套件

```bash
cd ~/ros2_ws
colcon build --packages-select kitti2bag_ros2 --symlink-install
source install/setup.bash
```

## 使用方法

### RAW Dataset 轉換

#### 直接執行

```bash
# 基本用法
python3 /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
    raw_synced /path/to/kitti/raw -t 2011_09_26 -r 0001

# 指定輸出目錄
python3 /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
    raw_synced /path/to/kitti/raw -t 2011_09_26 -r 0001 -o my_output_bag

# ✅ 實際成功案例 (2011_09_30_drive_0027)
python3 /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
    raw_synced ~/Data -t 2011_09_30 -r 0027
```

#### 實際轉換結果範例

**輸入:** 2011-09-30, Drive 0027  
**輸出 Bag 檔案:** `kitti_2011_09_30_drive_0027_synced`

```
✅ Conversion completed successfully!
📦 Bag file: kitti_2011_09_30_drive_0027_synced

轉換統計:
  ├─ 檔案大小: 6.0 GB
  ├─ 持續時間: 115.5 秒 (~2 分鐘)
  ├─ 消息總數: 37,490
  └─ Topics: 15 個

感測器資料:
  ├─ IMU 原始數據: 11,556 幀 (高頻 ~100Hz)
  ├─ GPS 位置: 1,106 幀
  ├─ GPS 速度: 1,106 幀
  ├─ 點雲資料: 1,106 幀 (Velodyne HDL-64E)
  ├─ 相機影像: 4,424 幀 (4個相機 × 1,106)
  ├─ 靜態 TF: 1,106 幀
  └─ 動態 TF: 1,106 幀
```

**輸出 Topics (RAW) - 完整清單 (15 個):**

| Topic | 類型 | 消息數 | 說明 |
|-------|------|--------|------|
| `/imu_raw` | sensor_msgs/Imu | 11,556 | 高頻原始 IMU (~100Hz) |
| `/imu_correct` | sensor_msgs/Imu | 11,556 | LIO-SAM 格式 IMU |
| `/gps/fix` | sensor_msgs/NavSatFix | 1,106 | GPS 位置 (經緯度/海拔) |
| `/gps/vel` | geometry_msgs/TwistStamped | 1,106 | GPS 速度 |
| `/points_raw` | sensor_msgs/PointCloud2 | 1,106 | Velodyne 點雲 (含 ring) |
| `/tf` | tf2_msgs/TFMessage | 1,106 | 動態座標轉換 |
| `/tf_static` | tf2_msgs/TFMessage | 1,106 | 靜態座標轉換 |
| `/kitti/camera_gray_left/image_raw` | sensor_msgs/Image | 1,106 | 左灰階影像 |
| `/kitti/camera_gray_left/camera_info` | sensor_msgs/CameraInfo | 1,106 | 左灰階相機資訊 |
| `/kitti/camera_gray_right/image_raw` | sensor_msgs/Image | 1,106 | 右灰階影像 |
| `/kitti/camera_gray_right/camera_info` | sensor_msgs/CameraInfo | 1,106 | 右灰階相機資訊 |
| `/kitti/camera_color_left/image_raw` | sensor_msgs/Image | 1,106 | 左彩色影像 |
| `/kitti/camera_color_left/camera_info` | sensor_msgs/CameraInfo | 1,106 | 左彩色相機資訊 |
| `/kitti/camera_color_right/image_raw` | sensor_msgs/Image | 1,106 | 右彩色影像 |
| `/kitti/camera_color_right/camera_info` | sensor_msgs/CameraInfo | 1,106 | 右彩色相機資訊 |

**總訊息數:** 37,490

### Odometry Dataset 轉換

```bash
# 灰階影像
kitti2bag odom_gray /path/to/kitti/odometry -s 00

# 彩色影像
kitti2bag odom_color /path/to/kitti/odometry -s 00

# 指定輸出
kitti2bag odom_gray /path/to/kitti/odometry -s 00 -o my_odom_bag
```

**輸出 Topics (Odometry):**
- `/tf` - 動態座標轉換
- `/kitti/camera_gray_left/image_rect` - 已校正影像
- `/kitti/camera_gray_left/camera_info`
- (灰階或彩色,根據選擇的類型)

## KITTI 資料集結構

### Raw Dataset
```
kitti_raw/
├── 2011_09_26/
│   ├── 2011_09_26_drive_0001_sync/
│   │   ├── image_00/     # 左灰階相機
│   │   ├── image_01/     # 右灰階相機
│   │   ├── image_02/     # 左彩色相機
│   │   ├── image_03/     # 右彩色相機
│   │   ├── velodyne_points/
│   │   └── oxts/         # IMU/GPS
│   └── calib_*.txt
```

### Odometry Dataset  
```
kitti_odometry/
├── sequences/
│   ├── 00/
│   │   ├── image_0/      # 左相機
│   │   ├── image_1/      # 右相機
│   │   ├── calib.txt
│   │   └── times.txt
│   └── ...
└── poses/
    └── 00.txt            # Ground truth (序列 00-10)
```

## 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `kitti_type` | 資料集類型 | `raw_synced`, `odom_gray`, `odom_color` |
| `dir` | 資料集根目錄 | `/home/user/kitti/raw` |
| `-t, --date` | RAW 資料集日期 | `2011_09_26` |
| `-r, --drive` | RAW 資料集驅動編號 | `0001`, `0002`, ... |
| `-s, --sequence` | Odometry 序列號 | `00` ~ `21` |
| `-o, --output` | 輸出 bag 目錄名稱 | `my_custom_bag` |

## 下載 KITTI 資料集

### Raw Dataset
- [官方下載頁面](https://www.cvlibs.net/datasets/kitti/raw_data.php)
- 需要下載:
  - `*_sync.zip` (同步數據)
  - `*_extract.zip` (高頻 IMU,可選)
  - `*_calib.zip` (校準文件)

### Odometry Dataset
- [官方下載頁面](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)
- 需要下載:
  - `data_odometry_gray.zip` 或 `data_odometry_color.zip`
  - `data_odometry_poses.zip` (Ground truth,序列 00-10)
  - `data_odometry_calib.zip`

## 與 LIO-SAM 配合使用 ⭐

此工具輸出的 bag 檔可直接用於 LIO-SAM:

### ✅ 已驗證成功案例 (2011_09_30_drive_0027)

```bash
# 終端 1: 播放 KITTI Bag 檔案
cd ~/ros2_ws
ros2 bag play kitti_2011_09_30_drive_0027_synced --loop

# 終端 2: 執行 LIO-SAM
source ~/ros2_ws/install/setup.bash
ros2 launch lio_sam run_kitti.launch.py
```

### 查看記錄資訊

```bash
# 查看 bag 摘要
ros2 bag info kitti_2011_09_30_drive_0027_synced

# 輸出範例:
# Files:             kitti_2011_09_30_drive_0027_synced_0.db3
# Bag size:          6.0 GiB
# Duration:          115.547650304s
# Messages:          37490
# Topics:            15
```

### LIO-SAM 參數配置

確保 LIO-SAM 的 `params_kitti.yaml` 中設置正確的 topic 名稱:

```yaml
imuTopic: "/imu_correct"          # ✅ 使用 /imu_correct (高頻)
likaTopic: "/points_raw"          # ✅ Velodyne 點雲
odomTopic: "/odometry/imu"
mapTopic: "/lio_sam/mapping/map_lo"
```

## 疑難排解

### 錯誤: "Could not load module 'pykitti'"
```bash
pip install pykitti
```

### 錯誤: "Path does not exist"
檢查資料集路徑是否正確,確保目錄結構符合 KITTI 格式。

### 點雲沒有 ring 資訊
本工具會自動計算 Velodyne HDL-64E 的 ring channel (64 線),確保與 LIO-SAM 相容。

### 時間戳問題
- RAW dataset: 使用原始時間戳
- Odometry dataset: 使用相對時間 + 當前 epoch

## 與原版差異

| 特性 | kitti2bag.py (ROS1) | kitti2bag_ros2 |
|------|---------------------|----------------|
| ROS 版本 | ROS1 | ✅ ROS2 |
| rosbag 版本 | rosbag (v1) | ✅ rosbag2 |
| 時間處理 | rospy.Time | ✅ rclpy.time.Time |
| TF | tf (v1) | ✅ tf2_msgs |
| 序列化 | 自動 | ✅ serialize_message |
| 進度顯示 | ✅ tqdm | ✅ tqdm |

## 授權

MIT License

## 貢獻者

基於原始 [kitti2bag](https://github.com/tomas789/kitti2bag) 專案改寫為 ROS2 版本。

## 參考資料

- [KITTI Dataset](https://www.cvlibs.net/datasets/kitti/)
- [pykitti](https://github.com/utiasSTARS/pykitti)
- [LIO-SAM](https://github.com/TixiaoShan/LIO-SAM)
