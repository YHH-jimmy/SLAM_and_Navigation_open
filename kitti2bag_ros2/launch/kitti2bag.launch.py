#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """
    Launch file for KITTI to ROS2 bag conversion
    """
    
    # Declare launch arguments
    kitti_type_arg = DeclareLaunchArgument(
        'kitti_type',
        default_value='raw_synced',
        description='KITTI dataset type: raw_synced, odom_color, or odom_gray'
    )
    
    dataset_dir_arg = DeclareLaunchArgument(
        'dataset_dir',
        default_value='/path/to/kitti',
        description='Base directory of KITTI dataset'
    )
    
    date_arg = DeclareLaunchArgument(
        'date',
        default_value='2011_09_26',
        description='Date of raw dataset (for raw_synced only)'
    )
    
    drive_arg = DeclareLaunchArgument(
        'drive',
        default_value='0001',
        description='Drive number (for raw_synced only)'
    )
    
    sequence_arg = DeclareLaunchArgument(
        'sequence',
        default_value='00',
        description='Sequence number (for odom_* only)'
    )
    
    output_arg = DeclareLaunchArgument(
        'output',
        default_value='',
        description='Output bag directory (optional)'
    )
    
    # Get launch configurations
    kitti_type = LaunchConfiguration('kitti_type')
    dataset_dir = LaunchConfiguration('dataset_dir')
    date = LaunchConfiguration('date')
    drive = LaunchConfiguration('drive')
    sequence = LaunchConfiguration('sequence')
    output = LaunchConfiguration('output')
    
    # Note: This is a simplified version. In practice, you would run the conversion
    # as a standalone script rather than through a launch file, or create a ROS2 node
    # that performs the conversion.
    
    return LaunchDescription([
        kitti_type_arg,
        dataset_dir_arg,
        date_arg,
        drive_arg,
        sequence_arg,
        output_arg,
    ])
