# batch processing of CSI and computer vision data
import glob
import os
import numpy as np
import csiread
import time

# csiread params
bandwidth = 20
chiptype = '43455c0'

wifi_dir = "/media/cooldev5/data/ReID/forge/wifi_csi/"
cam_dir = "/media/cooldev5/data/ReID/forge/east_entrance_cam/2021.06.10.23.26.44/"

# three ts to synch: csi recorded on server (pcap)
# csi on client (csi), camera time stamp on server (cam)
pcap_all = glob.glob(wifi_dir + "*.pcap")
pcap_all.sort(key=os.path.getmtime)

cam_list = cam_dir + "list.txt"
cam_ts = []
with open(cam_list, 'r') as cam_reader:
    for line in cam_reader:
        cam_ts.append(int(line[0:13]))

#print(cam_ts)
pcap_now = wifi_dir + "1623382164609.pcap"
pcap_now = wifi_dir + "1623382256765.pcap"
# convert linux epoch time to date time
pcap_now_linuxtime = int(pcap_now[-18:-5])
pcap_now_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pcap_now_linuxtime/1000.))
print("date time:", pcap_now_datetime)

# use csiread to find time stamp on client computer
csidata = csiread.Nexmon(pcap_now, chip=chiptype, bw=bandwidth)
csidata.read()
# TO verify: csidata.sec + .usec = time stamp 
csi_client_ts = csidata.sec[0]*1000 + csidata.usec[0]
print(csidata.sec, 'sec')
print(csi_client_ts, 'mili-sec')

# calculate delta time
csi_ts_diff = int(pcap_now_linuxtime) - csi_client_ts

print("time stamp difference between client and server, i.e., raspbery Pi vs. workstation")
print(csi_ts_diff, 'mili-sec')
print(csi_ts_diff/1000./3600., 'hour')
print("--------------------------")

# synch between pcap and cam ts
pcap_now_idx = pcap_all.index(pcap_now)
pcap_next = pcap_all[pcap_now_idx+1]

pcap_now_ts = int(pcap_now[-18:-5])
print(pcap_now_ts)

pcap_next_ts = int(pcap_next[-18:-5])
print(pcap_next_ts)

cam_ts = np.array(cam_ts)
cam_pcap_ts_msk = (cam_ts>pcap_now_ts)*(cam_ts<pcap_next_ts)
cam_pcap_ts_idx = np.where(cam_pcap_ts_msk)

cam_pcap_ts = cam_ts[cam_pcap_ts_idx]
#cam_pcap_ts = cam_ts[list(cam_pcap_ts_idx)]
print(cam_pcap_ts)

