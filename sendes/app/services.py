from app.extensions import db, ur, console
from app.models import Constants, Ljconfig, Test, StreamRead, Scan

from sqlalchemy import select, and_, inspect

import sys, os
from datetime import datetime, timedelta
import numpy as np
from matplotlib import pyplot as plt, lines
from uncertainties import ufloat, ufloat_fromstr
from pint import Quantity
from labjack import ljm


class ConstantsService:
    @staticmethod
    def create(form):
        constants_entry = Constants()
        form.populate_obj(constants_entry)
        constants_entry.is_active = False
        try:
            db.session.add(constants_entry)
            db.session.commit()
        except db.exc.IntegrityError:
            db.session.rollback()
            constants_entry = dbService.fetch_existing(Constants, constants_entry)
        return constants_entry

    @staticmethod
    def activate(constants_id):
        new_active_constant = db.session.get(Constants, constants_id)
        if new_active_constant.is_active:
            return
        active_constant = db.session.execute(
            select(Constants).where(Constants.is_active == True)
        ).scalar_one_or_none()
        if active_constant is not None:
            active_constant.is_active = False
            db.session.add(active_constant)
        new_active_constant.is_active = True
        db.session.add(new_active_constant)
        db.session.commit()
        return

    @staticmethod
    def get_vars(c: Constants) -> tuple[Quantity, Quantity, Quantity, Quantity]:
        d = (ufloat(c.piston_avg, c.piston_uncertainty) * ur.inch).to("meter")
        d1 = (ufloat(c.pipe_avg, c.pipe_uncertainty) * ur.inch).to("meter")
        d2 = (ufloat(c.orifice_avg, c.orifice_uncertainty) * ur.inch).to("meter")
        rho = ufloat(c.rho_avg, c.rho_uncertainty) * ur.kg / (ur.meter**3)
        return d, d1, d2, rho


class LjconfigService:
    @staticmethod
    def create(form):
        ljconfig_entry = Ljconfig()
        form.populate_obj(ljconfig_entry)
        ljconfig_entry.is_active = False
        ljconfig_entry.is_valid = False
        ljconfig_entry.ain_all_negative_ch = ljm.constants.GND
        ljconfig_entry.buffer_size = int(ljconfig_entry.scan_rate / 2)
        ljconfig_entry.error_message = "None"
        ljconfig_entry.scan_rate_actual = 0
        try:
            db.session.add(ljconfig_entry)
            db.session.commit()
            ljconfig_entry = LjconfigService.validate(ljconfig_entry)
        except db.exc.IntegrityError:
            db.session.rollback()
            ljconfig_entry = dbService.fetch_existing(Ljconfig, ljconfig_entry)
        return ljconfig_entry

    @staticmethod
    def activate(ljconfig_id):
        new_active_ljconfig = db.session.execute(
            select(Ljconfig).where(
                and_(Ljconfig.id == ljconfig_id, Ljconfig.is_valid == True)
            )
        ).scalar_one_or_none()
        if (
            new_active_ljconfig is not None
            and new_active_ljconfig.is_active
            or new_active_ljconfig is None
        ):
            return
        active_ljconfig = db.session.execute(
            select(Ljconfig).where(Ljconfig.is_active == True)
        ).scalar_one_or_none()
        if active_ljconfig is not None:
            active_ljconfig.is_active = False
            db.session.add(active_ljconfig)
        new_active_ljconfig.is_active = True
        db.session.add(new_active_ljconfig)
        db.session.commit()
        return

    @staticmethod
    def validate(ljconfig_entry):
        result = TestService.execute(ljconfig_entry, live=False)
        if isinstance(result, Test):
            if any(
                [
                    (sr.ljm_backlog > 100) or (sr.ljm_backlog > 100)
                    for sr in result.stream_reads
                ]
            ):
                ljconfig_entry.error_message = "Too many backlogs"
            else:
                ljconfig_entry.is_valid = True
            ljconfig_entry.scan_rate_actual = result.scan_rate_actual
        else:
            ljconfig_entry.error_message = str(result)

        db.session.add(ljconfig_entry)
        db.session.commit()
        return ljconfig_entry

    @staticmethod
    def get_default_window(ljconfig: Ljconfig) -> tuple[int, int]:
        """Gets default window start and stop values for valid test data range"""
        start = ljconfig.scan_rate
        finish = int(ljconfig.buffer_size * (ljconfig.read_count - 1.8))
        return start, finish


