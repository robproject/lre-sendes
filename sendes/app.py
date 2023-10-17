from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from typing import List

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange


from datetime import datetime
import sys
from labjack import ljm
import numpy as np

app = Flask(__name__)


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
        db.UniqueConstraint("scan_rate", "buffer_size", name="uq_ljconfig"),
    )


class Test(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    start: Mapped[str] = mapped_column(db.Text)
    end: Mapped[str] = mapped_column(db.Text)
    duration: Mapped[str] = mapped_column(db.Text)
    scan_rate_actual: Mapped[float] = mapped_column(db.Float)
    cd: Mapped[float] = mapped_column(db.Float)
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
    img_path: Mapped[str] = mapped_column(db.String)

    test_id: Mapped[int] = mapped_column(db.ForeignKey("test.id"))
    constants_id: Mapped[int] = mapped_column(db.ForeignKey("constants.id"))

    __table_args__ = (db.UniqueConstraint("test_id", "constants_id", name="uq_result"),)


with app.app_context():
    db.create_all()


class ConstantsForm(FlaskForm):
    id = HiddenField(default=1)
    piston_rad = FloatField("Piston ID Radius", default=0.3)
    orifice_id = FloatField("Orifice ID", default=0.0127)
    rho = FloatField("Water Density Constant", default=1000)
    downstream_id = FloatField("Downstream pip ID", default=0.0254)
    v2p = FloatField("AIN Voltage to Pressure Scalar", default=1.885e-6)
    v2l = FloatField("AIN Voltage to Length Scalar",default=0.2032)
    constants_dropdown = SelectField("Select Constants")


class LJConfigForm(FlaskForm):
    id = HiddenField(default=1)
    scan_rate = IntegerField("Scan Rate", default=3000)
    read_count = IntegerField("Test Duration in .5s Increments", default=10)
    stream_settling_us = IntegerField("Signal Settle Time in Microseconds", default=0)
    stream_resolution_index = IntegerField(
        "Noise Reduction", validators=[NumberRange(min=0, max=8)], default=0
    )
    ain0_range = SelectField("AIN Gain", choices=[10, 1, 0.1, 0.01], default=10)

    ljconfig_dropdown = SelectField("Select LJ Config")


class TestForm(FlaskForm):
    submit = SubmitField("Execute Test")


class ResultForm(FlaskForm):
    test_dropdown = SelectField("Select Test")


@app.route("/", methods=["GET", "POST"])
def index():
    constants_form = ConstantsForm(meta={"csrf": False})
    recent_constants = Constants.query.order_by(Constants.id.asc()).all()
    constants_form.constants_dropdown.choices = [
        f"{c.id} {c.piston_rad} {c.downstream_id}" for c in recent_constants
    ]
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

    ljconfig_form = LJConfigForm(meta={"csrf": False})
    recent_ljconfigs = Ljconfig.query.order_by(Ljconfig.id.asc()).all()
    ljconfig_form.ljconfig_dropdown.choices = [
        f"{ljc.id} {ljc.scan_rate} {ljc.read_count}" for ljc in recent_ljconfigs
    ]
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

    result_form = ResultForm(meta={"csrf": False})
    recent_tests = Test.query.order_by(Test.id.asc()).filter_by(
        ljconfig_id=ljconfig_form.id.data, constants_id=constants_form.id.data
    )
    result_form.test_dropdown.choices = [
        f"{t.id} {t.constants_id} {t.ljconfig_id}" for t in recent_tests
    ]
    if "test_dropdown" in request.form:
        # render test
        test_instance = db.session.get(Test, result_form.test_dropdown.data.split(" ")[0])
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

    test_form = TestForm(meta={"csrf": False})
    if "submit" in request.form:
        config_dict = {
            k.replace("constants_", "")
            .replace("ljconfig_", "")
            .replace("_hidden", ""): float(v)
            for k, v in request.form.items()
            if k != "submit"
        }
        test_instance = test(config_dict)
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

    template_dict = {
        "constants_form": constants_form,
        "ljconfig_form": ljconfig_form,
        "test_form": test_form,
        "result_form": result_form,
    }
    return render_template("index.html", **template_dict)


def test(config_dict):
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
        scanRate = config_dict['scan_rate']
        scansPerRead = int(scanRate / 2)
        MAX_REQUESTS = config_dict['read_count']  # The number of eStreamRead calls that will be performed.

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        # ljm config object creation and db save
        aConfig = {
            "AIN_ALL_NEGATIVE_CH": ljm.constants.GND,
            "AIN0_RANGE": config_dict['ain0_range'],
            "AIN1_RANGE": 10.0,
            "AIN2_RANGE": 10.0,
            "STREAM_SETTLING_US": config_dict['stream_settling_us'],
            "STREAM_RESOLUTION_INDEX": config_dict['stream_resolution_index'],
        }

        ljconfig_dict = {
            "scan_rate": scanRate,
            "buffer_size": scansPerRead,
            "read_count": MAX_REQUESTS,
        }
        ljconfig_dict.update({k.lower(): v for k, v in aConfig.items()})
        ljconfig_entry = Ljconfig(**ljconfig_dict)
        try:
            db.session.add(ljconfig_entry)
            db.session.commit()
        except db.exc.IntegrityError:
            db.session.rollback()
            ljconfig_entry = Ljconfig.query.filter_by(**ljconfig_dict).first()

        # constants object creation and db save
        piston_rad = config_dict['piston_rad']
        orifice_id = config_dict['orifice_id']
        downstream_id = config_dict['downstream_id']
        v2p = config_dict['v2p']
        v2l = config_dict['v2l']
        rho = config_dict['rho']

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
            db.session.add(constants_entry)
            db.session.commit()
        except db.exc.IntegrityError:
            db.session.rollback()
            constants_entry = Constants.query.filter_by(**constants_dict).first()

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

            # initialize test db entry
            test_entry = Test(
                start=start.isoformat(),
                cd=0.0,
                scan_rate_actual=0.0,
                end="test incomplete",
                duration="test incomplete",
                ljconfig_id=ljconfig_entry.id,
                constants_id=constants_entry.id,
            )
            db.session.add(test_entry)
            db.session.commit()

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
        except Exception:
            e = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            print(f"valve closed\n {e}")

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


def get_results(test_id):
    ## constants default to test if not specified
    # constants_id
    scans = (
        Scan.query.join(StreamRead, StreamRead.id == Scan.stream_read_id)
        .join(Test, Test.id == StreamRead.test_id)
        .filter(Test.id == test_id)
        .all()
    )
    # get configs for calculating cd values
    test = db.session.get(Test, test_id)
    constants = db.session.get(Constants, test.constants_id)

    # window of scans to output 100 result points
    result_objects = []
    window_size = int(len(scans) / 100)
    for i in range(0, len(scans), window_size):
        window = scans[i : i + window_size]
        result_entry = {
            "p1": np.average([scan.ain0 for scan in window]),
            "p2": np.average([scan.ain1 for scan in window]),
            "x": np.average(np.diff([scan.ain2 for scan in window])),
            "t": window_size * 1 / test.scan_rate_actual,
            "test_id": test_id,
        }

        result_entry["cd"] = get_cd(result_entry, constants)
        result_objects.append(result_entry)
    db.session.execute(db.insert(Result), result_objects)

    # update test with averaged cd
    test.cd = np.average([r["cd"] for r in result_objects])
    db.session.commit()
    return test


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


def get_plot(test_id):
    pass
    ## constants default to test if not specified
    # constants_id =
    # results = Result.query.filter(Result.test_id==test_id and )
