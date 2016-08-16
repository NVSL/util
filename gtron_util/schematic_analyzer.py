#!/usr/bin/env python

import argparse
import glob
import Swoop
import collections
from joblib import Parallel, delayed
import multiprocessing


def get_connections_per_device(swoop_sch):
    for part in swoop_sch.get_parts():
        part._xx_con_count = 0

    for sheet in swoop_sch.get_sheets():
        for net in sheet.get_nets():
            for segment in net.get_segments():
                for pinref in segment.get_pinrefs():
                    swoop_sch.get_part(pinref.get_part())._xx_con_count += 1

    connections_per_device = collections.defaultdict(list)
    for part in swoop_sch.get_parts():
        device = part.get_deviceset()
        # print "Part: {0}    Connections: {1}    Device: {2}"\
        #     .format(part.get_name(), part._xx_con_count, device)
        connections_per_device[device].append(part._xx_con_count)

    return connections_per_device

def schematic_stats(filename, part_limit, conn_limit, dup_limit):
    try:
        sch = Swoop.from_file(filename)[0]
    except:
        return None

    if len(sch.get_parts()) < part_limit:
        return None

    cpd = get_connections_per_device(sch)
    # print cpd

    # Number of times a device with over conn_limit connections was instantiated
    # There will be a count for each (important part)
    duplicate_instantiate_count = []
    for device in cpd.keys():
        # Does the usage of this device have enough connections?
        filter_enough_connections = filter(lambda d: d >= conn_limit, cpd[device])

        # Number of "actual" duplicates with enough connections
        dupes = len(filter_enough_connections)
        if dupes >= dup_limit:
            duplicate_instantiate_count.append((device,dupes))
    return duplicate_instantiate_count


parser = argparse.ArgumentParser(description="Analyze a directory full of Eagle schematics")
parser.add_argument("dir")
parser.add_argument("-p","--part-limit", default=5, type=int,
                    help="Limit schematics to at least this many parts")
parser.add_argument("-c","--connection-limit", default=3, type=int,
                    help="Only count devices with at least this many connections")
parser.add_argument("-d","--dup-limit", default=2, type=int,
                    help="Devices must be instantiated at least this many times to be considered a duplicate")
args = parser.parse_args()

schematics = glob.glob("{0}/*.sch".format(args.dir))

conn_limit = args.connection_limit
part_limit = args.part_limit
# print "Number of times a part with over 3 connections was instantiated on a schematic"

cores = multiprocessing.cpu_count()
results =   Parallel(n_jobs=cores)(
                delayed(schematic_stats)(filename, part_limit, conn_limit, args.dup_limit) for filename in schematics
            )
# print results

TOTAL = 0
HAS_DUPES = 0

# These are only among schematics with duplicates
DUPED_PART_COUNT = 0    # Number of devices duplicated
TOTAL_PART_DUPES = 0    # Sum of how many times each device duplicated
#

# Only schematics that loaded properly and met the part limit
results = filter(lambda x: x is not None, results)

TOTAL = len(results)

# Schematics with at least 1 device
results = filter(lambda x: len(x) > 0, results)

print results

all_devices = collections.defaultdict(int)

for duped_devices in results:
    if len(duped_devices) > 0:
        HAS_DUPES += 1
    DUPED_PART_COUNT += len(duped_devices)
    for device, duplicate_instantiate_count in duped_devices:
        all_devices[device] += 1
        TOTAL_PART_DUPES += duplicate_instantiate_count


devices_sorted = sorted(all_devices.items(), key=lambda x: x[1])
# print devices_sorted
for d in reversed(devices_sorted):
    print d


print "Total schematics with more that {0} parts: {1}".format(part_limit, TOTAL)
print "Amount that have duplicates over {0} connections each: {1}".format(conn_limit, HAS_DUPES)
print "Percent with duplicates: {0}%".format((HAS_DUPES / float(TOTAL))*100)
if DUPED_PART_COUNT > 0:
    print "For schematics with duplicates, average number of times a device" \
          " with at least {0} connections was instantiated: {1}"\
        .format(conn_limit, TOTAL_PART_DUPES / float(DUPED_PART_COUNT))


