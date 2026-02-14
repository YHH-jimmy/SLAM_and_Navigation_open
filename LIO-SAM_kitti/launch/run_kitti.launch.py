import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    package_dir = get_package_share_directory('lio_sam')
    
    # M2DGR specific configuration
    config_file = os.path.join(package_dir, 'config', 'params_kitti.yaml')
    rviz_config = os.path.join(package_dir, 'config', 'rviz2.rviz')

    return LaunchDescription([

        SetEnvironmentVariable('RCUTILS_CONSOLE_OUTPUT_FORMAT', '[{severity}]: {message}'),

        DeclareLaunchArgument(
            'config_file',
            default_value=config_file,
            description='Path to M2DGR configuration file'
        ),

        Node(
            package='lio_sam',
            executable='lio_sam_imuPreintegration',
            name='lio_sam_imuPreintegration',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),

        Node(
            package='lio_sam',
            executable='lio_sam_imageProjection',
            name='lio_sam_imageProjection',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),

        Node(
            package='lio_sam',
            executable='lio_sam_featureExtraction',
            name='lio_sam_featureExtraction',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),

        Node(
            package='lio_sam',
            executable='lio_sam_mapOptimization',
            name='lio_sam_mapOptimization',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        )
    ])
