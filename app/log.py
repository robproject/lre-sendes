from datetime import datetime
import sys
import csv

from labjack import ljm


def test():
    MAX_REQUESTS = 10  # The number of eStreamRead calls that will be performed.

    # Open first found LabJack
    handle = ljm.openS() 

    info = ljm.getHandleInfo(handle)
    #print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
    #      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
    #      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

    # Stream Configuration
    aScanListNames = ["AIN0", "AIN1", "AIN2", "CORE_TIMER"]  # Scan list names to stream
    numAddresses = len(aScanListNames)
    aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]
    scanRate =25000 
    scansPerRead = int(scanRate / 2)

    try:
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        # Ensure triggered stream is disabled.
        ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)

        # Enabling internally-clocked stream.
        ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN1_RANGE", "AIN2_RANGE",
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 10.0, 10.0, 0, 0]

        # Write the analog inputs' negative channels, ranges, stream settling time
        # and stream resolution configuration.
        ljm.eWriteNames(handle, len(aNames), aNames, aValues)


            ### clock sync
            # ljm.getHostTick()
            # ljm.eReadName(handle, "STREAM_START_TIME_STAMP")
            # ljm.eReadName(handle, "CORE_TIMER")
            ### goal: get timestamp of start that's correlated with core timer such that
            ### column can be added to csv containing actual datetimes associated with core timer

        # Configure and start stream
        scanRate = ljm.eStreamStart(handle, scansPerRead, numAddresses, aScanList, scanRate)
        print("\nStream started with a scan rate of %0.0f Hz." % scanRate)
        print("\nPerforming %i stream reads." % MAX_REQUESTS)
        totScans = 0
        totSkip = 0  # Total skipped samples

        # start test
        ljm.eWriteName(handle, "DAC0", 5)

        with open('test.csv', 'w', encoding='UTF8', newline='') as f:

            writer = csv.writer(f)
            # header = aScanListNames
            writer.writerow(aScanListNames)

            start = datetime.now()


            ljmScanBacklog = 0
            i = 1
            while i <= MAX_REQUESTS:

                if i == MAX_REQUESTS - 1:
                    # stop test
                    ljm.eWriteName(handle, "DAC0", 0)

                try:
                    ret = ljm.eStreamRead(handle)

                    aData = ret[0]
                    ljmScanBacklog = ret[2]
                    scans = len(aData) / numAddresses
                    totScans += scans

                    # Count the skipped samples which are indicated by -9999 values. Missed
                    # samples occur after a device's stream buffer overflows and are
                    # reported after auto-recover mode ends.
                    curSkip = aData.count(-9999.0)
                    totSkip += curSkip

                    rows = []
                    for k in range(0, len(aData), numAddresses):
                        rows.append(aData[k:k+numAddresses])

                    writer.writerows(rows)

                    print("\neStreamRead %i" % i)
                    ainStr = ""
                    for j in range(0, numAddresses):
                        ainStr += "%s = %0.5f, " % (aScanListNames[j], aData[j])
                    print("  1st scan out of %i: %s" % (scans, ainStr))
                    print("  Scans Skipped = %0.0f, Scan Backlogs: Device = %i, LJM = "
                          "%i" % (curSkip/numAddresses, ret[1], ljmScanBacklog))
                    i += 1
                except ljm.LJMError as err:
                    if err.errorCode == ljm.errorcodes.NO_SCANS_RETURNED:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        continue
                    else:
                        raise err

                end = datetime.now()

            print("\nTotal scans = %i" % (totScans))
            tt = (end - start).seconds + float((end - start).microseconds) / 1000000
            print("Time taken = %f seconds" % (tt))
            print("LJM Scan Rate = %f scans/second" % (scanRate))
            print("Timed Scan Rate = %f scans/second" % (totScans / tt))
            print("Timed Sample Rate = %f samples/second" % (totScans * numAddresses / tt))
            print("Skipped scans = %0.0f" % (totSkip / numAddresses))
    except ljm.LJMError:
        ljme = sys.exc_info()[1]
        print(ljme)
    except Exception:
        e = sys.exc_info()[1]
        print(e)

    try:
        print("\nStop Stream")
        ljm.eStreamStop(handle)
    except ljm.LJMError:
        ljme = sys.exc_info()[1]
        print(ljme)
    except Exception:
        e = sys.exc_info()[1]
        print(e)

    # Close handle
    ljm.close(handle)


test()