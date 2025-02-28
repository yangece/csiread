"""A fast channel state information parser for Intel, Atheros and Nexmon."""

from . import _csiread


class Intel(_csiread.Intel):
    """Parse CSI obtained using 'Linux 802.11n CSI Tool'.

    Args:
        file (str or None): CSI data file. If ``str``, ``read`` and ``readstp``
            methods are allowed. If ``None``, ``seek`` and ``pmsg`` methods are
            allowed.
        nrxnum (int, optional): Number of receive antennas. Default: 3
        ntxnum (int, optional): Number of transmit antennas. Default: 2
        pl_size (int, optional): The size of payload to be used. Default: 0
        if_report (bool, optional): Report the parsed result. Default: ``True``
        bufsize (int, optional): The maximum amount of packets to be parsed.
            If ``0`` and file is ``str``, all packets will be parsed. If ``0``
            and file is ``None``, this parameter is ignored by `pmsg` method.
            Default: 0

    Attributes:
        file (str, readonly): CSI data file
        count (int, readonly): Count of 0xbb packets parsed
        timestamp_low (ndarray): The low 32 bits of the NIC's 1 MHz clock. It
            wraps about every 4300 seconds, or 72 minutes.
        bfee_count (ndarray): The count of the total number of beamforming
            measurements that have been recorded by the driver and sent to
            userspace. The netlink channel between the kernel and userspace is
            lossy, so these can be used to detect measurements that were
            dropped in this pipe.
        Nrx (ndarray): The number of antennas used to receive the packet.
        Ntx (ndarray): The number of space/time streams transmitted.
        rssi_a (ndarray): RSSI measured by the receiving NIC at the input to
            antenna port A. This measurement is made during the packet preamble.
            This value is in dB relative to an internal reference.
        rssi_b (ndarray): See ``rssi_a``
        rssi_c (ndarray): See ``rssi_a``
        noise (ndarray): Noise
        agc (ndarray): Automatic Gain Control (AGC) setting in dB
        perm (ndarray): Tell us how the NIC permuted the signals from the 3
            receive antennas into the 3 RF chains that process the measurements.
        rate (ndarray): The rate at which the packet was sent, in the same
            format as the ``rate_n_flags``.
        csi (ndarray): The CSI itself, normalized to an internal reference.
            It is a Count×30×Nrx×Ntx 4-D matrix where the second dimension is
            across 30 subcarriers in the OFDM channel. For a 20 MHz-wide
            channel, these correspond to about half the OFDM subcarriers, and
            for a 40 MHz-wide channel, this is about one in every 4 subcarriers.
        stp (ndarray): World timestamp recorded by the modified ``log_to_file``.
        fc (ndarray): Frame control
        dur (ndarray): Duration
        addr_des (ndarray): Destination MAC address
        addr_src (ndarray): Source MAC address
        addr_bssid (ndarray): BSSID MAC address
        seq (ndarray): Serial number of packet
        payload (ndarray): MAC frame to be used

    Examples:

        >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
        >>> csidata = csiread.Intel(csifile, nrxnum=3, ntxnum=2, pl_size=10)
        >>> csidata.read()
        >>> csi = csidata.get_scaled_csi()
        >>> print(csidata.csi.shape)

    References:
        1. `Linux 802.11n CSI Tool <https://dhalperi.github.io/linux-80211n-csitool/>`_
        2. `linux-80211n-csitool-supplementary <https://github.com/dhalperi/linux-80211n-csitool-supplementary>`_
        3. `Linux 802.11n CSI Tool-FAQ <https://dhalperi.github.io/linux-80211n-csitool/faq.html>`_
    """

    def __init__(self, file, nrxnum=3, ntxnum=2, pl_size=0, if_report=True,
                 bufsize=0):
        super(Intel, self).__init__(file, nrxnum, ntxnum, pl_size, if_report,
                                    bufsize)

    def __getitem__(self, index):
        ret = {
            "timestamp_low": self.timestamp_low[index],
            "bfee_count": self.bfee_count[index],
            "Nrx": self.Nrx[index],
            "Ntx": self.Ntx[index],
            "rssi_a": self.rssi_a[index],
            "rssi_b": self.rssi_b[index],
            "rssi_c": self.rssi_c[index],
            "noise": self.noise[index],
            "agc": self.agc[index],
            "perm": self.perm[index],
            "rate": self.rate[index],
            "csi": self.csi[index]
        }
        return ret

    def read(self):
        """Parse data if 0xbb and 0xc1 packets

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> csidata.read()
        """
        super().read()

    def seek(self, file, pos, num):
        """Read packets from a specific position

        This method allows us to read different parts of different files
        randomly. It could be useful in Machine Learning. However, it could be
        very slow when reading files in HDD for the first time. For this case,
        it is better to do a pre-read with ``read()`` first.

        Args:
            file (str): CSI data file.
            pos (int): Position of file descriptor corresponding to the packet.
                Currently, it must be returned by the function in
                ``example/csiseek.py``.
            num (int): Number of packets to be read. ``num <= bufsize`` must be
                true. If ``0``, all packets after ``pos`` will be read.

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(None, bufsize=16)
            >>> for i in range(10):
            >>>     csidata.seek(csifile, 0, i+1)
            >>>     print(csidata.csi.shape)
        """
        super().seek(file, pos, num)

    def pmsg(self, data):
        """Parse message in real time

        Args:
            data (bytes): A bytes object representing the data received by udp
                socket
        Returns:
            int: The status code. If ``0xbb`` and ``0xc1``, parse message
                successfully. Otherwise, the ``data`` is not a CSI packet.

        Examples:

            >>> import socket
            >>> import csiread
            >>>
            >>> csidata = csiread.Intel(None)
            >>> with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            >>>     s.bind(('127.0.0.1', 10011))
            >>>     while True:
            >>>         data, address_src = s.recvfrom(4096)
            >>>         code = csidata.pmsg(data)
            >>>         if code == 0xbb:
            >>>             print(csidata.csi.shape)
        """
        return super().pmsg(data)

    def readstp(self, endian='little'):
        """Parse timestamp recorded by the modified ``log_to_file``

        ``file.dat`` and ``file.datstp`` must be in the same directory.

        Args:
            endian (str): The byte order of ``file.datstp``， it can be
                ``little`` and ``big``. Default: ``little``

        Returns:
            int: Timestamp of the first packet.

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> first_stp = csidata.readstp()
            >>> print(first_stp)
        """
        return super().readstp(endian)

    def get_total_rss(self):
        """Calculate the Received Signal Strength[RSS] in dBm from CSI

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> csidata.read()
            >>> rssi = csidata.get_total_rss()
            >>> print(rssi.shape)
        """
        return super().get_total_rss()

    def get_scaled_csi(self, inplace=False):
        """Convert CSI to channel matrix H

        Args:
            inplace (bool): Optionally do the operation in-place. Default: False

        Returns:
            ndarray: Channel matrix H

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> csidata.read()
            >>> scaled_csi = csidata.get_scaled_csi(False)
            >>> print(scaled_csi.shape)
            >>> print("scaled_csi is csidata.csi: ", scaled_csi is csidata.csi)
        """
        return super().get_scaled_csi(inplace)

    def get_scaled_csi_sm(self, inplace=False):
        """Convert CSI to pure channel matrix H

        This version undoes Intel's spatial mapping to return the pure MIMO
        channel matrix H.

        Args:
            inplace (bool): Optionally do the operation in-place. Default: False

        Returns:
            ndarray: The pure MIMO channel matrix H.

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> csidata.read()
            >>> scaled_csi_sm = csidata.get_scaled_csi_sm(False)
            >>> print(scaled_csi.shape)
            >>> print("scaled_csi_sm is csidata.csi: ", scaled_csi_sm is csidata.csi)
        """
        return super().get_scaled_csi_sm(inplace)

    def apply_sm(self, scaled_csi):
        """Undo the input spatial mapping

        Args:
            scaled_csi (ndarray): Channel matrix H.

        Returns:
            ndarray: The pure MIMO channel matrix H.

        Examples:

            >>> csifile = "../material/5300/dataset/sample_0x1_ap.dat"
            >>> csidata = csiread.Intel(csifile)
            >>> csidata.read()
            >>> scaled_csi = csidata.get_scaled_csi()
            >>> scaled_csi_sm = csidata.apply_sm(scaled_csi)
            >>> print(scaled_csi_sm.shape)
        """
        return super().apply_sm(scaled_csi)


