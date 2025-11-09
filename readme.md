##  1 DMRScope Capabilities
-------------

##### Startup Window of the Program
![pic](/pic/first.png)

##### [02] Visualization of Connections between subscribers with filtering and result saving options
![pic](/pic/01.png)

##### [03] Daily Activity of communication sessions with the ability to split into periods from 1 minute to 24 hours (1440 minutes), including filtering and result saving options
![pic](/pic/02.png)

```
Total sessions: 447

00: ██░ (21)
01: █▒ (16)
02: ██░ (22)
03: █▓ (17)
04: ██▒ (26)
05: ███▒ (35)
06: ▒ (6)
07: ██▒ (25)
08: █████░ (53)
09: █▓ (19)
10: ██ (20)
11: █▓ (18)
12: █████▓ (59)
13: ▓ (8)
14: █▒ (15)
15: ███░ (33)
16: ██░ (21)
17: ▒ (5)
18: ░ (3)
19:   (0)
20:   (0)
21:   (0)
22: █▓ (19)
23: ▒ (6)

Peak hour: 12:00 (59 sessions)
Minimum activity: 18:00 (3 sessions)
Average per hour: 18.6
```

##### [04] Group Connections within a session, with filtering and result saving options
![pic](/pic/03.png)

```
2025-05-12 14:05 (Sessions: 8)
TS:1 CC1 1 ─▶ 601 (0.7s) Group Call
TS:1 CC1 1 ─▶ 601 (1.1s) Group Call
TS:1 CC1 1 ─▶ 601 (1.5s) Group Call
TS:1 CC1 1 ─▶ 601 (1.5s) Group Call
TS:1 CC1 1 ─▶ 601 (0.7s) Group Call
TS:1 CC1 1 ─▶ 601 (1.0s) Group Call
TS:1 CC1 1 ─▶ 601 (1.4s) Group Call
TS:1 CC1 1 ─▶ 601 (1.5s) Group Call

2025-05-12 14:15 (Sessions: 10)
TS:1 CC1 1 ─▶ 601 (32.7s) Group Call
TS:1 CC1 1 ─▶ 601 (0.7s) Group Call
TS:1 CC1 1 ─▶ 601 (1.1s) Group Call
TS:1 CC1 1 ─▶ 601 (1.2s) Group Call
TS:1 CC1 1 ─▶ 601 (0.7s) Group Call
TS:1 CC1 1 ─▶ 601 (1.1s) Group Call
TS:1 CC1 1 ─▶ 601 (1.2s) Group Call
TS:1 CC1 1 ─▶ 601 (0.7s) Group Call
TS:1 CC1 1 ─▶ 601 (1.1s) Group Call
TS:1 CC1 1 ─▶ 601 (1.2s) Group Call
```

## Video Guide

##### DMRSCOPE Guide EN

[![DMRSCOPE Guide EN](https://img.youtube.com/vi/qTi-HwmALXE/0.jpg)](https://www.youtube.com/watch?v=qTi-HwmALXE)

##### DMRSCOPE Guide UKR 

[![DMRSCOPE Guide UKR](https://img.youtube.com/vi/pfoGPluMHyQ/0.jpg)](https://www.youtube.com/watch?v=pfoGPluMHyQ)

## 2 Install Sdrtrunk Windows/Linux
Go to website https://github.com/Dsheirer/sdrtrunk/releases
Windows version work satble 

![pic](/pic/sdrtrunk.png)

## 3 DMRScope Install

```
Install Windows [run PowerShall]
--------------

https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe

.\python-3.12.3-amd64.exe /passive InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_tcltk=1

.\python -m pip install --upgrade pip

.\pip install -r requirements.txt

```

## 4 Run program

```
.\python .\run.py
or
.\run_windows.bat
```

![pic](/pic/settings.png)

Gape time [0-60] sec
Default is 0 second
This parameter affects the data synchronization. SDRTrunk does not always write data to both files simultaneously; therefore, to find the [TO] parameter, you need to set this value (in seconds) higher if you want higher data quality. I usually set it to 3 seconds.
WARNING: The higher this value, the longer the conversion process will take.

![pic](/pic/gap_1.png)

![pic](/pic/gap_2.png)

## 5 DATA
test data

Test raw data from SDRTrunk from folder
[data_raw]

Convert data to folder
[data]

Output file format

```
"TIMESTAMP","DURATION_MS","PROTOCOL","EVENT","FROM","TO","TIMESLOT","COLOR_CODE","ALGORITHM","KEY","DETAILS"

"2025:05:12:10:01:23","","DMR","Group Call","1","602","TS:1","1","","","SERVICE OPTIONS []"
"2025:05:12:10:01:23","58","DMR","Group Call","1","602","TS:1","1","","","SERVICE OPTIONS []"

"2025:05:13:18:04:22","3100","DMR","Encrypted Group Call","","","TS:1","6","RC4/EP","22","ENCRYPTED"
"2025:05:13:18:05:04","4011","DMR","Encrypted Group Call","1001","","TS:1","6","RC4/EP","22","ENCRYPTED"
```

## 5 Struture files

Python code
```
run.py  
_00_0_convert.py  
_00_3_convert.py  
_01_visualization.py  
_02_graphics.py  
_03_group_connections.py  
_04_help.py  
```

```
config.ini  - config file
```

```
requirements.txt  - Python library
_python_install.txt - files for install Windows wersion
```

run programm 
```
.\python .\run.py

_run_linux.sh        - not tested
_install_linux.sh    - not tested

_run_windows.bat
_install_windows.bat - not tested
```