class TestService:
    @staticmethod
    def get(test_id: int) -> Test:
        test_entry = db.session.get(Test, test_id)
        if test_entry is None:
            return None
        elif test_entry.ufloat_vp1 == "not analyzed":
            TestService.analyze(test_entry)
        return test_entry

    @staticmethod
    def execute(ljconfig: Ljconfig = None, live: bool = False) -> Test:
        if ljconfig is None:
            ljconfig = db.session.execute(
                select(Ljconfig).where(Ljconfig.is_active == True)
            ).scalar_one()
        handle = ljm.openS()
        info = ljm.getHandleInfo(handle)
        console.print(
            f"\nOpened a LabJack with Device type: {info[0]}, Connection type: {info[1]},\n"
            f"Serial number: {info[2]}, IP address: {info[3]}, Port: {info[4]},\nMax bytes per MB: {info[5]}",
            style="magenta",
        )

        # Stream Configuration
        aScanListNames = ["AIN0", "AIN1", "AIN2"]  # Scan list names to stream
        numAddresses = len(aScanListNames)
        aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]

        # ljm config
        scanRate = ljconfig.scan_rate
        scansPerRead = ljconfig.buffer_size
        MAX_REQUESTS = ljconfig.read_count
        # The number of eStreamRead calls that will be performed.

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        # ljm config object creation
        aConfig = {
            "AIN_ALL_NEGATIVE_CH": ljconfig.ain_all_negative_ch,
            "AIN0_RANGE": 10,
            "AIN1_RANGE": 1,
            "AIN2_RANGE": 1,
            "STREAM_SETTLING_US": ljconfig.stream_settling_us,
            "STREAM_RESOLUTION_INDEX": ljconfig.stream_resolution_index,
        }

        try:
            # lj stream config
            # Ensure triggered stream is disabled.
            ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)
            # Enabling internally-clocked stream.
            ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)
            # Write the analog inputs' negative channels, ranges, stream settling time
            # and stream resolution configuration.
            ljm.eWriteNames(handle, len(aConfig), aConfig.keys(), aConfig.values())

            # Configure and start stream
            sync_1 = datetime.now()
            scanRate = ljm.eStreamStart(
                handle, scansPerRead, numAddresses, aScanList, scanRate
            )
            sync_2 = datetime.now()
            start = sync_1 + (sync_2 - sync_1) / 2

            # start test
            if live:
                ljm.eWriteName(handle, "DAC0", 5)
                console.print("valve opened", style="magenta")

            console.print(
                f"\nStream started with a scan rate of {scanRate:.2f} Hz."
                f"\nPerforming {MAX_REQUESTS} stream reads.\n",
                style="magenta",
            )

            ljmScanBacklog = 0
            totScans = 0
            totSkip = 0  # Total skipped samples
            i = 1
            while i <= MAX_REQUESTS:
                # stop test
                if i == MAX_REQUESTS and live:
                    ljm.eWriteName(handle, "DAC0", 0)
                    console.print("valve closed", style="magenta")

                ret = ljm.eStreamRead(handle)
                aData = ret[0]
                ljScanBacklog = ret[1]
                ljmScanBacklog = ret[2]
                scans = len(aData) / numAddresses
                totScans += scans

                if i == 1 and aData:
                    # initialize test db entry
                    w_start, w_finish = LjconfigService.get_default_window(ljconfig)
                    test_entry = Test(
                        start=start.isoformat(),
                        finish="test incomplete",
                        duration=0,
                        scan_rate_actual=0.0,
                        window_start=w_start,
                        window_finish=w_finish,
                        ufloat_vp1="not analyzed",
                        ufloat_vp2="not analyzed",
                        ufloat_vdx="not analyzed",
                        ljconfig_id=ljconfig.id,
                        constants_id=db.session.execute(
                            select(Constants.id).where(Constants.is_active == True)
                        ).scalar_one(),
                    )

                # Count the skipped samples which are indicated by -9999 values. Missed
                # samples occur after a device's stream buffer overflows and are
                # reported after auto-recover mode ends.
                curSkip = aData.count(-9999.0)
                skipped = curSkip / numAddresses
                totSkip += curSkip

                # create stream entry and scan bulk insert
                stream_read_entry = StreamRead(
                    stream_i=i,
                    skipped=skipped,
                    lj_backlog=ljScanBacklog,
                    ljm_backlog=ljmScanBacklog,
                    # test_id=test_entry.id,
                )
                test_entry.stream_reads.append(stream_read_entry)

                for k in range(0, len(aData), numAddresses):
                    scan_entry = Scan(
                        ain0=aData[k],
                        ain1=aData[k + 1],
                        ain2=aData[k + 2]
                        # "stream_read_id": stream_read_entry.id,
                    )
                    stream_read_entry.scans.append(scan_entry)

                console.print(
                    f"\neStreamRead {i}"
                    f"\nScans Skipped = {skipped}, Scan Backlogs: Device = {ljScanBacklog}, LJM = {ljmScanBacklog}\n",
                    style="magenta",
                )
                i += 1

            # update test entry
            end = datetime.now()
            tt = (end - start).seconds + float((end - start).microseconds) / 1000000
            test_entry.finish = end.isoformat()
            test_entry.duration = str(tt)
            test_entry.scan_rate_actual = scanRate

            console.print(
                f"\nTotal scans = {totScans}"
                f"\nTime taken = {tt:.2f} seconds"
                f"\nLJM Scan Rate = {scanRate:.1f} scans/second"
                f"\nTimed Scan Rate = {totScans/tt:.2f} scans/second"
                f"\nTimed Sample Rate = {totScans*numAddresses/tt:.1f} samples/second"
                f"\nSkipped scans = {totSkip/numAddresses}",
                style="magenta",
            )

        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            console.print(f"valve closed\n {ljme}", style="orange_red1")
            ljm.close(handle)
            return ljme
        except Exception:
            e = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            console.print(f"valve closed\n {e}", style="orange_red1")
            ljm.close(handle)
            return e

        try:
            console.print("\nStop Stream\n", style="magenta")
            ljm.eStreamStop(handle)
        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            console.print(ljme, style="orange_red1")
            ljm.close(handle)
            return ljme
        except Exception:
            e = sys.exc_info()[1]
            console.print(e, style="orange_red1")
            ljm.close(handle)
            return e

        ljm.close(handle)
        return test_entry

    @staticmethod
    def set_bounds(bound_form, test_id):
        test_entry = db.session.get(Test, test_id)
        bound_form.populate_obj(test_entry)
        test_entry = TestService.analyze(test_entry)

    @staticmethod
    def get_images(t: Test) -> list[str]:
        """
        Builds test images from raw test data or fetches them and returns paths
        Plots position and differences according to voltage and shows window
        """
        base = "sendes/app"
        raw_v = f"/static/tests/{t.id}_{t.window_start}_{t.window_finish}_{t.constants_id}_raw.png"
        delta_v = f"/static/tests/{t.id}_{t.window_start}_{t.window_finish}_{t.constants_id}_delta.png"

        if not os.path.isfile(f"{base}{raw_v}"):
            tt = np.arange(
                0, len(t.scans) * 1 / t.scan_rate_actual, 1 / t.scan_rate_actual
            )
            dtype = [(f"ain{i}", "f8") for i in range(3)]
            scans = [(s.ain0, s.ain1, s.ain2) for s in t.scans]
            scans = np.array(scans, dtype=dtype)

            # Raw plot
            fig, ax = plt.subplots()
            ax.plot(tt, scans["ain2"], label="$V_X$")
            ax.plot(tt, scans["ain0"], label="$V_{P1}$")
            ax.plot(tt, scans["ain1"], label="$V_{P2}$", color="green")
            ax.vlines(
                x=[
                    t.window_start / t.scan_rate_actual,
                    t.window_finish / t.scan_rate_actual,
                ],
                ymin=0,
                ymax=1,
                colors=["black", "black"],
            )
            ax.set_ylabel("Volts")
            ax.set_xlabel("Seconds")
            ax.legend(loc="center left")
            ax.set_title("Raw Data")

            forward = lambda x: x * t.scan_rate_actual
            inverse = lambda x: x / t.scan_rate_actual
            secxax = ax.secondary_xaxis("top", functions=(forward, inverse))
            secxax.set_xlabel("Sample")

            # Save the figure
            plt.savefig(f"{base}{raw_v}", bbox_inches="tight")

            # Delta plot
            x_scale = 100
            tt = tt[:-1]
            fig, ax = plt.subplots()
            ax.plot(tt, np.diff(scans["ain2"]) * x_scale, label="$\Delta V_X$")
            ax.plot(tt, (scans["ain0"] - scans["ain1"])[:-1], color="orange")
            ax.plot(
                tt,
                (scans["ain0"] - scans["ain1"])[:-1],
                "-",
                dashes=(4, 4),
                color="green",
            )

            ax.vlines(
                x=[
                    t.window_start / t.scan_rate_actual,
                    t.window_finish / t.scan_rate_actual,
                ],
                ymin=-0.05,
                ymax=0.55,
                colors=["black", "black"],
            )

            vp1 = lines.Line2D([], [], color="orange")
            vp2 = lines.Line2D([], [], linestyle="-", dashes=(4, 4), color="green")
            vdx = lines.Line2D([], [], color="blue")

            ax.set_ylabel("Volts")
            ax.set_xlabel("Seconds")
            ax.legend(
                [vdx, (vp1, vp2)],
                ["$\\frac{100\Delta V_X}{\Delta t}$", "$\Delta V_P$"],
                loc="center left",
            )
            ax.set_title("Processed Raw Data")

            secxax = ax.secondary_xaxis("top", functions=(forward, inverse))
            secxax.set_xlabel("Sample")

            plt.savefig(f"{base}{delta_v}", bbox_inches="tight")

        return [raw_v, delta_v]

    @staticmethod
    def analyze(test_entry: Test) -> Test:
        """
        Calculates ufloats for vp1, vp2, and vdx over window, saves to db and returns entry
        """
        scans = [
            (s.ain0, s.ain1, s.ain2)
            for s in test_entry.scans[
                test_entry.window_start : test_entry.window_finish
            ]
        ]
        dtype = [(f"ain{i}", "f8") for i in range(3)]
        scans = np.array(scans, dtype=dtype)

        ufloat_vp1 = ufloat(np.average(scans["ain0"]), np.std(scans["ain0"]))
        ufloat_vp2 = ufloat(np.average(scans["ain1"]), np.std(scans["ain1"]))
        ufloat_vdx = ufloat(
            np.average(np.diff(scans["ain2"])), np.std(np.diff(scans["ain2"]))
        )

        test_entry.ufloat_vp1 = str(ufloat_vp1)
        test_entry.ufloat_vp2 = str(ufloat_vp2)
        test_entry.ufloat_vdx = str(ufloat_vdx)

        db.session.add(test_entry)
        db.session.commit()

        return test_entry