class Atheros(_csiread.Atheros):
    """Parse CSI obtained using 'Atheros CSI Tool'.

    Args:
        file (str or None): CSI data file. If ``str``, ``read`` and ``readstp``
            methods are allowed. If ``None``, ``seek`` and ``pmsg`` methods are
            allowed.
        nrxnum (int, optional): Number of receive antennas. Default: 3
        ntxnum (int, optional): Number of transmit antennas. Default: 2
        pl_size (int, optional): The size of payload to be used. Default: 0
        tones (int, optional): The number of subcarrier. It can be 56 and 114.
            Default: 56
        if_report (bool, optional): Report the parsed result. Default: ``True``
        bufsize (int, optional): The maximum amount of packets to be parsed.
            If ``0`` and file is ``str``, all packets will be parsed. If ``0``
            and file is ``None``, this parameter is ignored by ``pmsg`` method.
            Default: 0

    Attributes:
        file (str, readonly): CSI data file
        count (int, readonly): Count of CSI packets parsed
        timestamp (ndarray): The time when packet is received, expressed in μs
        csi_len (ndarray): The csi data length in the received data buffer,
            expressed in bytes
        tx_channel (ndarray): The center frequency of the wireless channel,
            expressed in MHz
        err_info (ndarray): The phy error code, set to 0 if correctly received
        noise_floor (ndarray): The noise floor, expressed in dB. But it needs
            to be update and is set to 0 in current version.
        Rate (ndarray): The data rate of the received packet. Its value is a
            unsigned 8 bit integer number and the mapping between this value
            and the rate choice of 802.11 protocol
        bandWidth (ndarray): The channel bandwidth. It is 20MHz if set to 0 and
            40MHz if set to 1
        num_tones (ndarray): The number of subcarrier that used for data
            transmission.
        nr (ndarray): Number of receiving antenna
        nc (ndarray): Number of transmitting antenna
        rsssi (ndarray): The rssi of combination of all active chains
        rssi_1 (ndarray): The rssi of active chain 0
        rssi_2 (ndarray): The rssi of active chain 1
        rssi_3 (ndarray): The rssi of active chain 2
        payload_len (ndarray): The payload length of received packet, expressed
            in bytes.
        csi (ndarray): CSI
        payload (ndarray): MAC frame(MPDU) to be used

    Examples:

        >>> csifile = "../material/atheros/dataset/ath_csi_1.dat"
        >>> csidata = csiread.Atheros(csifile, nrxnum=3, ntxnum=2, pl_size=10, tones=56)
        >>> csidata.read(endian='little')
        >>> print(csidata.csi.shape)

    References:
        1. `Atheros CSI Tool <https://wands.sg/research/wifi/AtherosCSI/>`_
        2. `Atheros-CSI-Tool-UserSpace-APP <https://github.com/xieyaxiongfly/Atheros-CSI-Tool-UserSpace-APP>`_
        3. `Atheros CSI Tool User Guide <https://wands.sg/research/wifi/AtherosCSI/document/Atheros-CSI-Tool-User-Guide.pdf>`_
    """

    def __init__(self, file, nrxnum=3, ntxnum=2, pl_size=0, tones=56,
                 if_report=True, bufsize=0):
        super(Atheros, self).__init__(file, nrxnum, ntxnum, pl_size, tones,
                                      if_report, bufsize)

    def __getitem__(self, index):
        ret = {
            "timestamp": self.timestamp[index],
            "csi_len": self.csi_len[index],
            "tx_channel": self.tx_channel[index],
            "err_info": self.err_info[index],
            "noise_floor": self.noise_floor[index],
            "Rate": self.Rate[index],
            "bandWidth": self.bandWidth[index],
            "num_tones": self.num_tones[index],
            "nr": self.nr[index],
            "nc": self.nc[index],
            "rssi": self.rssi[index],
            "rssi_1": self.rssi_1[index],
            "rssi_2": self.rssi_2[index],
            "rssi_3": self.rssi_3[index],
            "payload_len": self.payload_len[index],
            "csi": self.csi[index],
            "payload": self.payload[index]
        }
        return ret

    def read(self, endian='little'):
        """Parse data

        Args:
            endian (str): The byte order of ``file.dat``， it can be ``little``
                and ``big``. Default: ``little``

        Examples:

            >>> csifile = "../material/atheros/dataset/ath_csi_1.dat"
            >>> csidata = csiread.Atheros(csifile)
            >>> csidata.read()
        """
        super().read(endian)

    def seek(self, file, pos, num, endian='little'):
        """Read packets from a specific position

        This method allows us to read different parts of different files
        randomly. It could be useful in Machine Learning. However, it could be
        very slow when reading files in HDD for the first time. For this case,
        it is better to do a pre-read with ``read()`` first.

        Args:
            file (str): CSI data file.
            pos (int): Position of file descriptor corresponding to the packet.
                Currently, it must be returned by the function in
                `example/csiseek.py`.
            num (int): Number of packets to be read. ``num <= bufsize`` must be
                true. If ``0``, all packets after ``pos`` will be read.
            endian (str): The byte order of ``file.dat``， it can be ``little``
                and ``big``. Default: ``little``

        Examples:

            >>> csifile = "../material/atheros/dataset/ath_csi_1.dat"
            >>> csidata = csiread.Atheros(None, bufsize=16)
            >>> for i in range(10):
            >>>     csidata.seek(csifile, 0, i+1)
            >>>     print(csidata.csi.shape)
        """
        super().seek(file, pos, num, endian)

    def pmsg(self, data, endian='little'):
        """Parse message in real time

        Args:
            data (bytes): A bytes object representing the data received by udp
                socket
            endian (str): The byte order of ``file.dat``， it can be ``little``
                and ``big``. Default: ``little``

        Returns:
            int: The status code. If ``0xff00``, parse message successfully.
                Otherwise, the ``data`` is not a CSI packet.

        Examples:

            >>> import socket
            >>> import csiread
            >>>
            >>> csidata = csiread.Atheros(None)
            >>> with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            >>>     s.bind(('127.0.0.1', 10011))
            >>>     while True:
            >>>         data, address_src = s.recvfrom(4096)
            >>>         code = csidata.pmsg(data)
            >>>         if code == 0xff00:
            >>>             print(csidata.csi.shape)
        """
        return super().pmsg(data, endian)

    def readstp(self, endian='little'):
        """Parse timestamp recorded by the modified ``recv_csi``

        ``file.dat`` and ``file.datstp`` must be in the same directory.

        Args:
            endian (str): The byte order of ``file.datstp``， it can be
                ``little`` and ``big``. Default: ``little``

        Examples:

            >>> csifile = "../material/atheros/dataset/ath_csi_1.dat"
            >>> csidata = csiread.Atheros(csifile)
            >>> first_stp = csidata.readstp()
            >>> print(first_stp)
        """
        return super().readstp(endian)


