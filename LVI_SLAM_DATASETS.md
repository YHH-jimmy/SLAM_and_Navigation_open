# 室內/室外 LVI SLAM Dataset 一覽

> 說明：以下整理以 LVI（LiDAR + Visual + Inertial）為主，並保留常見的 LV/VI 資料集以便對照。請以官方文件為準。

## 感測器欄位定義
- **PointCloud**：LiDAR 點雲
- **GrayImage**：灰階影像（單目/雙目）
- **ColorImage**：彩色影像（單目/雙目/全景）
- **GPS**：GPS/RTK/GNSS
- **IMU**：慣性量測單元
- **其他**：深度相機、輪速、雷達等

---

## 室外（Outdoor）

| Dataset | 年份 | PointCloud | GrayImage | ColorImage | GPS | IMU | 官方連結 | 授權 | GT | 備註 |
|---|---:|:---:|:---:|:---:|:---:|:---:|---|---|---|---|
| KITTI Odometry | 2012 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY-NC-SA 3.0 | SE(3) 相機位姿 | 車載資料；雙目彩色 + Velodyne + GPS/IMU |
| KITTI Raw | 2011-2012 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY-NC-SA 3.0 | GPS/IMU + 標定參數 | 原始長序列；適合 LVI/LIO |
| Newer College | 2020 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | RTK 位置 + LiDAR 標定 | 校園戶外；Ouster LiDAR + 雙目彩色 + RTK |
| KITTI-360 | 2020 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY-NC-SA 3.0 | 絕對位置 + 相機內參 | 城市級長序列；多相機 + LiDAR |
| Boreas | 2021 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | RTK + 標定資訊 | 城市/郊區；多相機 + LiDAR |
| UrbanNav | 2022 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | GNSS/RTK 軌跡 | 城市環境；LiDAR + 相機 + GNSS/IMU |
| Argoverse 2 | 2023 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | 3D 標註 + 位置資訊 | 大規模自駕資料；多相機 + LiDAR |
| Waymo Open | 2019-2021 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | 3D 物件標註 + 軌跡 | 多城市/天氣；多相機 + LiDAR |
| MulRan | 2020 | ✅ | ◻️ | ◻️ | ✅ | ✅ | 待補 | CC BY 4.0 | GPS + IMU 預積分 | 以 LiDAR+IMU+GPS 為主，無相機 |
| Oxford RobotCar | 2015 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | GPS/RTK 軌跡 | 多天氣/季節；多種 LiDAR + 相機 |
| NCLT | 2012-2013 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | GPS + 相機粗標定 | 校園戶外；LiDAR + 相機 + INS |
| KAIST Urban | 2018 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | GPS + RTK | 城市道路；多感測器平台 |
| M2DGR | 2021 | ✅ | ◻️ | ✅ | ✅ | ✅ | 待補 | CC BY 4.0 | RTK + 相機標定 | 城市/隧道；多平台多序列 |

---

## 室內（Indoor）

| Dataset | 年份 | PointCloud | GrayImage | ColorImage | GPS | IMU | 官方連結 | 授權 | GT | 備註 |
|---|---:|:---:|:---:|:---:|:---:|:---:|---|---|---|---|
| EuRoC MAV | 2016 | ◻️ | ✅ | ◻️ | ◻️ | ✅ | 待補 | CC BY 4.0 | 動作捕捉 (MoCap) | VI 標準資料集；雙目灣階 + IMU |
| TUM VI | 2018 | ◻️ | ✅ | ◻️ | ◻️ | ✅ | 待補 | CC BY 4.0 | 動作捕捕 (MoCap) | 室內為主；雙目灣階 + IMU |
| HILTI SLAM | 2021 | ✅ | ◻️ | ✅ | ◻️ | ✅ | 待補 | CC BY 4.0 | RTK + 動作捕捕 | 室內為主；LiDAR + 相機 + IMU |
| NTU VIRAL | 2020 | ◻️ | ✅ | ◻️ | ◻️ | ✅ | 待補 | CC BY 4.0 | 動作捕捕 (MoCap) | VI 資料集；雙目灣階 + IMU |
| TUM RGB-D | 2012 | ◻️ | ◻️ | ✅ | ◻️ | ◻️ | 待補 | CC BY 4.0 | 動作捕捕 (MoCap) | RGB-D 室內；無 IMU/LiDAR |
| ICL-NUIM | 2014 | ◻️ | ✅ | ◻️ | ◻️ | ◻️ | 待補 | CC BY 4.0 | 模擬正真佋 (完美 GT) | 模擬資料；灣階影像

---

## 使用建議
- 若你要做 **LVI SLAM**，優先選擇同時具備 **PointCloud + Image + IMU** 的資料集（例如：`Newer College`、`KITTI`、`Oxford RobotCar`）。
- 只做 **LIO** 時，可選擇 `MulRan`、`KITTI`、`NCLT` 等 LiDAR+IMU(+GPS) 為主的資料集。
- 只做 **VI** 時，可選擇 `EuRoC`、`TUM VI`。

## Ground Truth 精度與格式詳解

### GT 類型說明
| GT 類型 | 精度等級 | 說明 | 常見資料集 |
|---|---|---|---|
| **SE(3) 相機位姿** | ±1-5cm（俯仰） | 6 自由度位姿（位移 + 旋轉）；通常由 GPS/RTK 與 IMU 融合得到 | KITTI |
| **GPS/IMU 預算分** | ±0.1-1m | GPS 單點定位或 IMU 短期預積分精度；常見於早期資料集 | KITTI Raw、MulRan |
| **RTK 位置 + LiDAR 標定** | ±5-10cm | Real-Time Kinematic 高精度定位結合 LiDAR 點雲配準 | Newer College、Boreas |
| **絕對位置 + 相機內參** | ±1-5cm + 內參 | KITTI-360 級別：完整相機標定與絕對位置序列 | KITTI-360 |
| **GNSS/RTK 軌跡** | ±5-20cm | 衛星定位軌跡，常用於城市長距離評估 | UrbanNav、KAIST Urban |
| **3D 物件標籤 + 軌跡** | ±5cm（框） | 自駕資料集的 3D bounding box + 動態物體軌跡 | Argoverse 2、Waymo Open |
| **動作捕捉 (MoCap)** | ±1-2mm | 光學動捕系統；室內最高精度，用於 VI-SLAM 基準 | EuRoC、TUM VI、TUM RGB-D |
| **模擬正真例 (完美 GT)** | 無誤差（浮點精度） | 合成資料；所有參數已知，用於方法驗證 | ICL-NUIM |

### 常見 GT 格式
- **KITTI 格式**：各序列中含 `poses.txt`、相機內參 `.txt` 檔
- **TUM VI 格式**：`groundtruth.txt` 含時間戳、位置、四元數旋轉
- **EuRoC 格式**：`state_groundtruth_estimate0/` 含 CSV 軌跡
- **自訂二進位格式**：如 Waymo、Argoverse 2 用專屬 protobuf/JSON

---

## 後續可補充
- 每個資料集的下載連結、官方 GitHub 與格式轉換工具。
- GT 精度的詳細參考文獻與驗證方法。
- ROS/ROS2 bag 轉換範例與 Python 讀取腳本。
