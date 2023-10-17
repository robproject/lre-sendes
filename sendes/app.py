from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from typing import List

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange


from datetime import datetime
import sys
import os
from labjack import ljm
import numpy as np
import matplotlib.pyplot as plt

IMG_FOLDER = os.path.join("sendes", "assets")


app = Flask(__name__)
app.config["PNG_FOLDER"] = IMG_FOLDER


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.secret_key = "test_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sendes.db"
db.init_app(app)


class Constants(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    piston_rad: Mapped[float] = mapped_column(db.Float)
    orifice_id: Mapped[float] = mapped_column(db.Float)
    rho: Mapped[float] = mapped_column(db.Float)
    downstream_id: Mapped[float] = mapped_column(db.Float)
    v2p: Mapped[float] = mapped_column(db.Float)
    v2l: Mapped[float] = mapped_column(db.Float)
    tests: Mapped[List["Test"]] = relationship()

    __table_args__ = (
        db.UniqueConstraint(
            "piston_rad",
            "orifice_id",
            "downstream_id",
            "v2p",
            "v2l",
            "rho",
            name="uq_constants",
        ),
    )


class Ljconfig(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    scan_rate: Mapped[int] = mapped_column(db.Integer)
    buffer_size: Mapped[int] = mapped_column(db.Integer)
    read_count: Mapped[int] = mapped_column(db.Integer)
    ain_all_negative_ch: Mapped[int] = mapped_column(db.Integer)
    ain0_range: Mapped[int] = mapped_column(db.Integer)
    ain1_range: Mapped[int] = mapped_column(db.Integer)
    ain2_range: Mapped[int] = mapped_column(db.Integer)
    stream_settling_us: Mapped[int] = mapped_column(db.Integer)
    stream_resolution_index: Mapped[int] = mapped_column(db.Integer)
    tests: Mapped[List["Test"]] = relationship()

    __table_args__ = (
        db.UniqueConstraint(
            "scan_rate",
            "read_count",
            "ain0_range",
            "stream_settling_us",
            "stream_resolution_index",
            name="uq_ljconfig",
        ),
    )


class Test(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    start: Mapped[str] = mapped_column(db.Text)
    end: Mapped[str] = mapped_column(db.Text)
    duration: Mapped[str] = mapped_column(db.Text)
    scan_rate_actual: Mapped[float] = mapped_column(db.Float)
    cd: Mapped[float] = mapped_column(db.Float)
    result_imgpath: Mapped[str] = mapped_column(db.String)
    ljconfig_id: Mapped[int] = mapped_column(db.ForeignKey("ljconfig.id"))
    constants_id: Mapped[int] = mapped_column(db.ForeignKey("constants.id"))
    stream_reads: Mapped[List["StreamRead"]] = relationship()


class StreamRead(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    stream_i: Mapped[int] = mapped_column(db.Integer)
    skipped: Mapped[int] = mapped_column(db.Integer)
    lj_backlog: Mapped[int] = mapped_column(db.Integer)
    ljm_backlog: Mapped[int] = mapped_column(db.Integer)
    scans: Mapped[List["Scan"]] = relationship()
    test_id: Mapped[int] = mapped_column(db.ForeignKey("test.id"))


class Scan(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ain0: Mapped[float] = mapped_column(db.Float)
    ain1: Mapped[float] = mapped_column(db.Float)
    ain2: Mapped[float] = mapped_column(db.Float)
    stream_read_id: Mapped[int] = mapped_column(db.ForeignKey("stream_read.id"))


class Result(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    t: Mapped[float] = mapped_column(db.Float)
    x: Mapped[float] = mapped_column(db.Float)
    p1: Mapped[float] = mapped_column(db.Float)
    p2: Mapped[float] = mapped_column(db.Float)
    cd: Mapped[float] = mapped_column(db.Float)

    test_id: Mapped[int] = mapped_column(db.ForeignKey("test.id"))


with app.app_context():
    db.create_all()


class ConstantsForm(FlaskForm):
    id = HiddenField(default=1)
    piston_rad = FloatField("Piston Radius (Inner)", default=0.3)
    orifice_id = FloatField("Orifice ID", default=0.0127)
    rho = FloatField("Water Density Constant", default=1000)
    downstream_id = FloatField("Downstream Pipe ID", default=0.0254)
    v2p = FloatField("AIN Voltage to Pressure Scalar", default=1.885e-6)
    v2l = FloatField("AIN Voltage to Length Scalar", default=0.2032)
    constants_dropdown = SelectField("Select Constants")


class LJConfigForm(FlaskForm):
    id = HiddenField(default=1)
    scan_rate = IntegerField("Scan Rate", default=3000)
    read_count = IntegerField("Test Duration in .5s Increments", default=10)
    stream_settling_us = IntegerField("Signal Settle Time in Microseconds", default=0)
    stream_resolution_index = IntegerField(
        "Noise Reduction", validators=[NumberRange(min=0, max=8)], default=0
    )
    ain0_range = SelectField("AIN0 Gain", choices=[10, 1, 0.1, 0.01], default=10)

    ljconfig_dropdown = SelectField("Select LJ Config")


class TestForm(FlaskForm):
    submit = SubmitField("Execute Test")


class ResultForm(FlaskForm):
    test_dropdown = SelectField("Select Test")


@app.route("/", methods=["GET", "POST"])
def index():
    constants_form = ConstantsForm(meta={"csrf": False})
    ljconfig_form = LJConfigForm(meta={"csrf": False})
    result_form = ResultForm(meta={"csrf": False})
    test_form = TestForm(meta={"csrf": False})
    test_instance = None

    # dropdown was changed
    if "constants_dropdown" in request.form:
        constants = db.session.get(
            Constants, constants_form.constants_dropdown.data.split(" ")[0]
        )
        constants_form.id.data = constants.id
        constants_form.piston_rad.data = constants.piston_rad
        constants_form.orifice_id.data = constants.orifice_id
        constants_form.rho.data = constants.rho
        constants_form.downstream_id.data = constants.downstream_id
        constants_form.v2p.data = constants.v2p
        constants_form.v2l.data = constants.v2l

    if "ljconfig_dropdown" in request.form:
        ljconfig = db.session.get(
            Ljconfig, ljconfig_form.ljconfig_dropdown.data.split(" ")[0]
        )
        ljconfig_form.id.data = ljconfig.id
        ljconfig_form.scan_rate.data = ljconfig.scan_rate
        ljconfig_form.read_count.data = ljconfig.read_count
        ljconfig_form.stream_settling_us.data = ljconfig.stream_settling_us
        ljconfig_form.stream_resolution_index.data = ljconfig.stream_resolution_index
        ljconfig_form.ain0_range.data = ljconfig.ain0_range

    if "test_dropdown" in request.form:
        # render test
        test_instance = db.session.get(
            Test, result_form.test_dropdown.data.split(" ")[0]
        )
        ljconfig = db.session.get(Ljconfig, test_instance.ljconfig_id)
        constants = db.session.get(Constants, test_instance.constants_id)
        ljconfig_form.id.data = ljconfig.id
        ljconfig_form.scan_rate.data = ljconfig.scan_rate
        ljconfig_form.read_count.data = ljconfig.read_count
        ljconfig_form.stream_settling_us.data = ljconfig.stream_settling_us
        ljconfig_form.stream_resolution_index.data = ljconfig.stream_resolution_index
        ljconfig_form.ain0_range.data = ljconfig.ain0_range
        constants_form.id.data = constants.id
        constants_form.piston_rad.data = constants.piston_rad
        constants_form.orifice_id.data = constants.orifice_id
        constants_form.rho.data = constants.rho
        constants_form.downstream_id.data = constants.downstream_id
        constants_form.v2p.data = constants.v2p
        constants_form.v2l.data = constants.v2l
        plot_path = test_instance.result_imgpath

    # all form data is accessible individually
    if "submit" in request.form:
        config_dict = {
            k.replace("constants_", "")
            .replace("ljconfig_", "")
            .replace("_hidden", ""): float(v)
            for k, v in request.form.items()
            if "dropdown" not in k and k != "submit"
        }
        test_result = execute_test(config_dict)
        if type(test_result) is int:
            test_instance = db.session.get(Test, test_result)
        else:
            return test_result
        calc_results(test_instance.id)
        plot_path = generate_plot(test_instance.id)
        ljconfig = db.session.get(Ljconfig, test_instance.ljconfig_id)
        constants = db.session.get(Constants, test_instance.constants_id)
        ljconfig_form.id.data = ljconfig.id
        ljconfig_form.scan_rate.data = ljconfig.scan_rate
        ljconfig_form.read_count.data = ljconfig.read_count
        ljconfig_form.stream_settling_us.data = ljconfig.stream_settling_us
        ljconfig_form.stream_resolution_index.data = ljconfig.stream_resolution_index
        ljconfig_form.ain0_range.data = ljconfig.ain0_range
        constants_form.id.data = constants.id
        constants_form.piston_rad.data = constants.piston_rad
        constants_form.orifice_id.data = constants.orifice_id
        constants_form.rho.data = constants.rho
        constants_form.downstream_id.data = constants.downstream_id
        constants_form.v2p.data = constants.v2p
        constants_form.v2l.data = constants.v2l
        result_form.test_dropdown.data = f"{test_instance.id} {test_instance.cd:1.3f} {test_instance.start[:-7]} {test_instance.scan_rate_actual:.2f}"

    recent_constants = Constants.query.order_by(Constants.id.asc()).all()
    constants_form.constants_dropdown.choices = [
        f"{c.id} {c.piston_rad} {c.orifice_id} {c.rho} {c.downstream_id} {c.v2p} {c.v2l}" for c in recent_constants
    ]

    recent_ljconfigs = Ljconfig.query.order_by(Ljconfig.id.asc()).all()
    ljconfig_form.ljconfig_dropdown.choices = [
        f"{ljc.id} {ljc.scan_rate} {ljc.read_count} {ljc.stream_settling_us} {ljc.stream_resolution_index} {ljc.ain0_range}" for ljc in recent_ljconfigs
    ]

    recent_tests = (
        Test.query.order_by(Test.id.desc())
        .filter_by(
            ljconfig_id=ljconfig_form.id.data, constants_id=constants_form.id.data
        )
        .all()
    )
    result_form.test_dropdown.choices = [
        f"{t.id} {t.cd:1.3f} {t.start[:-7]} {t.scan_rate_actual:.2f}" for t in recent_tests
    ]
    if not test_instance:
        if result_form.test_dropdown.choices:
            test_instance = db.session.get(
                Test, result_form.test_dropdown.choices[0].split(" ")[0]
            )
            plot_path = test_instance.result_imgpath
        else:
            plot_path = "favicon/lre.png"

    if test_instance:
        test_instance = {
            "start": f"{test_instance.start[:-4]}",
            "end": f"{test_instance.end[:-4]}",
            "duration": f"{test_instance.duration[:-4]}",
            "scan_rate_actual": f"{test_instance.scan_rate_actual:.1f}",
            "cd": f"{test_instance.cd:0.3f}",
        }
    template_dict = {
        "constants_form": constants_form,
        "ljconfig_form": ljconfig_form,
        "test_form": test_form,
        "result_form": result_form,
        "plot_path": plot_path,
        "test_instance": test_instance,
    }
    return render_template("index.html", **template_dict)


def execute_test(config_dict):
    with app.app_context():
        # Open first found LabJack
        handle = ljm.openS()
        info = ljm.getHandleInfo(handle)
        print(
            f"Opened a LabJack with Device type: {info[0]}, Connection type: {info[1]},\n"
            f"Serial number: {info[2]}, IP address: {info[3]}, Port: {info[4]},\nMax bytes per MB: {info[5]}"
        )

        # Stream Configuration
        aScanListNames = ["AIN0", "AIN1", "AIN2"]  # Scan list names to stream
        numAddresses = len(aScanListNames)
        aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]

        # ljm config
        scanRate = int(config_dict["scan_rate"])
        scansPerRead = int(scanRate / 2)
        MAX_REQUESTS = config_dict[
            "read_count"
        ]  # The number of eStreamRead calls that will be performed.

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        # ljm config object creation
        aConfig = {
            "AIN_ALL_NEGATIVE_CH": ljm.constants.GND,
            "AIN0_RANGE": config_dict["ain0_range"],
            "AIN1_RANGE": 10.0,
            "AIN2_RANGE": 10.0,
            "STREAM_SETTLING_US": config_dict["stream_settling_us"],
            "STREAM_RESOLUTION_INDEX": config_dict["stream_resolution_index"],
        }

        ljconfig_dict = {
            "scan_rate": scanRate,
            "buffer_size": scansPerRead,
            "read_count": MAX_REQUESTS,
        }
        ljconfig_dict.update({k.lower(): v for k, v in aConfig.items()})
        ljconfig_entry = Ljconfig(**ljconfig_dict)

        # constants object creation
        piston_rad = config_dict["piston_rad"]
        orifice_id = config_dict["orifice_id"]
        downstream_id = config_dict["downstream_id"]
        v2p = config_dict["v2p"]
        v2l = config_dict["v2l"]
        rho = config_dict["rho"]

        constants_dict = {
            "piston_rad": piston_rad,
            "orifice_id": orifice_id,
            "downstream_id": downstream_id,
            "v2p": v2p,
            "rho": rho,
            "v2l": v2l,
        }
        constants_entry = Constants(**constants_dict)

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
            ljm.eWriteName(handle, "DAC0", 5)
            print(
                "valve opened"
                f"\nStream started with a scan rate of {scanRate:.2f} Hz."
                f"\nPerforming {MAX_REQUESTS} stream reads."
            )

            ljmScanBacklog = 0
            totScans = 0
            totSkip = 0  # Total skipped samples
            i = 1
            while i <= MAX_REQUESTS:
                # stop test
                if i == MAX_REQUESTS:
                    ljm.eWriteName(handle, "DAC0", 0)
                    print("valve closed")

                ret = ljm.eStreamRead(handle)

                if i == 1:
                    # commit constant and config entries
                    try:
                        db.session.add(constants_entry)
                        db.session.commit()
                    except db.exc.IntegrityError:
                        db.session.rollback()
                        constants_entry = Constants.query.filter_by(
                            **constants_dict
                        ).first()
                    try:
                        db.session.add(ljconfig_entry)
                        db.session.commit()
                    except db.exc.IntegrityError:
                        db.session.rollback()
                        ljconfig_entry = Ljconfig.query.filter_by(
                            **ljconfig_dict
                        ).first()

                    # initialize test db entry
                    test_entry = Test(
                        start=start.isoformat(),
                        cd=0.0,
                        result_imgpath="/",
                        scan_rate_actual=0.0,
                        end="test incomplete",
                        duration="test incomplete",
                        ljconfig_id=ljconfig_entry.id,
                        constants_id=constants_entry.id,
                    )
                    db.session.add(test_entry)
                    db.session.commit()

                aData = ret[0]
                ljScanBacklog = ret[1]
                ljmScanBacklog = ret[2]
                scans = len(aData) / numAddresses
                totScans += scans

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
                    test_id=test_entry.id,
                )
                db.session.add(stream_read_entry)
                db.session.commit()

                scan_objects = []
                for k in range(0, len(aData), numAddresses):
                    scan_entry = {
                        "ain0": aData[k],
                        "ain1": aData[k + 1],
                        "ain2": aData[k + 2],
                        "stream_read_id": stream_read_entry.id,
                    }
                    scan_objects.append(scan_entry)
                db.session.execute(db.insert(Scan), scan_objects)

                print(
                    f"\neStreamRead {i}"
                    f"  Scans Skipped = {skipped}, Scan Backlogs: Device = {ljScanBacklog}, LJM = {ljmScanBacklog}"
                )

                i += 1

            end = datetime.now()
            tt = (end - start).seconds + float((end - start).microseconds) / 1000000

            # update test entry
            test_entry.end = end.isoformat()
            test_entry.duration = str(tt)
            test_entry.scan_rate_actual = scanRate
            db.session.commit()

            print(
                f"\nTotal scans = {totScans}"
                f"\nTime taken = {tt:.2f} seconds"
                f"\nLJM Scan Rate = {scanRate:.1f} scans/second"
                f"\nTimed Scan Rate = {totScans/tt:.2f} scans/second"
                f"\nTimed Sample Rate = {totScans*numAddresses/tt:.1f} samples/second"
                f"\nSkipped scans = {totSkip/numAddresses}"
            )

        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            print(f"valve closed\n {ljme}")
            ljm.close(handle)
            return f"{ljme}"
        except Exception:
            e = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            print(f"valve closed\n {e}")
            ljm.close(handle)
            return f"{e}"

        try:
            print("\nStop Stream")
            ljm.eStreamStop(handle)
        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            print(ljme)
            ljm.close(handle)
            return f"{ljme}"
        except Exception:
            e = sys.exc_info()[1]
            print(e)
            ljm.close(handle)
            return f"{e}"

        ljm.close(handle)
        return test_entry.id


def calc_results(test_id):
    ## constants default to test if not specified
    # constants_id
    scans = (
        Scan.query.join(StreamRead, StreamRead.id == Scan.stream_read_id)
        .join(Test, Test.id == StreamRead.test_id)
        .filter(Test.id == test_id)
        .all()
    )
    # get configs for calculating cd values
    test_instance = db.session.get(Test, test_id)
    constants = db.session.get(Constants, test_instance.constants_id)

    # window of scans to output 100 result points
    result_objects = []
    window_size = int(len(scans) / 100)
    dtypes = [("ain0", float), ("ain1", float), ("ain2", float)]
    scans_np = np.array(
        [(scan.ain0, scan.ain1, scan.ain2) for scan in scans], dtype=dtypes
    )
    for i in range(0, len(scans), window_size):
        window = scans_np[i : i + window_size]
        result_entry = {
            "p1": window["ain0"].mean(),
            "p2": window["ain1"].mean(),
            "x": np.diff(window["ain2"]).mean(),
            "t": window_size * 1 / test_instance.scan_rate_actual,
            "test_id": test_id,
        }

        result_entry["cd"] = get_cd(result_entry, constants)
        result_objects.append(result_entry)
    db.session.execute(db.insert(Result), result_objects)

    # update test with averaged cd from slice of results
    test_instance.cd = np.average([r["cd"] for r in result_objects[20:80]])
    db.session.commit()


def get_cd(r: dict, c: Constants):
    cd = (
        4
        * c.piston_rad**2
        * np.abs(r["x"] / r["t"])
        * c.downstream_id**-2
        * np.abs(
            2
            * np.abs(r["p1"] - r["p2"])
            * (c.rho * (1 - (c.downstream_id / c.orifice_id) ** 4) ** -1)
        )
        ** (-1 / 2)
    )
    return cd


def generate_plot(test_id):
    results = Result.query.filter_by(test_id=test_id).all()
    t = []
    ts = 0
    x = []
    p1 = []
    p2 = []
    cd = []
    for i, r in enumerate(results):
        t.append(ts)
        ts += r.t
        x.append(r.x)
        p1.append(r.p1)
        p2.append(r.p2)
        cd.append(r.cd)

    img_name = f"{test_id}.png"
    test_instance = db.session.get(Test, test_id)
    test_instance.result_imgpath = img_name

    plt.clf()
    plt.plot(t, x, label="Position")
    plt.plot(t, p1, label="P1")
    plt.plot(t, p2, label="P2")
    plt.plot(t, cd, label="Cd")
    plt.legend()
    plt.xlabel("Time")
    plt.savefig(f"sendes/static/{img_name}")

    db.session.commit()
    return img_name
