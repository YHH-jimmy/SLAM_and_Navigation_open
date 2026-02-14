#!/bin/bash

# KITTI to ROS2 Bag 轉換範例腳本
# 使用方法: ./example_usage.sh

echo "=== KITTI to ROS2 Bag 轉換工具使用範例 ==="
echo ""

# 確保環境已載入
source /home/jimmyrtioms/ros2_ws/install/setup.bash

# 設定路徑 (請根據實際情況修改)
KITTI_RAW_DIR="/path/to/kitti/raw"
KITTI_ODOM_DIR="/path/to/kitti/odometry"
OUTPUT_DIR="/home/jimmyrtioms/ros2_ws/kitti_bags"

# 創建輸出目錄
mkdir -p $OUTPUT_DIR

echo "請選擇轉換類型:"
echo "1) RAW Dataset (完整感測器: IMU + GPS + LiDAR + Camera)"
echo "2) Odometry Dataset - Grayscale (僅相機)"
echo "3) Odometry Dataset - Color (僅相機)"
echo ""

read -p "請輸入選擇 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "=== 轉換 KITTI RAW Dataset ==="
        echo ""
        
        # 範例: 2011_09_26, drive 0001
        DATE="2011_09_26"
        DRIVE="0001"
        
        read -p "日期 (預設: $DATE): " input_date
        DATE=${input_date:-$DATE}
        
        read -p "Drive (預設: $DRIVE): " input_drive
        DRIVE=${input_drive:-$DRIVE}
        
        echo ""
        echo "開始轉換..."
        echo "資料集目錄: $KITTI_RAW_DIR"
        echo "日期: $DATE"
        echo "Drive: $DRIVE"
        echo ""
        
        cd $OUTPUT_DIR
        /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
            raw_synced $KITTI_RAW_DIR -t $DATE -r $DRIVE
        
        echo ""
        echo "✅ 完成! Bag 檔案位於: $OUTPUT_DIR"
        ;;
        
    2)
        echo ""
        echo "=== 轉換 KITTI Odometry Dataset (Grayscale) ==="
        echo ""
        
        SEQUENCE="00"
        
        read -p "序列號 (00-21, 預設: $SEQUENCE): " input_seq
        SEQUENCE=${input_seq:-$SEQUENCE}
        
        echo ""
        echo "開始轉換..."
        echo "資料集目錄: $KITTI_ODOM_DIR"
        echo "序列: $SEQUENCE"
        echo ""
        
        cd $OUTPUT_DIR
        /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
            odom_gray $KITTI_ODOM_DIR -s $SEQUENCE
        
        echo ""
        echo "✅ 完成! Bag 檔案位於: $OUTPUT_DIR"
        ;;
        
    3)
        echo ""
        echo "=== 轉換 KITTI Odometry Dataset (Color) ==="
        echo ""
        
        SEQUENCE="00"
        
        read -p "序列號 (00-21, 預設: $SEQUENCE): " input_seq
        SEQUENCE=${input_seq:-$SEQUENCE}
        
        echo ""
        echo "開始轉換..."
        echo "資料集目錄: $KITTI_ODOM_DIR"
        echo "序列: $SEQUENCE"
        echo ""
        
        cd $OUTPUT_DIR
        /home/jimmyrtioms/ros2_ws/install/kitti2bag_ros2/lib/kitti2bag_ros2/kitti2bag \
            odom_color $KITTI_ODOM_DIR -s $SEQUENCE
        
        echo ""
        echo "✅ 完成! Bag 檔案位於: $OUTPUT_DIR"
        ;;
        
    *)
        echo "無效的選擇"
        exit 1
        ;;
esac

echo ""
echo "=== 使用轉換後的 Bag 檔案 ==="
echo ""
echo "播放 bag:"
echo "  ros2 bag play <bag_name>"
echo ""
echo "查看 bag 資訊:"
echo "  ros2 bag info <bag_name>"
echo ""
echo "配合 LIO-SAM 使用:"
echo "  1. 播放 bag: ros2 bag play <bag_name>"
echo "  2. 執行 LIO-SAM: ros2 launch lio_sam run_kitti.launch.py"
echo ""