class ResultService:
    @staticmethod
    def get_vars(t: Test, c: Constants) -> tuple[Quantity, Quantity, Quantity]:
        """
        Given a Test and constants entry, get dx ufloat and pressure quantity_ufloats (constants contain xducer calibration)
        """
        dx = ResultService.v2l(ufloat_fromstr(t.ufloat_vdx) * ur.volt)
        p1 = ResultService.v2p(ufloat_fromstr(t.ufloat_vp1) * ur.volt, "p1", c)
        p2 = ResultService.v2p(ufloat_fromstr(t.ufloat_vp2) * ur.volt, "p2", c)
        return dx, p1, p2

    @staticmethod
    def analyze(test_id: int, constants_id: int = None) -> dict:
        """
        Given a test id, returns ufloat cd string according to tested constants
        Constants can be passed explicitly

        Saves cd ufloat str to test entry
        Returns dict containing component uncertainties with and their UMF with respect to Cd
        """
        test_entry = db.session.get(Test, test_id)
        constants = db.session.get(
            Constants, test_entry.constants_id if constants_id is None else constants_id
        )

        d, d1, d2, rho = ConstantsService.get_vars(constants)
        dx, p1, p2 = ResultService.get_vars(test_entry, constants)

        p1_ucal = ufloat(1, (0.000697**2 + 0.000436**2) ** (1 / 2))
        p2_ucal = ufloat(1, (0.000226**2 + 0.000635**2) ** (1 / 2))
        p1_tot = p1 * p1_ucal
        p2_tot = p2 * p2_ucal
        sample_period = 1 / test_entry.scan_rate_actual
        dt = ufloat(sample_period, (sample_period * 267) ** (1 / 2) * 1.6552e-8) * ur.s
        try:
            cd = (
                4
                * (d / 2) ** 2
                * (dx / dt)
                / (
                    d2**2
                    * (2 * (p1_tot - p2_tot) / (rho * (1 - (d2 / d1) ** 4))) ** (1 / 2)
                )
            )
        except Exception as e:
            return e

        # variable : [ ufloat_str, umf ]
        cd_dict = {
            "cd": [str(cd.magnitude), 1],
            "d": [
                str(d.to("in").magnitude),
                abs(cd.derivatives[next(iter(d.to("in").derivatives))]),
            ],
            "d1": [
                str(d1.to("in").magnitude),
                abs(cd.derivatives[next(iter(d1.to("in").derivatives))]),
            ],
            "d2": [
                str(d2.to("in").magnitude),
                abs(cd.derivatives[next(iter(d2.to("in").derivatives))]),
            ],
            "rho": [str(rho.magnitude), abs(cd.derivatives[next(iter(rho.derivatives))])],
            "dx": [
                str(dx.to("in").magnitude),
                abs(cd.derivatives[next(iter(dx.to("in").derivatives))]),
            ],
            "dt": [str(dt.magnitude), abs(cd.derivatives[next(iter(dt.derivatives))])],
            #"p1": [
            #    str(p1.to("psi").magnitude),
            #    abs(cd.derivatives[next(iter(p1.to("psi").derivatives))]),
            #],
            #"p1_cal": [str(p1_ucal), abs(cd.derivatives[next(iter(p1_ucal.derivatives))])],
            #"p2": [
            #    str(p2.to("psi").magnitude),
            #    abs(cd.derivatives[next(iter(p2.to("psi").derivatives))]),
            #],
            #"p2_cal": [str(p2_ucal), abs(cd.derivatives[next(iter(p2_ucal.derivatives))])],
            "dp": [
                str(p1_tot.to("psi").magnitude -  p2_tot.to("psi").magnitude),
                (cd.derivatives[next(iter(p1_tot.to("psi").derivatives))]**2 +
                cd.derivatives[next(iter(p2_tot.to("psi").derivatives))]**2)**(1/2),
            ],
        }
        return cd_dict

    @staticmethod
    def v2p(v: Quantity, p: str, c: Constants) -> Quantity:
        """
        Given voltage, transducer designator (1 or 2), and constants entry, returns pressure quantity_ufloat
        """
        return (
            (
                (v / (20 * 5.9 * ur.ohm) - 0.004 * ur.A)
                * (200 * ur.psi)
                / (0.016 * ur.A)
                * getattr(c, f"{p}_slope")
                + getattr(c, f"{p}_offset") * ur.psi
            )
        ).to("Pa")

    @staticmethod
    def v2l(v: Quantity) -> Quantity:
        """Given voltage, return distance quantity_ufloat"""
        return (v * 7.853 * ur.inch / ur.V).to("m")

    @staticmethod
    def get_images(cd_dict: dict, test_id: int, const_id: int = None) -> str:
        t = db.session.get(Test, test_id)
        base = "sendes/app"
        percentage_img = f"/static/results/{test_id}_{t.window_start}_{t.window_finish}_{t.constants_id if const_id is None else const_id}_uPer.png"

        if not os.path.isfile(f"{base}{percentage_img}"):
            urels_wrt_cd = [(ufloat_fromstr(lis[0]).s / (ufloat_fromstr(lis[0]).n if ufloat_fromstr(lis[0]).n != 0 else 1e-10) * lis[1]) ** 2
                for key, lis in cd_dict.items()
                if key != "cd"
            ]
            sum_urels_wrt_cd = sum(urels_wrt_cd)
            plt.clf()
            plt.bar(
                x=[var for var in cd_dict.keys() if var != "cd"],
                height=[ uwc / sum_urels_wrt_cd for uwc in urels_wrt_cd],
                color="blue",
            )

            plt.xlabel("Variable")
            plt.ylabel("Percentage Uncertainty wrt CD")
            plt.savefig(f"{base}{percentage_img}")

        return percentage_img


