# LIO-SAM 使用手冊（中文版）

## 目錄

1. [系統簡介](#系統簡介)
2. [系統要求](#系統要求)
3. [安裝步驟](#安裝步驟)
4. [硬件準備](#硬件準備)
5. [配置指南](#配置指南)
6. [運行系統](#運行系統)
7. [常見問題排查](#常見問題排查)
8. [進階功能](#進階功能)
9. [參數調整指南](#參數調整指南)

---

## 系統簡介

### 什麼是 LIO-SAM？

LIO-SAM 是一個**激光雷達-慣性測量組合定位與製圖系統**（Lidar-Inertial Odometry and Mapping）。該系統將激光雷達(Lidar)和慣性測量單元(IMU)的數據進行緊耦合融合，實現實時、準確的機器人定位與環境地圖構建。

### 核心特點

- **實時性**：運行速度可達實時速度的 10 倍
- **精度高**：利用因子圖優化方法進行精確的姿態估計
- **魯棒性**：支持閉環檢測和 GPS 融合
- **靈活性**：支持多種激光雷達和 IMU 型號

### 系統架構

LIO-SAM 維護兩個因子圖：

1. **地圖優化圖** (`mapOptimization.cpp`)
   - 優化激光雷達里程計因子和 GPS 因子
   - 全程維護，提供全局地圖
   - 運行速度較慢但精度高

2. **IMU 預積分圖** (`imuPreintegration.cpp`)
   - 優化 IMU 和激光雷達里程計因子
   - 估計 IMU 偏差
   - 定期重置，保證 IMU 頻率下的實時里程計

---

## 系統要求

### 操作系統
- **Ubuntu 20.04** + ROS2 Foxy/Galactic
- **Ubuntu 22.04** + ROS2 Humble

### 必要的軟件包

```bash
# ROS2 基礎包
sudo apt install ros-<ros2-version>-perception-pcl \
                 ros-<ros2-version>-pcl-msgs \
                 ros-<ros2-version>-vision-opencv \
                 ros-<ros2-version>-xacro

# GTSAM 庫（優化庫）
sudo add-apt-repository ppa:borglab/gtsam-release-4.1
sudo apt install libgtsam-dev libgtsam-unstable-dev
```

### 硬件建議

- **CPU**：4 核或以上
- **RAM**：8GB 或以上
- **SSD**：用於實時數據處理

---

## 安裝步驟

### 1. 克隆代碼庫

```bash
cd ~/ros2_ws/src
git clone https://github.com/TixiaoShan/LIO-SAM.git
cd LIO-SAM
git checkout ros2
cd ~/ros2_ws
```

### 2. 編譯項目

```bash
colcon build --symlink-install
```

編譯完成後，應該看到以下可執行文件：
- `lio_sam_imuPreintegration`
- `lio_sam_imageProjection`
- `lio_sam_featureExtraction`
- `lio_sam_mapOptimization`

### 3. 驗證安裝

```bash
source install/setup.bash
ros2 launch lio_sam run.launch.py
```

---

## 硬件準備

### 激光雷達要求

#### 1. 點雲時間戳

LIO-SAM 使用 IMU 數據進行點雲去畸變，因此需要：
- **每個點都有相對時間戳**
- 時間戳應在掃描開始時為 0，在掃描結束時達到掃描周期（如 10Hz 掃描應為 0-0.1 秒）

#### 2. 環號信息

- 每個點需要標記其所屬的激光通道（環號）
- 機械式激光雷達可直接使用通道號
- 內部 IMU 的激光雷達（如 Ouster 內置 IMU）不支持

### IMU 要求

#### 1. IMU 軸數
- **必須為 9 軸 IMU**（包含加速度、角速度和姿態）
- 6 軸 IMU 不支持（如 Ouster 內置 IMU）

#### 2. IMU 數據率
- **最低要求**：200Hz
- **建議**：500Hz 或以上（我們使用 Microstrain 3DM-GX5-25）

#### 3. IMU 安裝方式
- IMU 應與激光雷達固定安裝
- IMU 的 X 軸應與激光雷達的前進方向一致
- 按照 ROS REP-105 坐標系規則

### 支持的硬件組合

| 激光雷達 | IMU 型號 | 驅動包 | 狀態 |
|---------|--------|------|------|
| Ouster | Xsens/SBG | ros2_ouster_drivers | ✓ 測試通過 |
| Velodyne | Microstrain | - | ✗ 未在 ROS2 版本測試 |
| Livox | - | - | ✗ 未在 ROS2 版本測試 |

---

## 配置指南

### 配置文件位置

`config/params.yaml` - 所有參數配置

### 關鍵配置參數

#### 1. 主題配置

```yaml
# 數據輸入主題
pointCloudTopic: "/points"          # 點雲數據
imuTopic: "/imu/data"              # IMU 數據
odomTopic: "odometry/imu"          # IMU 里程計
gpsTopic: "odometry/gpsz"          # GPS 數據（可選）

# 坐標系框架
lidarFrame: "lidar_link"           # 激光雷達坐標系
baselinkFrame: "base_link"         # 機器人基礎坐標系
odometryFrame: "odom"              # 里程計坐標系
mapFrame: "map"                    # 地圖坐標系
```

#### 2. 傳感器配置

```yaml
# 激光雷達類型和參數
sensor: ouster                     # 選項：velodyne, ouster, livox
N_SCAN: 64                         # 激光通道數
Horizon_SCAN: 512                  # 水平分辨率
downsampleRate: 1                  # 下採樣率（1=不下採樣）
lidarMinRange: 1.0                 # 最小有效距離(m)
lidarMaxRange: 1000.0              # 最大有效距離(m)
```

#### 3. IMU 參數配置

```yaml
# IMU 噪聲參數（需根據 IMU 類型調整）
imuAccNoise: 3.9939570888238808e-03        # 加速度計噪聲
imuGyrNoise: 1.5636343949698187e-03        # 陀螺儀噪聲
imuAccBiasN: 6.4356659353532566e-05        # 加速度計偏差噪聲
imuGyrBiasN: 3.5640318696367613e-05        # 陀螺儀偏差噪聲

imuGravity: 9.80511                        # 重力加速度
imuRPYWeight: 0.01                         # RPY 初始化權重

# IMU 與激光雷達的外參（關鍵參數）
extrinsicTrans: [0.0, 0.0, 0.0]           # 平移向量
extrinsicRot: [-1.0, 0.0, 0.0,             # 旋轉矩陣（陀螺儀和加速度計）
               0.0, 1.0, 0.0,
               0.0, 0.0, -1.0]
extrinsicRPY: [0.0, 1.0, 0.0,              # 旋轉矩陣（IMU 姿態）
              -1.0, 0.0, 0.0,
               0.0, 0.0, 1.0]
```

#### 4. 特徵提取參數

```yaml
# LOAM 特徵檢測閾值
edgeThreshold: 1.0                 # 邊緣特徵檢測閾值
surfThreshold: 0.1                 # 平面特徵檢測閾值
edgeFeatureMinValidNum: 10         # 最少邊緣特徵數
surfFeatureMinValidNum: 100        # 最少平面特徵數
```

#### 5. 體素濾波參數

```yaml
odometrySurfLeafSize: 0.4          # 里程計表面濾波（室外：0.4，室內：0.2）
mappingCornerLeafSize: 0.2         # 地圖製作角特徵濾波
mappingSurfLeafSize: 0.4           # 地圖製作表面特徵濾波
```

#### 6. 關鍵幀和地圖參數

```yaml
surroundingkeyframeAddingDistThreshold: 1.0    # 添加關鍵幀距離閾值
surroundingkeyframeAddingAngleThreshold: 0.2   # 添加關鍵幀角度閾值
surroundingKeyframeDensity: 2.0                # 關鍵幀下採樣密度
surroundingKeyframeSearchRadius: 50.0          # 掃描匹配搜索半徑
```

---

## 運行系統

### 基本運行步驟

#### 1. 啟動 ROS 環境

```bash
source ~/ros2_ws/install/setup.bash
```

#### 2. 啟動 LIO-SAM

```bash
ros2 launch lio_sam run.launch.py
```

此命令會啟動以下節點：
- `static_transform_publisher`：發佈靜態坐標變換
- `robot_state_publisher`：發佈機器人模型
- `lio_sam_imuPreintegration`：IMU 預積分
- `lio_sam_imageProjection`：點雲投影和去畸變
- `lio_sam_featureExtraction`：特徵提取
- `lio_sam_mapOptimization`：地圖優化

#### 3. 播放 ROS Bag 數據

在另一個終端：

```bash
ros2 bag play your-bag.bag
```

或者循環播放：

```bash
ros2 bag play your-bag.bag --loop
```

加速播放（對於閉環檢測）：

```bash
ros2 bag play your-bag.bag -r 1.0
```

#### 4. 可視化結果

使用 RViz 可視化：

```bash
ros2 run rviz2 rviz2 -d $(ros2 pkg prefix lio_sam)/share/lio_sam/config/rviz2.rviz
```

---

## 常見問題排查

### 1. 之字形或抖動行為（Zigzag Behavior）

**症狀**：軌跡呈現之字形或明顯的抖動

**原因**：激光雷達和 IMU 數據時間戳不同步

**解決方法**：
- 檢查激光雷達驅動的時間戳設置
- 確認激光雷達和 IMU 的時鐘同步
- 在驅動中配置正確的時間戳模式（如 Ouster 使用 `TIME_FROM_PTP_1588`）

### 2. 上下跳動（Jumping Up and Down）

**症狀**：啟動後 base_link 立即開始上下跳動

**原因**：IMU 外參配置錯誤，通常是重力加速度符號反了

**解決方法**：
- 檢查 `extrinsicRot` 和 `extrinsicRPY` 是否正確
- 嘗試反轉 Z 軸：改變第 9 個元素的符號
- 調整 IMU 坐標系轉換

### 3. mapOptimization 崩潰

**症狀**：程序突然崩潰，錯誤信息與 GTSAM 相關

**解決方法**：
- 確保安裝了正確版本的 GTSAM
  ```bash
  sudo apt install libgtsam-dev libgtsam-unstable-dev
  ```
- 重新編譯項目
  ```bash
  colcon clean all
  colcon build
  ```

### 4. GPS 里程計不可用

**症狀**：GPS 數據發布但系統未使用

**原因**：坐標系之間的變換丟失或不正確

**解決方法**：
- 檢查所有坐標系框架是否正確發佈
- 驗證 `imu_frame_id`、`gps_frame_id` 到 `base_link` 的變換
- 參考 Robot Localization 文檔

---

## 進階功能

### 1. 閉環檢測

#### 啟用閉環檢測

在 `params.yaml` 中配置：

```yaml
loopClosureEnableFlag: true        # 啟用閉環檢測
loopClosureFrequency: 1.0          # 閉環檢測頻率（Hz）
surroundingKeyframeSize: 50        # 子圖大小
historyKeyframeSearchRadius: 15.0  # 閉環搜索半徑（米）
historyKeyframeSearchTimeDiff: 30.0 # 時間差闾值（秒）
historyKeyframeSearchNum: 25       # 融合的歷史幀數
historyKeyframeFitnessScore: 0.3   # ICP 匹配閾值
```

#### 在 RViz 中查看

- 取消勾選 "Map (cloud)"
- 勾選 "Map (global)" 查看全局地圖
- 閉環檢測會在地圖中修正軌跡

### 2. GPS 融合

#### 啟用 GPS 功能

```yaml
useImuHeadingInitialization: true  # 使用 IMU 航向初始化
useGpsElevation: true              # 使用 GPS 高度
gpsCovThreshold: 2.0               # GPS 協方差閾值
poseCovThreshold: 25.0             # 位置協方差閾值

gpsTopic: "odometry/gpsz"          # GPS 數據主題
```

#### 在 RViz 中查看

- 勾選 "Odom GPS" 查看 GPS 里程計

### 3. 保存地圖

#### 服務調用

```bash
# 默認設置保存地圖
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap

# 自定義分辨率和位置
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap "{resolution: 0.2, destination: /home/user/maps/my_map}"
```

地圖將被保存為 `.pcd` 格式的點雲文件。

---

## 進階功能（續）

### 4. 數據導出設置

```yaml
savePCD: true                      # 是否保存點雲
savePCDDirectory: "/Downloads/LOAM/"  # 保存目錄
```

**警告**：系統會刪除並重建 LOAM 文件夾，請備份重要數據。

### 5. CPU 性能參數

```yaml
numberOfCores: 4                   # 用於地圖優化的核心數
mappingProcessInterval: 0.15       # 地圖處理間隔（秒）
```

調整這些參數可以平衡計算負載和更新頻率。

---

## 參數調整指南

### 針對不同傳感器的配置

#### Ouster 激光雷達

```yaml
sensor: ouster
N_SCAN: 128 或 64（根據型號）
Horizon_SCAN: 1024 或 512

# Ouster 驅動配置（launch 文件中）
timestamp_mode: "TIME_FROM_PTP_1588"
```

#### Velodyne 激光雷達

```yaml
sensor: velodyne
N_SCAN: 16, 32 或 64
Horizon_SCAN: 1800
```

#### KITTI 數據集

```yaml
pointCloudTopic: "points_raw"
imuTopic: "imu_raw"
sensor: velodyne
N_SCAN: 64
Horizon_SCAN: 2083
downsampleRate: 1
loopClosureEnableFlag: true

# 外參（KITTI 特定）
extrinsicTrans: [-8.086759e-01, 3.195559e-01, -7.997231e-01]
extrinsicRot: [9.999976e-01, 7.553071e-04, -2.035826e-03,
               -7.854027e-04, 9.998898e-01, -1.482298e-02,
               2.024406e-03, 1.482454e-02, 9.998881e-01]
extrinsicRPY: [9.999976e-01, 7.553071e-04, -2.035826e-03,
               -7.854027e-04, 9.998898e-01, -1.482298e-02,
               2.024406e-03, 1.482454e-02, 9.998881e-01]
```

**說明**：若 KITTI 點雲沒有 `ring` 或 `time` 欄位，本專案會自動以垂直角度估算 `ring`，並以掃描角度估算每點 `time`（10Hz 掃描）。

**快速流程**：
1. 以 kitti2bag_ros2 轉換資料並播放 bag。
2. 使用本專案的 `config/params.yaml` 直接啟動 LIO-SAM。

### 環境自適應調整

#### 室外環境（Outdoor）

```yaml
odometrySurfLeafSize: 0.4          # 較大濾波以提高速度
mappingCornerLeafSize: 0.2
mappingSurfLeafSize: 0.4
surroundingKeyframeSearchRadius: 50.0
```

#### 室內環境（Indoor）

```yaml
odometrySurfLeafSize: 0.2          # 較小濾波以增加精度
mappingCornerLeafSize: 0.1
mappingSurfLeafSize: 0.2
surroundingKeyframeSearchRadius: 20.0
```

#### 低紋理環境

```yaml
edgeThreshold: 0.5                 # 降低特徵提取閾值
surfThreshold: 0.05
edgeFeatureMinValidNum: 5
surfFeatureMinValidNum: 50
```

### IMU 調整指南

#### 高噪聲 IMU

```yaml
# 增大噪聲參數，降低 IMU 信任度
imuRPYWeight: 0.001                # 降低權重
poseCovThreshold: 100.0            # 提高閾值
```

#### 低漂移 IMU

```yaml
# 減小噪聲參數，提高 IMU 信任度
imuRPYWeight: 0.1
imuAccBiasN: 1e-5
imuGyrBiasN: 1e-5
```

---

## 使用 Docker 運行

### 構建 Docker 鏡像

```bash
docker build -t liosam-humble-jammy .
```

### 使用 docker run

```bash
docker run --init -it -d \
  --name liosam-container \
  -v /etc/localtime:/etc/localtime:ro \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --runtime=nvidia --gpus all \
  liosam-humble-jammy bash
```

### 使用 docker-compose

```bash
# 啟動容器
docker-compose up -d

# 進入容器
docker exec -it liosam-humble-jammy-container bash

# 停止容器
docker-compose down
```

---

## 性能優化建議

### 1. 即時性改進

- 減小 `mappingProcessInterval`（但不要過小）
- 增加 `numberOfCores` 用於並行處理
- 調整 `downsampleRate` 進行點雲下採樣

### 2. 準確性改進

- 增加關鍵幀密度：降低 `surroundingKeyframeDensity`
- 調整特徵提取閾值：降低 `edgeThreshold` 和 `surfThreshold`
- 啟用閉環檢測：`loopClosureEnableFlag: true`

### 3. 內存優化

- 使用適當的下採樣率
- 調整 `globalMapVisualizationLeafSize` 減少可視化負擔
- 定期清理舊的中間結果

---

## 實驗建議

### 初次測試步驟

1. **準備數據**
   - 準備包含激光雷達和 IMU 數據的 ROS Bag
   - 確認點雲和 IMU 數據的主題名稱

2. **驗證數據格式**
   - 檢查點雲是否包含時間戳和環號
   - 確認 IMU 數據的發布頻率

3. **配置參數**
   - 根據硬件修改傳感器參數
   - 調整 IMU 外參

4. **運行系統**
   - 啟動 LIO-SAM
   - 播放 Bag 文件
   - 觀察 RViz 中的軌跡

5. **調試和優化**
   - 檢查軌跡質量
   - 根據結果調整參數
   - 重複運行驗證穩定性

### 調試技巧

#### 啟用 IMU 調試輸出

在 `imageProjection.cpp` 的 `imuHandler()` 中取消註釋調試行：

```cpp
// 觀察轉換後的 IMU 數據
std::cout << "IMU accel: " << imuAcc << std::endl;
std::cout << "IMU gyro: " << imuGyr << std::endl;
```

然後重新編譯：

```bash
colcon build --symlink-install
```

#### 驗證 IMU 方向

- 手動旋轉傳感器
- 檢查 RViz 中 IMU 坐標軸的顏色和方向
- 確保旋轉與實際運動一致

---

## 相關資源

### 論文

LIO-SAM 論文：[Tightly-coupled Lidar Inertial Odometry via Smoothing and Mapping (IROS 2020)](https://github.com/TixiaoShan/LIO-SAM/blob/master/config/doc/paper.pdf)

```bibtex
@inproceedings{liosam2020shan,
  title={LIO-SAM: Tightly-coupled Lidar Inertial Odometry via Smoothing and Mapping},
  author={Shan, Tixiao and Englot, Brendan and Meyers, Drew and Wang, Wei and Ratti, Carlo and Rus Daniela},
  booktitle={IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
  pages={5135-5142},
  year={2020},
  organization={IEEE}
}
```

### 相關項目

- **[ScanContext](https://github.com/irapkaist/SC-LeGO-LOAM)** - 改進的閉環檢測
- **[SC-LIO-SAM](https://github.com/gisbi-kim/SC-LIO-SAM)** - LIO-SAM + ScanContext
- **[Lidar-IMU Calibration](https://github.com/chennuo0125-HIT/lidar_imu_calib)** - 傳感器標定工具
- **[LeGO-LOAM](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)** - 基礎算法

### ROS2 驅動

- [ros2_ouster_drivers](https://github.com/ros-drivers/ros2_ouster_drivers)
- [bluespace_ai_xsens_ros_mti_driver](https://github.com/bluespace-ai/bluespace_ai_xsens_ros_mti_driver)
- [sbg_ros2_driver](https://github.com/SBG-Systems/sbg_ros2_driver)

---

## 故障排除速查表

| 問題 | 可能原因 | 解決方案 |
|------|--------|---------|
| 軌跡漂移 | IMU 偏差未正確估計 | 增加初始化時間，調整噪聲參數 |
| 地圖破損 | 點雲去畸變失敗 | 檢查時間戳同步，驗證 IMU 配置 |
| CPU 占用率高 | 點雲數據過多 | 增加下採樣率，調整濾波器大小 |
| GPS 融合失效 | 變換關係不完整 | 確保 GPS 到 base_link 的完整變換鏈 |
| 內存持續增長 | 舊數據未清理 | 檢查地圖保存設置，重啟節點 |

---

## 常見命令速查

```bash
# 編譯項目
colcon build --symlink-install

# 源環境
source ~/ros2_ws/install/setup.bash

# 啟動 LIO-SAM
ros2 launch lio_sam run.launch.py

# 播放 Bag 文件
ros2 bag play <bag-file> --loop

# 保存地圖
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap

# 列出活動節點
ros2 node list

# 列出主題
ros2 topic list

# 檢查主題數據# LIO-SAM 使用者手冊

## 目錄
1. [系統簡介](#系統簡介)
2. [系統架構](#系統架構)
3. [依賴項目與安裝](#依賴項目與安裝)
4. [感測器準備](#感測器準備)
5. [參數配置](#參數配置)
6. [運行系統](#運行系統)
7. [保存地圖](#保存地圖)
8. [進階功能](#進階功能)
9. [故障排除](#故障排除)

---

## 系統簡介

LIO-SAM（Tightly-coupled Lidar Inertial Odometry via Smoothing and Mapping）是一個基於因子圖的緊耦合激光雷達慣性里程計框架，能夠實現高精度、即時的移動機器人軌跡估計和地圖構建。

### 主要特點
- **因子圖架構**：支援多感測器融合，可輕鬆整合 IMU、GPS、迴圈檢測等多種測量來源- **即時性能**：採用局部滑動窗口的掃描匹配方法，而非全局地圖匹配，大幅提升運算效率- **高精度**：利用 IMU 預積分進行點雲去扭曲，並提供激光里程計優化的初始猜測---

## 系統架構

LIO-SAM 維護兩個因子圖並以高達 10 倍於即時速度運行：

1. **mapOptimization.cpp**：優化激光里程計因子和 GPS 因子，在整個測試過程中保持一致性
2. **imuPreintegration.cpp**：優化 IMU 和激光里程計因子，估計 IMU 偏差，定期重置以保證 IMU 頻率的即時里程計估計

### 四種因子類型- **IMU 預積分因子**：用於點雲去扭曲和提供運動初始估計
- **激光里程計因子**：通過掃描匹配獲得的位姿約束
- **GPS 因子**：提供絕對位置測量（可選）
- **迴圈閉合因子**：消除長時間累積的漂移

---

## 依賴項目與安裝

### 系統要求
- **作業系統**：Ubuntu 20.04（Foxy/Galactic）或 Ubuntu 22.04（Humble）- **ROS2 版本**：Foxy、Galactic 或 Humble

### 依賴套件安裝

```bash
# 安裝 ROS2 相關套件
sudo apt install ros-<ros2-version>-perception-pcl \
                 ros-<ros2-version>-pcl-msgs \
                 ros-<ros2-version>-vision-opencv \
                 ros-<ros2-version>-xacro
``````bash
# 安裝 GTSAM（Georgia Tech Smoothing and Mapping library）
sudo add-apt-repository ppa:borglab/gtsam-release-4.1
sudo apt install libgtsam-dev libgtsam-unstable-dev
```### 編譯安裝

```bash
cd ~/ros2_ws/src
git clone https://github.com/TixiaoShan/LIO-SAM.git
cd LIO-SAM
git checkout ros2
cd ..
colcon build
```### 使用 Docker（可選）

```bash
# 建立映像（基於 ROS2 Humble）
docker build -t liosam-humble-jammy .

# 啟動容器
docker run --init -it -d \
  --name liosam-humble-jammy-container \
  -v /etc/localtime:/etc/localtime:ro \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --runtime=nvidia --gpus all \
  liosam-humble-jammy bash
```---

## 感測器準備

### 激光雷達要求LIO-SAM 需要點雲數據符合以下格式才能正確進行點雲去扭曲：

#### 1. 提供點時間戳
- 每個點需包含相對於掃描開始的時間信息（通道名稱為 "time"）
- 當激光雷達以 10Hz 旋轉時，點的時間戳應在 0 到 0.1 秒之間變化
- 定義位於 `imageProjection.cpp` 頂部#### 2. 提供點環號（Ring Number）
- 用於將點正確組織成矩陣形式
- 指示該點屬於感測器的哪個通道
- 目前僅支援機械式激光雷達#### 感測器特定配置

**Velodyne 激光雷達**：
- 最新的 ROS 驅動應直接輸出所需信息**Ouster 激光雷達**：
- **硬體**：
  - 使用外部 IMU（內建 6 軸 IMU 不支援）
  - 將驅動的 `timestamp_mode` 設為 `TIME_FROM_PTP_1588`
- **配置**：
  - 在 `params.yaml` 中設定 `sensor: ouster`
  - 根據激光雷達型號調整 `N_SCAN` 和 `Horizon_SCAN`（如 128 線：`N_SCAN=128, Horizon_SCAN=1024`）

### IMU 要求#### 1. IMU 規格
- **必需**：9 軸 IMU（提供 roll、pitch、yaw 估計）
- **建議輸出頻率**：至少 200Hz（測試使用 Microstrain 3DM-GX5-25，500Hz）
- **注意**：Ouster 內建 IMU 為 6 軸，不符合要求

#### 2. IMU 對齊（非常重要！）

LIO-SAM 將 IMU 原始數據從 IMU 座標系轉換到激光雷達座標系（遵循 ROS REP-105 慣例：x-前、y-左、z-上）。需在 `params.yaml` 中提供兩個外參：

- **`extrinsicRot`**：將 IMU 陀螺儀和加速度計測量轉換到激光雷達座標系的旋轉矩陣
- **`extrinsicRPY`**：將 IMU 姿態轉換到激光雷達座標系的旋轉矩陣

**為什麼有兩個外參？** 某些 IMU（如 Microstrain 3DM-GX5-25）的加速度和姿態測量使用不同的座標系。

#### 3. IMU 調試（強烈建議）

在 `imageProjection.cpp` 的 `imuHandler()` 中取消調試程式碼的註解，驗證轉換後的 IMU 數據：

```cpp
// 在 imuHandler() 中取消註解
cout << "IMU acc: " << endl;
cout << "x: " << thisImu.linear_acceleration.x << 
      ", y: " << thisImu.linear_acceleration.y << 
      ", z: " << thisImu.linear_acceleration.z << endl;
```旋轉感測器套件，檢查讀數是否與實際運動對應。

---

## 參數配置

主要配置文件為 `params.yaml`。以下是關鍵參數說明：

### 話題設定
```yaml
pointCloudTopic: "/points"       # 點雲數據
imuTopic: "/imu/data"            # IMU 數據
odomTopic: "odometry/imu"        # IMU 預積分里程計
gpsTopic: "odometry/gpsz"        # GPS 里程計（可選）
```### 座標系
```yaml
lidarFrame: "lidar_link"
baselinkFrame: "base_link"
odometryFrame: "odom"
mapFrame: "map"
```### GPS 設定
```yaml
useImuHeadingInitialization: false  # 使用 GPS 時設為 true
useGpsElevation: false              # GPS 高程不佳時設為 false
gpsCovThreshold: 2.0                # GPS 數據使用閾值（m²）
poseCovThreshold: 25.0              # 位姿協方差閾值（m²）
```### 感測器設定
```yaml
sensor: ouster                   # velodyne、ouster 或 livox
N_SCAN: 64                       # 激光雷達通道數
Horizon_SCAN: 512                # 水平分辨率
downsampleRate: 1                # 降採樣率
lidarMinRange: 1.0               # 最小範圍（m）
lidarMaxRange: 1000.0            # 最大範圍（m）
```### IMU 設定
```yaml
imuAccNoise: 3.9939570888238808e-03
imuGyrNoise: 1.5636343949698187e-03
imuAccBiasN: 6.4356659353532566e-05
imuGyrBiasN: 3.5640318696367613e-05
imuGravity: 9.80511
imuRPYWeight: 0.01
```### 外參（根據實際安裝調整）
```yaml
extrinsicTrans: [0.0, 0.0, 0.0]
extrinsicRot: [-1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, -1.0]
extrinsicRPY: [0.0, 1.0, 0.0,
              -1.0, 0.0, 0.0,
               0.0, 0.0, 1.0]
```### LOAM 特徵閾值
```yaml
edgeThreshold: 1.0                # 邊緣特徵閾值
surfThreshold: 0.1                # 平面特徵閾值
edgeFeatureMinValidNum: 10
surfFeatureMinValidNum: 100
```### 迴圈閉合
```yaml
loopClosureEnableFlag: true
loopClosureFrequency: 1.0         # Hz
historyKeyframeSearchRadius: 15.0 # 搜索半徑（m）
historyKeyframeSearchTimeDiff: 30.0  # 時間差（s）
historyKeyframeFitnessScore: 0.3  # ICP 閾值
```---

## 運行系統

### 1. 啟動 LIO-SAM

```bash
ros2 launch lio_sam run.launch.py
```launch 文件會自動啟動以下節點：
- `lio_sam_imuPreintegration`：IMU 預積分
- `lio_sam_imageProjection`：圖像投影與去扭曲
- `lio_sam_featureExtraction`：特徵提取
- `lio_sam_mapOptimization`：地圖優化
- `robot_state_publisher`：機器人狀態發布
- `rviz2`：視覺化

### 2. 播放數據包

```bash
ros2 bag play your-bag.bag
```**注意**：
- 確保 bag 文件包含激光雷達和 IMU 數據
- 檢查時間戳是否同步- 建議首次測試時以 `-r 1`（即時速度）播放

### 3. 視覺化

在 Rviz2 中可查看：
- **Trajectory**：機器人軌跡（`lio_sam/mapping/trajectory`）
- **Map (cloud)**：局部點雲地圖（`lio_sam/mapping/map_global`）
- **Map (global)**：全局優化後的地圖（啟用迴圈閉合時使用）- **Odom GPS**：GPS 里程計（若使用 GPS）---

## 保存地圖

### 基本保存

```bash
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap
```地圖將保存到默認目錄：`~/Downloads/LOAM/`### 自訂解析度與路徑

```bash
ros2 service call /lio_sam/save_map lio_sam/srv/SaveMap \
  "{resolution: 0.2, destination: /Downloads/service_LOAM}"
```### 保存的文件- `trajectory.pcd`：關鍵幀位姿（3D 點）
- `transformations.pcd`：關鍵幀變換（6D 位姿）
- `CornerMap.pcd`：邊緣特徵地圖
- `SurfMap.pcd`：平面特徵地圖
- `GlobalMap.pcd`：完整全局地圖

---

## 進階功能

### 1. 迴圈閉合迴圈閉合功能可消除長時間累積的漂移：

1. 在 `params.yaml` 中設定 `loopClosureEnableFlag: true`
2. 在 Rviz2 中：
   - 取消勾選 "Map (cloud)"
   - 勾選 "Map (global)"
3. 建議以 `-r 1` 速度播放（ICP 運算較慢）

**注意**：目前的迴圈閉合直接改編自 LeGO-LOAM，基於 ICP 方法。如需更進階的實作，可參考 [ScanContext](https://github.com/irapkaist/SC-LeGO-LOAM)。

### 2. GPS 融合啟用 GPS 功能：

1. 將 `params.yaml` 中的 `gpsTopic` 改為 `"odometry/gps"`
2. 調整參數：
   - `gpsCovThreshold`：過濾不良 GPS 讀數
   - `poseCovThreshold`：調整 GPS 因子加入頻率（值越小，GPS 修正越頻繁）
3. 在 Rviz2 中勾選 "Odom GPS" 和 "Map (global)"

**範例效果**：Park 數據集展示了 LIO-GPS 和 LIO-SAM 達到相似的 RMSE 誤差（相對於 GPS 真值）。

### 3. KITTI 數據集支援KITTI 原始數據需調整以下參數：

```yaml
extrinsicTrans: [-8.086759e-01, 3.195559e-01, -7.997231e-01]
extrinsicRot: [9.999976e-01, 7.553071e-04, -2.035826e-03,
              -7.854027e-04, 9.998898e-01, -1.482298e-02,
               2.024406e-03, 1.482454e-02, 9.998881e-01]
extrinsicRPY: [9.999976e-01, 7.553071e-04, -2.035826e-03,
              -7.854027e-04, 9.998898e-01, -1.482298e-02,
               2.024406e-03, 1.482454e-02, 9.998881e-01]
N_SCAN: 64
downsampleRate: 2  # 或 4
loopClosureEnableFlag: true  # 或 false
```

**限制**：KITTI IMU 的內參未知，對精度有較大影響。

---

## 故障排除

### 常見問題

#### 1. 之字形或抖動行為**原因**：激光雷達和 IMU 數據時間戳未同步  
**解決方案**：
- 檢查 bag 文件中兩者的時間戳
- 確認感測器驅動配置正確

#### 2. 上下跳動**原因**：IMU 外參錯誤（如重力加速度為負值）  
**解決方案**：
- 使用 IMU 調試功能驗證轉換是否正確
- 檢查 `extrinsicRot` 和 `extrinsicRPY` 配置

#### 3. mapOptimization 崩潰**原因**：通常由 GTSAM 引起  
**解決方案**：
- 安裝 README 指定的 GTSAM 版本
- 參考 [GitHub Issues](https://github.com/TixiaoShan/LIO-SAM/issues)

#### 4. GPS 里程計不可用**原因**：缺少 frame_id 之間的變換  
**解決方案**：
- 確保 `imu_frame_id` 和 `gps_frame_id` 到 `base_link` 的變換可用
- 參考 [Robot Localization 文檔](http://docs.ros.org/en/melodic/api/robot_localization/html/preparing_sensor_data.html)

### 性能基準以下是處理一幀掃描的平均運行時間（ms）：

| 數據集      | LOAM  | LIOM  | LIO-SAM | 壓力測試 |
|------------|-------|-------|---------|----------|
| Rotation   | 83.6  | 失敗   | 41.9    | 13×      |
| Walking    | 253.6 | 339.8 | 58.4    | 13×      |
| Campus     | 244.9 | 失敗   | 97.8    | 10×      |
| Park       | 266.4 | 245.2 | 100.5   | 9×       |
| Amsterdam  | 失敗   | 失敗   | 79.3    | 11×      |

**結論**：LIO-SAM 比其他方法快得多，且能以高達 13 倍即時速度處理數據。

---

## 引用

如使用本程式碼，請引用 LIO-SAM (IROS-2020) 論文：

```bibtex
@inproceedings{liosam2020shan,
  title={LIO-SAM: Tightly-coupled Lidar Inertial Odometry via Smoothing and Mapping},
  author={Shan, Tixiao and Englot, Brendan and Meyers, Drew and Wang, Wei and Ratti, Carlo and Rus Daniela},
  booktitle={IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
  pages={5135-5142},
  year={2020},
  organization={IEEE}
}
```

部分程式碼改編自 [LeGO-LOAM](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)。

---

## 相關資源

- **激光雷達-IMU 校準**：[lidar_imu_calib](https://github.com/chennuo0125-HIT/lidar_imu_calib)- **LIO-SAM with Scan Context**：[SC-LIO-SAM](https://github.com/gisbi-kim/SC-LIO-SAM)- **原始碼**：[GitHub - LIO-SAM](https://github.com/TixiaoShan/LIO-SAM)
- **示範影片**：[YouTube](https://www.youtube.com/watch?v=A0H8CoORZJU)---

**維護者**：Tixiao Shan（麻省理工學院）  
**版本**：ROS2（支援 Foxy、Galactic、Humble）  
**授權**：TODO
ros2 topic echo /topic-name

# 啟動 RViz
ros2 run rviz2 rviz2
```

---

**最後更新**：2026 年 2 月
**版本**：LIO-SAM ROS2
