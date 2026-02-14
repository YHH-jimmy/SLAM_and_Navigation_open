# LIO-SAM 實際使用與除錯紀錄

本文整理實際使用 LIO-SAM 跑 KITTI 資料集的流程與除錯步驟，包含問題現象與解法。

## 1. 實際流程

### 1.1 KITTI 資料轉換

```bash
# 轉換 KITTI Raw (含 sync + extract)
python3 /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
    raw_synced ~/Data -t 2011_09_30 -r 0027
```

轉換完成輸出：
```
kitti_2011_09_30_drive_0027_synced
```

### 1.2 播放 bag

```bash
ros2 bag play kitti_2011_09_30_drive_0027_synced --loop
```

### 1.3 啟動 LIO-SAM

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch lio_sam run_kitti.launch.py
```

### 1.4 查看輸出 topics

```bash
ros2 topic list | grep lio_sam
```

常見輸出：
```
/lio_sam/mapping/odometry
/lio_sam/mapping/odometry_incremental
/lio_sam/mapping/map_global
/lio_sam/mapping/map_local
/lio_sam/mapping/path
/lio_sam/mapping/cloud_registered
```

## 2. 除錯紀錄

### 問題 1: 找不到 run_kitti.launch.py

**現象**
```
file 'run_kitti.launch.py' was not found in the share directory of package 'lio_sam'
```

**原因**
`run_kitti.launch.py` 存在於 src，但未安裝到 install 目錄。

**解法**
```bash
cd ~/ros2_ws
colcon build --packages-select lio_sam --symlink-install
```

---

### 問題 2: LIO-SAM 沒有任何 node 啟動

**現象**
`ros2 node list` 只有 RViz，沒有 `lio_sam_*` node。

**原因**
`params_kitti.yaml` 的 `sensor` 設定錯誤。

**解法**
將 `sensor: kitti` 改為 `sensor: velodyne`。

```yaml
sensor: velodyne
```

---

### 問題 3: IMU 原始高頻資料缺失

**現象**
```
FileNotFoundError: ... drive_0027_extract/oxts/timestamps.txt
```

**原因**
只下載 `*_sync.zip`，缺少 `*_extract.zip`。

**解法**
下載並解壓 `*_extract.zip`：
```
2011_09_30_drive_0027_extract/oxts/timestamps.txt
```

---

### 問題 4: KITTI 資料夾結構不符

**現象**
```
FileNotFoundError: .../2011_09_30/calib_imu_to_velo.txt
```

**原因**
pykitti 期望資料夾結構如下：
```
Data/2011_09_30/
├── calib_*.txt
├── 2011_09_30_drive_0027_sync/
└── 2011_09_30_drive_0027_extract/
```

**解法**
將 `calib_*.txt` 移到日期資料夾下，並把 drive 資料夾放在日期資料夾內。

---

### 問題 5: 虛擬環境干擾 ros2 入口點

**現象**
```
PackageNotFoundError: No package metadata was found for kitti2bag-ros2
```

**原因**
Python venv 覆蓋 ROS2 的路徑。

**解法**
關閉虛擬環境或直接用 `python3` 執行腳本：
```bash
deactivate
source ~/ros2_ws/install/setup.bash
python3 .../kitti2bag
```

---

## 3. 最終可用參數 (摘要)

### params_kitti.yaml 重點

```yaml
pointCloudTopic: "/points_raw"
imuTopic: "/imu_correct"
useCloudRing: true
useCloudTime: false
sensor: velodyne
N_SCAN: 64
Horizon_SCAN: 1800
```

## 4. 產生全域地圖

### 方法 1: SaveMap 服務

```bash
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap

# 指定輸出目錄
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap "{resolution: 0.2, destination: /Downloads/kitti_map}"
```

輸出檔案：
- `GlobalMap.pcd`
- `trajectory.pcd`
- `transformations.pcd`

### 方法 2: RViz2 即時顯示

```
/lio_sam/mapping/map_global
```

## 5. 參考指令

```bash
# 查看 LIO-SAM 輸出
ros2 topic list | grep lio_sam

# 查看頻率
ros2 topic hz /lio_sam/mapping/map_global

# 查看 tf
ros2 topic echo /tf | head
```

## 6. 結論

完成以下條件後，LIO-SAM 可正常產生全域地圖：
- KITTI sync + extract 版本完整
- 正確資料夾結構
- `sensor: velodyne`
- `useCloudRing: true`
- `/points_raw` 與 `/imu_correct` 正確對應

---

最後更新：2026-02-11