class dbService:
    # gets existing row based on unique constraint
    @staticmethod
    def fetch_existing(model, instance):
        """
        Gets existing model instance with matching properties
        """
        conditions = []
        for attr in inspect(instance).attrs:
            # Reflectively build conditions based on the object's attributes (ChatGPT)
            # only constrained fields
            if attr.key in {c.name for c in model.__table_args__[0].columns}:
                conditions.append(
                    getattr(model, attr.key) == getattr(instance, attr.key)
                )
        instance = db.session.execute(
            select(model).where(and_(*conditions))
        ).scalar_one()
        return instance

    @staticmethod
    def populate_sample_data():
        scan_rate = 267
        stream_reads = 5
        sec_div = 2
        ain0_uncertainty = (0.007120869,)
        ain1_uncertainty = (0.007436709,)
        ain2_uncertainty = (6.08881e-5,)

        scans_per_read = int(scan_rate / sec_div)
        constants = Constants(
            piston_avg=3.505,
            piston_uncertainty=0.002284631,
            orifice_avg=0.238,
            orifice_uncertainty=7.84915e-4,
            rho_avg=1000,
            rho_uncertainty=0,
            pipe_avg=0.618,
            pipe_uncertainty=0.001129,
            p1_slope=0.9977953,
            p1_offset=-0.008752722,
            p2_slope=1.002007,
            p2_offset=0.1061045,
            is_active=True,
        )
        ljconfig = Ljconfig(
            scan_rate=scan_rate,
            scan_rate_actual=scan_rate,
            buffer_size=scans_per_read,
            read_count=stream_reads,
            ain_all_negative_ch=ljm.constants.GND,
            stream_settling_us=0,
            stream_resolution_index=8,
            is_active=True,
            is_valid=True,
            error_message="None",
        )

        t = datetime.now()
        w_start, w_finish = LjconfigService.get_default_window(ljconfig)
        test = Test(
            start=str(t),
            finish=str(t + timedelta(seconds=stream_reads / sec_div)),
            duration=str(
                (timedelta(seconds=stream_reads / sec_div)).seconds
                + float((timedelta(seconds=stream_reads / sec_div)).microseconds)
                / 1000000
            ),
            scan_rate_actual=scan_rate,
            window_start=w_start,
            window_finish=w_finish,
            ufloat_vp1="not analyzed",
            ufloat_vp2="not analyzed",
            ufloat_vdx="not analyzed",
        )
        #
        x = np.arange(0, stream_reads / sec_div, 1 / scan_rate)
        # sample test data
        ain0, ain1, ain2 = np.ones_like(x), np.ones_like(x), np.ones_like(x)
        # ain0 = P1
        ain0[:] = 0.9451
        # ain1 = P2
        ain1[(x < 0.5)] = 0.9451
        ain1[(x >= 0.5) & (x < 1)] = (
            -(0.9451 - 0.471) / 0.5 * x[(x >= 0.5) & (x < 1)] + 0.9451 + 0.9451 - 0.47
        )
        ain1[(x >= 1) & (x < 2)] = 0.47
        ain1[(x >= 2)] = (0.9451 - 0.471) / 0.5 * x[(x >= 2)] - 1.4253
        # ain2 = x
        ain2[(x < 0.5)] = 0.2
        ain2[(x >= 0.5) & (x < 2)] = x[(x >= 0.5) & (x < 2)] * 0.368 + 0.016
        ain2[(x >= 2)] = 2 * 0.368 + 0.016

        # apply noise
        ain0 = np.random.normal(ain0, ain0_uncertainty)
        ain1 = np.random.normal(ain1, ain1_uncertainty)
        ain2 = np.random.normal(ain2, ain2_uncertainty)

        # create stream reads and scans
        j = 1
        for k in range(5):
            i = k * 0.5
            stream_read = StreamRead(stream_i=j, skipped=0, lj_backlog=0, ljm_backlog=0)
            j += 1
            stream_read.scans = [
                Scan(ain0=x, ain1=y, ain2=z)
                for x, y, z in zip(
                    ain0[(i < x) & (i + 0.5 > x)],
                    ain1[(i < x) & (i + 0.5 > x)],
                    ain2[(i < x) & (i + 0.5 > x)],
                )
            ]
            test.stream_reads.append(stream_read)

        constants.tests = [test]
        ljconfig.tests = [test]
        db.session.add(constants)
        db.session.add(ljconfig)
        db.session.add(test)
        db.session.commit()

    @staticmethod
    def start():
        # create sample data - ljconfig, constants, test, streamreads, scan
        # get actual values from matlab UncertaintyPropagation for voltages and constants
        if not db.session.get(Constants, 1):
            dbService.populate_sample_data()