class Nexmon(_csiread.Nexmon):
    """Parse CSI obtained using 'nexmon_csi'.

    Args:
        file (str or None): CSI data file ``.pcap``. If ``str``, ``read``
            methods is allowed. If ``None``, ``seek`` and ``pmsg`` methods are
            allowed.
        chip (str): WiFi Chip, it can be '4339', '43455c0', '4358' and '4366c0'.
        bw (int): bandwidth, it can be 20, 40 and 80.
        if_report (bool, optional): Report the parsed result. Default: `True`
        bufsize (int, optional): The maximum amount of packets to be parsed. If
            ``0`` and file is ``str``, all packets will be parsed. If ``0`` and
            file is ``None``, this parameter is ignored by `pmsg` method.
            Default: 0

    Attributes:
        file (str, readonly): CSI data file
        count (int, readonly): Count of csi packets parsed
        chip (str, readonly): Chip type we set
        bw (int, readonly): Bandwidth we set
        nano (bool, readonly): nanosecond-resolution or not
        sec (ndarray): Time the packet was captured
        usec (ndarray): The microseconds when this packet was captured, as an
            offset to ``sec`` if ``nano`` is True. The nanoseconds when the
            packet was captured, as an offset to ``sec`` if ``nano`` is False.
        caplen (ndarray): The number of bytes of packet data actually captured
            and saved in the file
        wirelen (ndarray): The length of the packet as it appeared on the
            network when it was captured
        magic (ndarray): Four magic bytes ``0x11111111``
        src_addr (ndarray): Source MAC address
        seq (ndarray): Sequence number of the Wi-Fi frame that triggered the
            collection of the CSI contained in packets
        core (ndarray): Core
        spatial (ndarray): Spatial stream
        chan_spec (ndarray): (unknown)
        chip_version (ndarray): The chip version
        csi (ndarray): CSI

    Examples:

        >>> csifile = "../material/nexmon/dataset/example.pcap"
        >>> csidata = csiread.Nexmon(csifile, chip='4358', bw=80)
        >>> csidata.read()
        >>> print(csidata.csi.shape)

    References:
        1. `nexmon_csi <https://github.com/seemoo-lab/nexmon_csi>`_
        2. `rdpcap <https://github.com/secdev/scapy/blob/master/scapy/utils.py>`_
        3. `Libpcap File Format <https://wiki.wireshark.org/Development/LibpcapFileFormat>`_
    """
    def __init__(self, file, chip, bw, if_report=True, bufsize=0):
        super(Nexmon, self).__init__(file, chip, bw, if_report, bufsize)

    def __getitem__(self, index):
        ret = {
            "magic": self.magic[index],
            "src_addr": self.src_addr[index],
            "seq": self.seq[index],
            "core": self.core[index],
            "spatial": self.spatial[index],
            "chan_spec": self.chan_spec[index],
            "chip_version": self.chip_version[index],
            "csi": self.csi[index]
        }
        return ret

    def read(self):
        """Parse data

        Examples:

            >>> csifile = "../material/nexmon/dataset/example.pcap"
            >>> csidata = csiread.Nexmon(csifile, chip='4358', bw=80)
            >>> csidata.read()
            >>> print(csidata.csi.shape)
        """
        super().read()

    def seek(self, file, pos, num):
        """Read packets from specific position

        This method allows us to read different parts of different files
        randomly. It could be useful in Machine Learning. However, it could be
        very slow when reading files in HDD for the first time. For this case,
        it is better to use `read()` for a pre-read first.

        Args:
            file (str): CSI data file ``.pcap``.
            pos (int): Position of file descriptor corresponding to the packet.
                Currently, it must be returned by the function in 
                ``example/csiseek.py``.
            num (int): Number of packets to be read. ``num <= bufsize`` must be
                true. If ``0``, all packets after ``pos`` will be read.

        Examples:

            >>> csifile = "../material/nexmon/dataset/example.pcap"
            >>> csidata = csiread.Nexmon(None, chip='4358', bw=80, bufsize=4)
            >>> for i in range(4):
            >>>     csidata.seek(csifile, 0, i+1)
            >>>     print(csidata.csi.shape)
        """
        super().seek(file, pos, num)

    def pmsg(self, data, endian='little'):
        """Parse message in real time

        Args:
            data (bytes): A bytes object representing the data received by raw
                socket
            endian (str): The byte order of ``file.dat``， it can be ``little``
                and ``big``. Default: ``little``

        Returns:
            int: The status code. If ``0xf100``, parse message successfully.
                Otherwise, the ``data`` is not a CSI packet.

        Examples:

            >>> import socket
            >>> import csiread
            >>> 
            >>> csidata = csiread.Nexmon(None, chip='4358', bw=80)
            >>> with socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x3)) as s:
            >>>     while True:
            >>>         data, address_src = s.recvfrom(4096)
            >>>         code = csidata.pmsg(data)
            >>>         if code == 0xf100:
            >>>             print(csidata.csi.shape)
        """
        return super().pmsg(data, endian)


