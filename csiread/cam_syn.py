# batch processing of CSI and computer vision data
import glob
import os
import numpy as np
import csiread
import time
import sys


def main():
    cam_file = "2021.06.10.23.26.44"
    # wifi_dir = "/media/cooldev5/data/ReID/forge/wifi_csi/"
    # cam_dir = "/media/cooldev5/data/ReID/forge/east_entrance_cam/2021.06.10.23.26.44/"
    wifi_dir = "./"
    cam_dir1 = "./"
    cam_dir = cam_dir1 + cam_file + "/"

    pcap_all = glob.glob(wifi_dir + "*.pcap")
    pcap_all.sort(key=os.path.getmtime)

    pcap_now = wifi_dir + "1623382164609.pcap"
    cam_list = cam_dir + "list.txt"
    cam_csi_syn(cam_list, cam_file, pcap_now, pcap_all)


def cam_csi_syn(cam_list, cam_file, pcap_now, pcap_all):
    """
    Args:
        cam_list: txt file with camera localization results as XY labels
        cam_file: camera file folder name with date and time that contains the cam_list file
        pcap_now: csi pcap file to be sycned
        pcap_all: all pcap files in the folder

    Returns: 1) time stamp difference between server and client
    2) matched camera and csi time stamps on server

    note that we have three time stamps to synch: csi recorded on server (pcap)
    csi on client (csi), camera time stamp on server (cam)
    """

    # csiread params
    bandwidth = 20
    chiptype = "43455c0"
    pcap_num = len(pcap_all)

    cam_ts = []
    with open(cam_list, 'r') as cam_reader:
        for line in cam_reader:
            cam_ts.append(int(line[0:13]))

    # convert linux epoch time to date time
    pcap_now_linuxtime = int(pcap_now[-18:-5])
    pcap_now_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pcap_now_linuxtime/1000.))
    print("date time:", pcap_now_datetime)

    # see if camera and csi file dates match or not
    if pcap_now_datetime[0:4] != cam_file[0:4] or pcap_now_datetime[5:7] != cam_file[5:7] or \
        pcap_now_datetime[8:10] != cam_file[8:10]:
        sys.exit("file dates do not match")

    # use csiread to find time stamp on client computer
    csidata = csiread.Nexmon(pcap_now, chip=chiptype, bw=bandwidth)
    csidata.read()

    # TO verify: csidata.sec + .usec = time stamp
    csi_client_ts = csidata.sec[0]*1000 + csidata.usec[0]
    print(csidata.sec, 'sec')
    print(csi_client_ts, 'mili-sec')

    # calculate delta time
    csi_ts_diff = int(pcap_now_linuxtime) - csi_client_ts

    print("time stamp difference between client and server"
          "i.e., raspbery Pi vs. workstation")
    print(csi_ts_diff, 'mili-sec')
    print(csi_ts_diff/1000./3600., 'hour')
    print("--------------------------")

    # sync between pcap and cam ts
    pcap_now_idx = pcap_all.index(pcap_now)
    pcap_now_ts = int(pcap_now[-18:-5])
    print(pcap_now_ts)

    # boundary condition processing
    if pcap_now_idx < pcap_num-1:
        pcap_next = pcap_all[pcap_now_idx+1]
        pcap_next_ts = int(pcap_next[-18:-5])
        print(pcap_next_ts)
    else:
        pcap_next_ts = pcap_now_ts + 10.*60.*1000.  # assume 10 minutes

    cam_ts = np.array(cam_ts)
    cam_pcap_ts_msk = (cam_ts>pcap_now_ts)*(cam_ts<pcap_next_ts)
    cam_pcap_ts_idx = np.where(cam_pcap_ts_msk)

    cam_pcap_ts = cam_ts[cam_pcap_ts_idx]
    print(cam_pcap_ts)

    return csi_ts_diff, cam_pcap_ts


if __name__ == '__main__':
    main()
