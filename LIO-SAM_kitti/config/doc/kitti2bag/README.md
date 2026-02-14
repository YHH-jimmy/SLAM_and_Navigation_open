# kitti2bag

## How to run it?

```bash
aria2c -x 16 -s 16 -k 1M https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_drive_0084/2011_09_26_drive_0084_sync.zip
aria2c -x 16 -s 16 -k 1M https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_drive_0084/2011_09_26_drive_0084_extract.zip
aria2c -x 16 -s 16 -k 1M https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_calib.zip
unzip 2011_09_26_drive_0084_sync.zip
unzip 2011_09_26_drive_0084_extract.zip
unzip 2011_09_26_calib.zip
python kitti2bag.py -t 2011_09_26 -r 0084 raw_synced .
```

That's it. You have a bag that contains your data.

Other source files can be found at [KITTI raw data](http://www.cvlibs.net/datasets/kitti/raw_data.php) page.