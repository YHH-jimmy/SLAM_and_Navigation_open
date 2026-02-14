#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KITTI to ROS2 Bag Converter
Converts KITTI Raw and Odometry datasets to ROS2 bag format
Supports: IMU, GPS, LiDAR (Velodyne), Camera, Odometry
"""

import sys
import os
import cv2
import numpy as np
import argparse
from tqdm import tqdm
from datetime import datetime
from pathlib import Path

try:
    import pykitti
except ImportError as e:
    print('Could not load module \'pykitti\'. Please run `pip install pykitti`')
    sys.exit(1)

import rclpy
from rclpy.serialization import serialize_message
from rclpy.time import Time
from rclpy.duration import Duration
import rosbag2_py

from sensor_msgs.msg import CameraInfo, Imu, PointField, NavSatFix, Image, PointCloud2
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, TwistStamped, Transform, Quaternion as QuaternionMsg
from tf2_msgs.msg import TFMessage
from std_msgs.msg import Header
from cv_bridge import CvBridge


def quaternion_from_euler(roll, pitch, yaw):
    """
    Convert Euler angles to quaternion
    """
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    q = QuaternionMsg()
    q.w = cr * cp * cy + sr * sp * sy
    q.x = sr * cp * cy - cr * sp * sy
    q.y = cr * sp * cy + sr * cp * sy
    q.z = cr * cp * sy - sr * sp * cy

    return [q.x, q.y, q.z, q.w]


def quaternion_from_matrix(matrix):
    """
    Convert rotation matrix to quaternion
    """
    trace = np.trace(matrix[:3, :3])
    
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (matrix[2, 1] - matrix[1, 2]) * s
        y = (matrix[0, 2] - matrix[2, 0]) * s
        z = (matrix[1, 0] - matrix[0, 1]) * s
    elif matrix[0, 0] > matrix[1, 1] and matrix[0, 0] > matrix[2, 2]:
        s = 2.0 * np.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2])
        w = (matrix[2, 1] - matrix[1, 2]) / s
        x = 0.25 * s
        y = (matrix[0, 1] + matrix[1, 0]) / s
        z = (matrix[0, 2] + matrix[2, 0]) / s
    elif matrix[1, 1] > matrix[2, 2]:
        s = 2.0 * np.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2])
        w = (matrix[0, 2] - matrix[2, 0]) / s
        x = (matrix[0, 1] + matrix[1, 0]) / s
        y = 0.25 * s
        z = (matrix[1, 2] + matrix[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1])
        w = (matrix[1, 0] - matrix[0, 1]) / s
        x = (matrix[0, 2] + matrix[2, 0]) / s
        y = (matrix[1, 2] + matrix[2, 1]) / s
        z = 0.25 * s
    
    return [x, y, z, w]


def inv(transform):
    """Invert rigid body transformation matrix"""
    R = transform[0:3, 0:3]
    t = transform[0:3, 3]
    t_inv = -1 * R.T.dot(t)
    transform_inv = np.eye(4)
    transform_inv[0:3, 0:3] = R.T
    transform_inv[0:3, 3] = t_inv
    return transform_inv


def save_imu_data_raw(writer, kitti, imu_frame_id, topic):
    """Export raw IMU data with high frequency"""
    print("Exporting IMU Raw Data...")
    synced_path = kitti.data_path
    unsynced_path = synced_path.replace('sync', 'extract')
    imu_path = os.path.join(unsynced_path, 'oxts')

    # Read timestamps
    with open(os.path.join(imu_path, 'timestamps.txt')) as f:
        lines = f.readlines()
        imu_datetimes = []
        for line in lines:
            if len(line) == 1:
                continue
            timestamp = datetime.strptime(line[:-4], '%Y-%m-%d %H:%M:%S.%f')
            imu_datetimes.append(float(timestamp.strftime("%s.%f")))

    # Fix IMU time using linear model
    imu_index = np.asarray(range(len(imu_datetimes)), dtype=np.float64)
    z = np.polyfit(imu_index, imu_datetimes, 1)
    imu_datetimes_new = z[0] * imu_index + z[1]
    imu_datetimes = imu_datetimes_new.tolist()

    # Get all IMU data
    imu_data_dir = os.path.join(imu_path, 'data')
    imu_filenames = sorted(os.listdir(imu_data_dir))
    imu_data = [None] * len(imu_filenames)
    for i, imu_file in enumerate(imu_filenames):
        imu_data_file = open(os.path.join(imu_data_dir, imu_file), "r")
        for line in imu_data_file:
            if len(line) == 1:
                continue
            stripped_line = line.strip()
            line_list = stripped_line.split()
            imu_data[i] = line_list

    assert len(imu_datetimes) == len(imu_data)
    
    for timestamp, data in tqdm(zip(imu_datetimes, imu_data), total=len(imu_data), desc="IMU"):
        roll, pitch, yaw = float(data[3]), float(data[4]), float(data[5])
        q = quaternion_from_euler(roll, pitch, yaw)
        
        imu = Imu()
        imu.header.frame_id = imu_frame_id
        imu.header.stamp = Time(seconds=timestamp).to_msg()
        imu.orientation.x = q[0]
        imu.orientation.y = q[1]
        imu.orientation.z = q[2]
        imu.orientation.w = q[3]
        imu.linear_acceleration.x = float(data[11])
        imu.linear_acceleration.y = float(data[12])
        imu.linear_acceleration.z = float(data[13])
        imu.angular_velocity.x = float(data[17])
        imu.angular_velocity.y = float(data[18])
        imu.angular_velocity.z = float(data[19])
        
        timestamp_ns = int(timestamp * 1e9)
        writer.write(topic, serialize_message(imu), timestamp_ns)
        
        # Also write to /imu_correct for LIO-SAM compatibility
        imu.header.frame_id = 'imu_enu_link'
        writer.write('/imu_correct', serialize_message(imu), timestamp_ns)


def save_gps_fix_data(writer, kitti, gps_frame_id, topic):
    """Export GPS fix data"""
    print("Exporting GPS Fix Data...")
    for timestamp, oxts in tqdm(zip(kitti.timestamps, kitti.oxts), total=len(kitti.timestamps), desc="GPS Fix"):
        navsatfix_msg = NavSatFix()
        navsatfix_msg.header.frame_id = gps_frame_id
        timestamp_sec = float(timestamp.strftime("%s.%f"))
        navsatfix_msg.header.stamp = Time(seconds=timestamp_sec).to_msg()
        navsatfix_msg.latitude = oxts.packet.lat
        navsatfix_msg.longitude = oxts.packet.lon
        navsatfix_msg.altitude = oxts.packet.alt
        navsatfix_msg.status.service = 1
        
        timestamp_ns = int(timestamp_sec * 1e9)
        writer.write(topic, serialize_message(navsatfix_msg), timestamp_ns)


def save_gps_vel_data(writer, kitti, gps_frame_id, topic):
    """Export GPS velocity data"""
    print("Exporting GPS Velocity Data...")
    for timestamp, oxts in tqdm(zip(kitti.timestamps, kitti.oxts), total=len(kitti.timestamps), desc="GPS Vel"):
        twist_msg = TwistStamped()
        twist_msg.header.frame_id = gps_frame_id
        timestamp_sec = float(timestamp.strftime("%s.%f"))
        twist_msg.header.stamp = Time(seconds=timestamp_sec).to_msg()
        twist_msg.twist.linear.x = oxts.packet.vf
        twist_msg.twist.linear.y = oxts.packet.vl
        twist_msg.twist.linear.z = oxts.packet.vu
        twist_msg.twist.angular.x = oxts.packet.wf
        twist_msg.twist.angular.y = oxts.packet.wl
        twist_msg.twist.angular.z = oxts.packet.wu
        
        timestamp_ns = int(timestamp_sec * 1e9)
        writer.write(topic, serialize_message(twist_msg), timestamp_ns)


def create_point_cloud2(header, points):
    """Create PointCloud2 message with ring information"""
    fields = [
        PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
        PointField(name='ring', offset=16, datatype=PointField.UINT16, count=1)
    ]
    
    # Pack point data
    point_step = 18  # 4+4+4+4+2
    cloud_data = []
    
    for point in points:
        x, y, z, intensity, ring = point
        cloud_data.append(np.array([x, y, z, intensity], dtype=np.float32).tobytes())
        cloud_data.append(np.array([ring], dtype=np.uint16).tobytes())
    
    pcl_msg = PointCloud2()
    pcl_msg.header = header
    pcl_msg.height = 1
    pcl_msg.width = len(points)
    pcl_msg.fields = fields
    pcl_msg.is_bigendian = False
    pcl_msg.point_step = point_step
    pcl_msg.row_step = point_step * len(points)
    pcl_msg.is_dense = True
    pcl_msg.data = b''.join(cloud_data)
    
    return pcl_msg


def save_velo_data(writer, kitti, velo_frame_id, topic):
    """Export Velodyne LiDAR point cloud data with ring information"""
    print("Exporting Velodyne Point Cloud Data...")
    velo_path = os.path.join(kitti.data_path, 'velodyne_points')
    velo_data_dir = os.path.join(velo_path, 'data')
    velo_filenames = sorted(os.listdir(velo_data_dir))
    
    with open(os.path.join(velo_path, 'timestamps.txt')) as f:
        lines = f.readlines()
        velo_datetimes = []
        for line in lines:
            if len(line) == 1:
                continue
            dt = datetime.strptime(line[:-4], '%Y-%m-%d %H:%M:%S.%f')
            velo_datetimes.append(dt)

    for dt, filename in tqdm(zip(velo_datetimes, velo_filenames), total=len(velo_filenames), desc="Velodyne"):
        if dt is None:
            continue

        velo_filename = os.path.join(velo_data_dir, filename)
        
        # Read binary data
        scan = (np.fromfile(velo_filename, dtype=np.float32)).reshape(-1, 4)

        # Calculate ring channel
        depth = np.linalg.norm(scan, 2, axis=1)
        pitch = np.arcsin(scan[:, 2] / depth)
        fov_down = -24.8 / 180.0 * np.pi
        fov = (abs(-24.8) + abs(2.0)) / 180.0 * np.pi
        proj_y = (pitch + abs(fov_down)) / fov
        proj_y *= 64
        proj_y = np.floor(proj_y)
        proj_y = np.minimum(64 - 1, proj_y)
        proj_y = np.maximum(0, proj_y).astype(np.uint16)
        
        # Combine scan with ring
        scan_with_ring = []
        for i in range(len(scan)):
            scan_with_ring.append([scan[i][0], scan[i][1], scan[i][2], scan[i][3], int(proj_y[i])])

        # Create header
        timestamp_sec = float(dt.strftime("%s.%f"))
        header = Header()
        header.frame_id = velo_frame_id
        header.stamp = Time(seconds=timestamp_sec).to_msg()

        # Create PointCloud2 message
        pcl_msg = create_point_cloud2(header, scan_with_ring)
        
        timestamp_ns = int(timestamp_sec * 1e9)
        writer.write(topic, serialize_message(pcl_msg), timestamp_ns)


def save_camera_data(writer, kitti_type, kitti, util, bridge, camera, camera_frame_id, topic, initial_time):
    """Export camera image and camera info data"""
    print(f"Exporting Camera {camera}...")
    
    if kitti_type.find("raw") != -1:
        camera_pad = '{0:02d}'.format(camera)
        image_dir = os.path.join(kitti.data_path, 'image_{}'.format(camera_pad))
        image_path = os.path.join(image_dir, 'data')
        image_filenames = sorted(os.listdir(image_path))
        
        with open(os.path.join(image_dir, 'timestamps.txt')) as f:
            image_datetimes = [datetime.strptime(x[:-4], '%Y-%m-%d %H:%M:%S.%f') for x in f.readlines()]
        
        calib = CameraInfo()
        calib.header.frame_id = camera_frame_id
        calib.width, calib.height = [int(x) for x in util['S_rect_{}'.format(camera_pad)].tolist()]
        calib.distortion_model = 'plumb_bob'
        calib.k = util['K_{}'.format(camera_pad)].flatten().tolist()
        calib.r = util['R_rect_{}'.format(camera_pad)].flatten().tolist()
        calib.d = util['D_{}'.format(camera_pad)].flatten().tolist()
        calib.p = util['P_rect_{}'.format(camera_pad)].flatten().tolist()
            
    elif kitti_type.find("odom") != -1:
        camera_pad = '{0:01d}'.format(camera)
        image_path = os.path.join(kitti.sequence_path, 'image_{}'.format(camera_pad))
        image_filenames = sorted(os.listdir(image_path))
        image_datetimes = [initial_time + x.total_seconds() for x in kitti.timestamps]
        
        calib = CameraInfo()
        calib.header.frame_id = camera_frame_id
        calib.p = util['P{}'.format(camera_pad)].flatten().tolist()
    
    for dt, filename in tqdm(zip(image_datetimes, image_filenames), total=len(image_filenames), desc=f"Camera {camera}"):
        image_filename = os.path.join(image_path, filename)
        cv_image = cv2.imread(image_filename)
        calib.height, calib.width = cv_image.shape[:2]
        
        if camera in (0, 1):
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        encoding = "mono8" if camera in (0, 1) else "bgr8"
        
        image_message = bridge.cv2_to_imgmsg(cv_image, encoding=encoding)
        image_message.header.frame_id = camera_frame_id
        
        if kitti_type.find("raw") != -1:
            timestamp_sec = float(dt.strftime("%s.%f"))
            topic_ext = "/image_raw"
        elif kitti_type.find("odom") != -1:
            timestamp_sec = dt
            topic_ext = "/image_rect"
            
        image_message.header.stamp = Time(seconds=timestamp_sec).to_msg()
        calib.header.stamp = image_message.header.stamp
        
        timestamp_ns = int(timestamp_sec * 1e9)
        writer.write(topic + topic_ext, serialize_message(image_message), timestamp_ns)
        writer.write(topic + '/camera_info', serialize_message(calib), timestamp_ns)


def save_static_transforms(writer, transforms, timestamps):
    """Export static TF transformations"""
    print("Exporting Static Transformations...")
    tfm = TFMessage()
    
    for transform in transforms:
        tf_msg = TransformStamped()
        tf_msg.header.frame_id = transform[0]
        tf_msg.child_frame_id = transform[1]
        
        t = transform[2][0:3, 3]
        q = quaternion_from_matrix(transform[2])
        
        tf_msg.transform.translation.x = float(t[0])
        tf_msg.transform.translation.y = float(t[1])
        tf_msg.transform.translation.z = float(t[2])
        tf_msg.transform.rotation.x = float(q[0])
        tf_msg.transform.rotation.y = float(q[1])
        tf_msg.transform.rotation.z = float(q[2])
        tf_msg.transform.rotation.w = float(q[3])
        
        tfm.transforms.append(tf_msg)
    
    for timestamp in tqdm(timestamps, desc="TF Static"):
        timestamp_sec = float(timestamp.strftime("%s.%f"))
        timestamp_ns = int(timestamp_sec * 1e9)
        
        for i in range(len(tfm.transforms)):
            tfm.transforms[i].header.stamp = Time(seconds=timestamp_sec).to_msg()
        
        writer.write('/tf_static', serialize_message(tfm), timestamp_ns)


def save_dynamic_tf(writer, kitti, kitti_type, initial_time):
    """Export dynamic TF transformations"""
    print("Exporting Dynamic Transformations...")
    
    if kitti_type.find("raw") != -1:
        for timestamp, oxts in tqdm(zip(kitti.timestamps, kitti.oxts), total=len(kitti.timestamps), desc="TF Dynamic"):
            tf_oxts_msg = TFMessage()
            tf_oxts_transform = TransformStamped()
            
            timestamp_sec = float(timestamp.strftime("%s.%f"))
            tf_oxts_transform.header.stamp = Time(seconds=timestamp_sec).to_msg()
            tf_oxts_transform.header.frame_id = 'world'
            tf_oxts_transform.child_frame_id = 'base_link'

            transform = oxts.T_w_imu
            t = transform[0:3, 3]
            q = quaternion_from_matrix(transform)

            tf_oxts_transform.transform.translation.x = t[0]
            tf_oxts_transform.transform.translation.y = t[1]
            tf_oxts_transform.transform.translation.z = t[2]
            tf_oxts_transform.transform.rotation.x = q[0]
            tf_oxts_transform.transform.rotation.y = q[1]
            tf_oxts_transform.transform.rotation.z = q[2]
            tf_oxts_transform.transform.rotation.w = q[3]

            tf_oxts_msg.transforms.append(tf_oxts_transform)
            
            timestamp_ns = int(timestamp_sec * 1e9)
            writer.write('/tf', serialize_message(tf_oxts_msg), timestamp_ns)

    elif kitti_type.find("odom") != -1:
        timestamps = [initial_time + x.total_seconds() for x in kitti.timestamps]
        
        for timestamp, tf_matrix in tqdm(zip(timestamps, kitti.T_w_cam0), total=len(timestamps), desc="TF Dynamic"):
            tf_msg = TFMessage()
            tf_stamped = TransformStamped()
            
            tf_stamped.header.stamp = Time(seconds=timestamp).to_msg()
            tf_stamped.header.frame_id = 'world'
            tf_stamped.child_frame_id = 'camera_left'
            
            t = tf_matrix[0:3, 3]
            q = quaternion_from_matrix(tf_matrix)

            tf_stamped.transform.translation.x = t[0]
            tf_stamped.transform.translation.y = t[1]
            tf_stamped.transform.translation.z = t[2]
            tf_stamped.transform.rotation.x = q[0]
            tf_stamped.transform.rotation.y = q[1]
            tf_stamped.transform.rotation.z = q[2]
            tf_stamped.transform.rotation.w = q[3]

            tf_msg.transforms.append(tf_stamped)
            
            timestamp_ns = int(timestamp * 1e9)
            writer.write('/tf', serialize_message(tf_msg), timestamp_ns)


def main(args=None):
    parser = argparse.ArgumentParser(description="Convert KITTI dataset to ROS2 bag format")
    
    # Accepted argument values
    kitti_types = ["raw_synced", "odom_color", "odom_gray"]
    odometry_sequences = [str(s).zfill(2) for s in range(22)]
    
    parser.add_argument("kitti_type", choices=kitti_types, help="KITTI dataset type")
    parser.add_argument("dir", nargs="?", default=os.getcwd(), 
                       help="Base directory of the dataset (default: current directory)")
    parser.add_argument("-t", "--date", help="Date of the raw dataset (e.g., 2011_09_26)")
    parser.add_argument("-r", "--drive", help="Drive number of the raw dataset (e.g., 0001)")
    parser.add_argument("-s", "--sequence", choices=odometry_sequences,
                       help="Sequence of the odometry dataset (00-21)")
    parser.add_argument("-o", "--output", help="Output bag directory (optional)")
    
    args = parser.parse_args()

    bridge = CvBridge()
    
    # Camera definitions
    cameras = [
        (0, 'camera_gray_left', '/kitti/camera_gray_left'),
        (1, 'camera_gray_right', '/kitti/camera_gray_right'),
        (2, 'camera_color_left', '/kitti/camera_color_left'),
        (3, 'camera_color_right', '/kitti/camera_color_right')
    ]

    # Process RAW dataset
    if args.kitti_type.find("raw") != -1:
        if args.date is None:
            print("Error: Date option is required for raw dataset.")
            print("Usage: kitti2bag raw_synced [dir] -t <date> -r <drive>")
            sys.exit(1)
        elif args.drive is None:
            print("Error: Drive option is required for raw dataset.")
            print("Usage: kitti2bag raw_synced [dir] -t <date> -r <drive>")
            sys.exit(1)
        
        # Set output bag name
        if args.output:
            bag_name = args.output
        else:
            bag_name = f"kitti_{args.date}_drive_{args.drive}_{args.kitti_type[4:]}"
        
        # Initialize ROS2 bag writer
        writer = rosbag2_py.SequentialWriter()
        storage_options = rosbag2_py.StorageOptions(uri=bag_name, storage_id='sqlite3')
        converter_options = rosbag2_py.ConverterOptions('', '')
        writer.open(storage_options, converter_options)
        
        # Load KITTI data
        kitti = pykitti.raw(args.dir, args.date, args.drive)
        
        if not os.path.exists(kitti.data_path):
            print(f'Error: Path {kitti.data_path} does not exist.')
            sys.exit(1)

        if len(kitti.timestamps) == 0:
            print('Error: Dataset is empty.')
            sys.exit(1)

        try:
            # Create topics
            topics_to_create = [
                ('/imu_raw', 'sensor_msgs/msg/Imu'),
                ('/imu_correct', 'sensor_msgs/msg/Imu'),
                ('/gps/fix', 'sensor_msgs/msg/NavSatFix'),
                ('/gps/vel', 'geometry_msgs/msg/TwistStamped'),
                ('/points_raw', 'sensor_msgs/msg/PointCloud2'),
                ('/tf', 'tf2_msgs/msg/TFMessage'),
                ('/tf_static', 'tf2_msgs/msg/TFMessage'),
            ]
            
            for camera in cameras:
                topics_to_create.extend([
                    (camera[2] + '/image_raw', 'sensor_msgs/msg/Image'),
                    (camera[2] + '/camera_info', 'sensor_msgs/msg/CameraInfo'),
                ])
            
            for topic_name, topic_type in topics_to_create:
                topic_info = rosbag2_py.TopicMetadata(
                    name=topic_name, 
                    type=topic_type, 
                    serialization_format='cdr'
                )
                writer.create_topic(topic_info)
            
            # Frame IDs
            imu_frame_id = 'imu_link'
            velo_frame_id = 'velodyne'
            
            # Base link to IMU transform
            T_base_link_to_imu = np.eye(4, 4)
            T_base_link_to_imu[0:3, 3] = [-2.71/2.0-0.05, 0.32, 0.93]

            # Static transforms
            transforms = [
                ('base_link', imu_frame_id, T_base_link_to_imu),
                (imu_frame_id, velo_frame_id, inv(kitti.calib.T_velo_imu)),
                (imu_frame_id, cameras[0][1], inv(kitti.calib.T_cam0_imu)),
                (imu_frame_id, cameras[1][1], inv(kitti.calib.T_cam1_imu)),
                (imu_frame_id, cameras[2][1], inv(kitti.calib.T_cam2_imu)),
                (imu_frame_id, cameras[3][1], inv(kitti.calib.T_cam3_imu))
            ]

            util = pykitti.utils.read_calib_file(
                os.path.join(kitti.calib_path, 'calib_cam_to_cam.txt')
            )

            # Export data
            print(f"\n=== Converting KITTI Raw Dataset ===")
            print(f"Date: {args.date}, Drive: {args.drive}")
            print(f"Output: {bag_name}\n")
            
            save_static_transforms(writer, transforms, kitti.timestamps)
            save_dynamic_tf(writer, kitti, args.kitti_type, initial_time=None)
            save_imu_data_raw(writer, kitti, imu_frame_id, '/imu_raw')
            save_gps_fix_data(writer, kitti, imu_frame_id, '/gps/fix')
            save_gps_vel_data(writer, kitti, imu_frame_id, '/gps/vel')
            save_velo_data(writer, kitti, velo_frame_id, '/points_raw')
            
            for camera in cameras:
                save_camera_data(writer, args.kitti_type, kitti, util, bridge, 
                               camera=camera[0], camera_frame_id=camera[1], 
                               topic=camera[2], initial_time=None)

            print(f"\n✅ Conversion completed successfully!")
            print(f"📦 Bag file: {bag_name}")

        except Exception as e:
            print(f"\n❌ Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    # Process ODOMETRY dataset
    elif args.kitti_type.find("odom") != -1:
        if args.sequence is None:
            print("Error: Sequence option is required for odometry dataset.")
            print("Usage: kitti2bag {odom_color, odom_gray} [dir] -s <sequence>")
            sys.exit(1)
        
        # Set output bag name
        if args.output:
            bag_name = args.output
        else:
            bag_name = f"kitti_odometry_{args.kitti_type[5:]}_sequence_{args.sequence}"
        
        # Initialize ROS2 bag writer
        writer = rosbag2_py.SequentialWriter()
        storage_options = rosbag2_py.StorageOptions(uri=bag_name, storage_id='sqlite3')
        converter_options = rosbag2_py.ConverterOptions('', '')
        writer.open(storage_options, converter_options)
        
        kitti = pykitti.odometry(args.dir, args.sequence)
        
        if not os.path.exists(kitti.sequence_path):
            print(f'Error: Path {kitti.sequence_path} does not exist.')
            sys.exit(1)

        kitti.load_calib()
        kitti.load_timestamps()
             
        if len(kitti.timestamps) == 0:
            print('Error: Dataset is empty.')
            sys.exit(1)
            
        if args.sequence in odometry_sequences[:11]:
            print(f"Sequence {args.sequence} has ground truth poses.")
            kitti.load_poses()

        try:
            # Determine cameras to use
            if args.kitti_type.find("gray") != -1:
                used_cameras = cameras[:2]
            elif args.kitti_type.find("color") != -1:
                used_cameras = cameras[-2:]

            # Create topics
            topics_to_create = [
                ('/tf', 'tf2_msgs/msg/TFMessage'),
            ]
            
            for camera in used_cameras:
                topics_to_create.extend([
                    (camera[2] + '/image_rect', 'sensor_msgs/msg/Image'),
                    (camera[2] + '/camera_info', 'sensor_msgs/msg/CameraInfo'),
                ])
            
            for topic_name, topic_type in topics_to_create:
                topic_info = rosbag2_py.TopicMetadata(
                    name=topic_name, 
                    type=topic_type, 
                    serialization_format='cdr'
                )
                writer.create_topic(topic_info)

            util = pykitti.utils.read_calib_file(
                os.path.join(args.dir, 'sequences', args.sequence, 'calib.txt')
            )
            
            current_epoch = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
            
            print(f"\n=== Converting KITTI Odometry Dataset ===")
            print(f"Sequence: {args.sequence}, Type: {args.kitti_type}")
            print(f"Output: {bag_name}\n")
            
            # Export
            save_dynamic_tf(writer, kitti, args.kitti_type, initial_time=current_epoch)
            
            for camera in used_cameras:
                save_camera_data(writer, args.kitti_type, kitti, util, bridge,
                               camera=camera[0], camera_frame_id=camera[1],
                               topic=camera[2], initial_time=current_epoch)

            print(f"\n✅ Conversion completed successfully!")
            print(f"📦 Bag file: {bag_name}")

        except Exception as e:
            print(f"\n❌ Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