class AtherosPull10(Atheros):
    """Parse CSI obtained using 'Atheros CSI Tool' pull 10.

    The same as Atheros

    References:
        1. `Atheros-CSI-Tool-UserSpace-APP pull 10 <https://github.com/xieyaxiongfly/Atheros-CSI-Tool-UserSpace-APP/pull/10>`_
    """
    def read(self):
        """Parse data

        Examples:

            >>> csifile = "../material/atheros/dataset/ath_csi_1.dat"
            >>> csidata = csiread.Atheros(csifile)
            >>> csidata.read()
        """
        with open(self.file, 'rb') as f:
            endian = 'big' if f.read(1) == b'\xff' else 'little'
        self.seek(self.file, 1, 0, endian)


class NexmonPull46(Nexmon):
    """Parse CSI obtained using 'nexmon_csi' pull 46.

    Args:
        See ``Nexmon``

    Attributes:
        rssi (ndarray): rssi
        fc (ndarray): frame control
        others: see ``Nexmon``

    References:
        1. `nexmon_csi pull 46 <https://github.com/seemoo-lab/nexmon_csi/pull/46>`_
    """
    def __init__(self, file, chip, bw, if_report=True, bufsize=0):
        super(NexmonPull46, self).__init__(file, chip, bw, if_report, bufsize)
        self.rssi = None
        self.fc = None
        self._autoscale = 0

    def __getitem__(self, index):
        ret = super().__getitem__(index)
        ret['rssi'] = self.rssi[index]
        ret['fc'] = self.fc[index]
        return ret

    def seek(self, file, pos, num):
        """Read packets from specific position, see ``Nexmon.seek``"""
        super().seek(file, pos, num)
        self.__pull46()

    def pmsg(self, data, endian='little'):
        """Parse message in real time

        Args:
            data (bytes): A bytes object representing the data received by raw
                socket
            endian (str): The byte order of ``file.dat``， it can be ``little``
                and ``big``. Default: ``little``

        Returns:
            int: The status code. If ``0xf101``, parse message successfully.
                Otherwise, the ``data`` is not a CSI packet.
        """
        super().pmsg(data, endian)
        self.__pull46()
        return 0xf101

    def __pull46(self):
        if self.magic[0] & 0x0000ffff == 0x1111:
            self.rssi = ((self.magic & 0x00ff0000) >> 16)
            self.rssi = self.rssi.astype('i1').astype(int)
            self.fc = (self.magic & 0xff000000) >> 24
            self.magic &= 0x0000ffff
        else:
            self.rssi = ((self.magic & 0x0000ff00) >> 8)
            self.rssi = self.rssi.astype('i1').astype(int)
            self.fc = self.magic & 0x000000ff
            self.magic = (self.magic & 0xffff0000) >> 16
