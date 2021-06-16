FROM python:3.6

ADD main.py .

RUN pip install numpy
RUN pip install csiread
RUN mkdir ./2021.06.10.23.26.44
ADD list.txt ./2021.06.10.23.26.44
ADD 1623382164609.pcap 1623382256765.pcap ./

CMD ["python3", "main.py"]

