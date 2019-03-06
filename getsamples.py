#!/usr/bin/env python3
import sys

import driver.ut2000


def read_samples():
    dev = driver.ut2000.open()
    if dev is None:
        print('USB device cannot be found, check connection', file=sys.stderr)
        sys.exit(1)
    dev.attach()
    try:
        return dev.get_samples()
    finally:
        dev.detach()


def extract_samples(channels, sample_selector):
    return [i[sample_selector] for i in channels]


class SampleOutput(object):
    @staticmethod
    def plot(channels, samples):
        import matplotlib.pyplot as plt
        for channel in samples:
            plt.plot(channel)
        plt.show()

    @staticmethod
    def json(channels, samples):
        import json
        for channel in channels:
            channel['samples'] = channel['samples'].tolist()
            channel['samples_volt'] = channel['samples_volt'].tolist()
        for channel in channels:
            channel['samples'] = 0
            channel['samples_volt'] = 0
        print(json.dumps(channels, sort_keys=True, indent=4))

    @staticmethod
    def numpy(samples):
        np.array(samples).save(sys.stdout)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Read sample data from scope')
    parser.add_argument('--output', help='Define the output format',
                        choices=['plot', 'json', 'numpy'], default='plot')
    parser.add_argument('--datatype', help='What data to dump',
                        choices=['raw', 'voltage'], default='voltage')
    args = parser.parse_args()

    channels = read_samples()
    samples = extract_samples(channels,
                              dict(raw='samples',
                                   voltage='samples_volt')[args.datatype])
    getattr(SampleOutput, args.output)(channels, samples)
