'''
    Project Name: GQRX Scanner
    File name: gqrx_scanner.py
    Author: Adolfo Garza
    Date created: 05/24/2019
    Python Version: 3.6
    Description: Script that allows GQRX users to automatically scan custom
    frequency ranges by remote controlling the GQRX client's RTL-SDR hardware.
    Available Modes: ['OFF', 'RAW', 'AM', 'FM', 'WFM', 'WFM_ST', 'LSB', 'USB',
    'CW', 'CWL', 'CWU']
'''
from telnetlib import Telnet
from time import sleep


class Scanner:
    def __init__(self,
                 hostname='127.0.0.1',
                 port=7356,
                 squelch=-20):
        self.host = hostname
        self.port = port
        self.squelch = squelch

    def __request(self, message):
        try:
            telnet = Telnet(self.host, self.port)
        except Exception as error:
            print(f'Encountered: {error}')
        telnet.write(('%s\n' % message).encode('ascii'))
        response = telnet.read_some().decode('ascii').strip()
        telnet.write('c\n'.encode('ascii'))
        return response

    def set_frequency(self, frequency):
        return self.__request('F %s' % frequency)

    def get_frequency(self):
        return self.__request('f')

    def set_mode(self, mode):
        return self.__request('M %s' % mode)

    def get_mode(self):
        return self.__request('m')

    def get_level(self):
        return self.__request('l')

    def set_squelch(self, squelch):
        return self.__request('L SQL %s' % squelch)

    def scan(self, min_frequency, max_frequency, mode, step=50000):
        min_frequency = int((str(float(min_frequency) * 1e5)).replace('.', ''))
        max_frequency = int((str(float(max_frequency) * 1e5)).replace('.', ''))
        current_frequency = min_frequency
        self.set_mode(mode)

        while True:
            if current_frequency > max_frequency:
                current_frequency = min_frequency

            self.set_frequency(current_frequency)
            self.set_squelch(self.squelch)
            sleep(0.5)

            if float(self.get_level()) >= self.squelch:
                print(f'Found: {current_frequency}')
                sleep(3)
            current_frequency += step

    def peak_scan(self, min_frequency, max_frequency, mode, step=50000):
        """Peak scanning: When encountered with a strong enough signal,
        it seeks until it finds the point of maximum strength, it helps to
        avoid providing duplicated signal sources.
        """
        min_frequency = int((str(float(min_frequency) * 1e5)).replace('.', ''))
        max_frequency = int((str(float(max_frequency) * 1e5)).replace('.', ''))
        current_frequency = min_frequency
        self.set_mode(mode)

        while True:
            if current_frequency > max_frequency:
                current_frequency = min_frequency

            peak_frequency = current_frequency
            current_squelch = self.squelch
            custom_step = step
            self.set_frequency(current_frequency)
            self.set_squelch(self.squelch)
            sleep(0.5)

            # Fine tunning: increases the squelch steadily to
            # find the clearest frequency for the source.
            while float(self.get_level()) >= current_squelch:
                peak_frequency = current_frequency
                current_squelch += 5
                current_frequency += 10000
                self.set_frequency(current_frequency)
                self.set_squelch(current_squelch)
                sleep(0.5)

            if peak_frequency != current_frequency:
                print(f'Found: {peak_frequency}')
                custom_step += (peak_frequency - current_frequency) * 1.15
            current_frequency += custom_step


if __name__ == "__main__":
    Scanner().peak_scan(88.0, 100.0, 'WFM_ST')
