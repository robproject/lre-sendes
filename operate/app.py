from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy import select, and_, inspect
from typing import List

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, AnyOf

from datetime import datetime
import sys
import os

from labjack import ljm
import numpy as np
import matplotlib.pyplot as plt
from uncertainties import ufloat, ufloat_fromstr, unumpy
from pint import Quantity, UnitRegistry

from rich.console import Console

ur = UnitRegistry()
app = Flask(__name__)
app.config["SQLALCHEMY_ECHO"] = True

console = Console()


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.secret_key = "test_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sendes.db"
db.init_app(app)


class Constants(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    piston_avg: Mapped[float] = mapped_column(db.Float)
    piston_uncertainty: Mapped[float] = mapped_column(db.Float)
    orifice_avg: Mapped[float] = mapped_column(db.Float)
    orifice_uncertainty: Mapped[float] = mapped_column(db.Float)
    rho_avg: Mapped[float] = mapped_column(db.Float)
    rho_uncertainty: Mapped[float] = mapped_column(db.Float)
    pipe_avg: Mapped[float] = mapped_column(db.Float)
    pipe_uncertainty: Mapped[float] = mapped_column(db.Float)
    ain0_uncertainty: Mapped[float] = mapped_column(db.Float)
    ain1_uncertainty: Mapped[float] = mapped_column(db.Float)
    ain2_uncertainty: Mapped[float] = mapped_column(db.Float)
    p1_slope: Mapped[float] = mapped_column(db.Float)
    p1_offset: Mapped[float] = mapped_column(db.Float)
    p2_slope: Mapped[float] = mapped_column(db.Float)
    p2_offset: Mapped[float] = mapped_column(db.Float)
    is_active: Mapped[bool] = mapped_column(db.Boolean)
    tests: Mapped[List["Test"]] = relationship()

    __table_args__ = (
        db.UniqueConstraint(
            "piston_avg",
            "piston_uncertainty",
            "orifice_avg",
            "orifice_uncertainty",
            "rho_avg",
            "rho_uncertainty",
            "pipe_avg",
            "pipe_uncertainty",
            "ain0_uncertainty",
            "ain1_uncertainty",
            "ain2_uncertainty",
            "p1_slope",
            "p1_offset",
            "p2_slope",
            "p2_offset",
            name="uq_constants",
        ),
    )


class Ljconfig(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    scan_rate: Mapped[int] = mapped_column(db.Integer)
    scan_rate_actual: Mapped[float] = mapped_column(db.Float)
    buffer_size: Mapped[int] = mapped_column(db.Integer)
    read_count: Mapped[int] = mapped_column(db.Integer)
    ain_all_negative_ch: Mapped[int] = mapped_column(db.Integer)
    stream_settling_us: Mapped[int] = mapped_column(db.Integer)
    stream_resolution_index: Mapped[int] = mapped_column(db.Integer)
    is_active: Mapped[bool] = mapped_column(db.Boolean)
    is_valid: Mapped[bool] = mapped_column(db.Boolean)
    error_message: Mapped[str] = mapped_column(db.String)
    tests: Mapped[List["Test"]] = relationship()

    __table_args__ = (
        db.UniqueConstraint(
            "scan_rate",
            "stream_settling_us",
            "stream_resolution_index",
            name="uq_ljconfig",
        ),
    )


class Test(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    start: Mapped[str] = mapped_column(db.Text)
    finish: Mapped[str] = mapped_column(db.Text)
    duration: Mapped[float] = mapped_column(db.Float)
    scan_rate_actual: Mapped[float] = mapped_column(db.Float)
    window_start: Mapped[int] = mapped_column(db.Integer)
    window_finish: Mapped[int] = mapped_column(db.Integer)
    window_n: Mapped[int] = mapped_column(db.Integer)
    avg_uain0: Mapped[str] = mapped_column(db.String)
    avg_uain1: Mapped[str] = mapped_column(db.String)
    avg_uain2_diff: Mapped[str] = mapped_column(db.String)
    ljconfig_id: Mapped[int] = mapped_column(db.ForeignKey("ljconfig.id"))
    constants_id: Mapped[int] = mapped_column(db.ForeignKey("constants.id"))
    stream_reads: Mapped[List["StreamRead"]] = relationship()
    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        secondary="stream_read",
        primaryjoin="Test.id==StreamRead.test_id",
        secondaryjoin="StreamRead.id==Scan.stream_read_id",
        viewonly=True,
    )


class StreamRead(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    stream_i: Mapped[int] = mapped_column(db.Integer)
    skipped: Mapped[int] = mapped_column(db.Integer)
    lj_backlog: Mapped[int] = mapped_column(db.Integer)
    ljm_backlog: Mapped[int] = mapped_column(db.Integer)
    scans: Mapped[List["Scan"]] = relationship()
    test_id: Mapped[int] = mapped_column(db.ForeignKey("test.id"), index=True)


class Scan(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ain0: Mapped[float] = mapped_column(db.Float)
    ain1: Mapped[float] = mapped_column(db.Float)
    ain2: Mapped[float] = mapped_column(db.Float)
    stream_read_id: Mapped[int] = mapped_column(
        db.ForeignKey("stream_read.id"), index=True
    )


with app.app_context():
    db.create_all()


class ConstantsForm(FlaskForm):
    piston_avg = FloatField("AVG Piston", default=3.505)
    piston_uncertainty = FloatField("U Piston", default=0.3)
    orifice_avg = FloatField("AVG Orifice", default=0.0127)
    orifice_uncertainty = FloatField("U Orifice", default=0.0127)
    rho_avg = FloatField("AVG Water Density Constant", default=1000)
    rho_uncertainty = FloatField("U Water Density Constant", default=0)
    pipe_avg = FloatField("AVG Pipe", default=0.0254)
    pipe_uncertainty = FloatField("U Pipe", default=0.0254)
    ain0_uncertainty = FloatField("U AIN0")
    ain1_uncertainty = FloatField("U AIN1")
    ain2_uncertainty = FloatField("U AIN2")
    p1_slope = FloatField("P1 Slope")
    p1_offset = FloatField("P1 Offset")
    p2_slope = FloatField("P2 Slope")
    p2_offset = FloatField("P2 Offset")
    submit = SubmitField("Save Constants")


class LjconfigForm(FlaskForm):
    scan_rate = IntegerField("Scan Rate", default=3000)
    read_count = IntegerField("Test Duration in .5s Increments", default=10)
    stream_settling_us = IntegerField("Signal Settle Time in Microseconds", default=0)
    stream_resolution_index = IntegerField(
        "Noise Reduction", validators=[NumberRange(min=0, max=8)], default=0
    )
    submit = SubmitField("Save and Validate LJConfig")


class TestBoundForm(FlaskForm):
    window_start = IntegerField("Window Start")
    window_finish = IntegerField("Window Finish")
    submit = SubmitField("Update Window")


class TestForm(FlaskForm):
    submit = SubmitField("Execute Test")


class ResultForm(FlaskForm):
    test_dropdown = SelectField("Select Test")


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
            # Reflectively build conditions based on the object's attributes (ChatGPT)
            conditions = []
            for attr in inspect(constants_entry).attrs:
                if attr.key in {
                    c.name for c in Constants.__table_args__[0].columns
                }:  # only constrained fields
                    conditions.append(
                        getattr(Constants, attr.key)
                        == getattr(constants_entry, attr.key)
                    )
            constants_entry = db.session.execute(
                select(Constants).where(and_(*conditions))
            ).scalar_one_or_none()
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
        d1 = (ufloat(c.orifice_avg, c.orifice_uncertainty) * ur.inch).to("meter")
        d2 = (ufloat(c.pipe_avg, c.pipe_uncertainty) * ur.inch).to("meter")
        rho = ufloat(c.rho_avg, c.rho_uncertainty) * ur.kg / (ur.meter**3)
        return d, d1, d2, rho


class LjconfigService:
    @staticmethod
    def create(form):
        ljconfig_entry = Ljconfig()
        form.populate_obj(ljconfig_entry)
        ljconfig_entry.is_active = False
        ljconfig_entry.is_valid = False
        try:
            db.session.add(ljconfig_entry)
            db.session.commit()
        except db.exc.IntegrityError:
            db.session.rollback()
            # Reflectively build conditions based on the object's attributes (ChatGPT)
            conditions = []
            for attr in inspect(ljconfig_entry).attrs:
                if attr.key in {
                    c.name for c in Ljconfig.__table_args__[0].columns
                }:  # only constrained fields
                    conditions.append(
                        getattr(Ljconfig, attr.key) == getattr(ljconfig_entry, attr.key)
                    )
            ljconfig_entry = db.session.execute(
                select(Ljconfig).where(and_(*conditions))
            ).scalar_one_or_none()
            return ljconfig_entry

        ljconfig_entry = LjconfigService.validate(ljconfig_entry)
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
        try:
            result = TestService.execute(ljconfig_entry, live=False)
        except Exception as e:
            result = e

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
            ljconfig_entry.error_message = result

        db.session.add(ljconfig_entry)
        db.session.commit()
        return ljconifg_entry


class TestService:
    @staticmethod
    def get(test_id: int) -> Test:
        test_entry = db.session.get(Test, test_id)
        if test_entry.ufloat_ain0 == "not analyzed":
            test_entry = TestService.analyze(test_entry)
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
        scanRate = int(ljconfig.scan_rate)
        scansPerRead = int(scanRate / 2)
        MAX_REQUESTS = (
            ljconfig.read_count
        )  # The number of eStreamRead calls that will be performed.

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        # ljm config object creation
        aConfig = {
            "AIN_ALL_NEGATIVE_CH": ljm.constants.GND,
            "AIN0_RANGE": 1,
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
                    test_entry = Test(
                        start=start.isoformat(),
                        finish="test incomplete",
                        duration=0,
                        scan_rate_actual=0.0,
                        window_start=int(scansPerRead * 2),
                        window_finish=int(scansPerRead * (MAX_REQUESTS - 1.8)),
                        ufloat_ain0="not analyzed",
                        ufloat_ain1="not analyzed",
                        ufloat_ain2_diff="not analyzed",
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
                    scan_entry = {
                        "ain0": aData[k],
                        "ain1": aData[k + 1],
                        "ain2": aData[k + 2],
                        # "stream_read_id": stream_read_entry.id,
                    }
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
            test_entry.end = end.isoformat()
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
            console.print(f"valve closed\n {ljme}", style="magenta")
            ljm.close(handle)
            return e
        except Exception:
            e = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            console.print(f"valve closed\n {e}", style="magenta")
            ljm.close(handle)
            return e

        try:
            console.print("\nStop Stream\n", style="magenta")
            ljm.eStreamStop(handle)
        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            console.print(ljme, style="magenta")
            ljm.close(handle)
            return e
        except Exception:
            e = sys.exc_info()[1]
            console.print(e, style="magenta")
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
        raw_v = f"/static/tests/{t.id}_{t.window_start}_{t.window_finish}_{t.constants_id}_raw.png"
        delta_v = f"/static/tests/{t.id}_{t.window_start}_{t.window_finish}_{t.constants_id}_delta.png"

        if not os.path.isfile(raw_v):
            t = np.arange(
                0, t.window_n * 1 / t.scan_rate_actual, 1 / t.scan_rate_actual
            )
            dtype = [(f"ain{i}", "f8") for i in range(3)]
            scans = np.array(
                t.scans[t.window_start : t.window_finish],
                dtype=dtype,
            )
            plt.clf()
            plt.plot(t, scans["ain0"], label="$V_{P1}$")
            plt.plot(t, scans["ain1"], label="$V_{P2}$")
            plt.plot(t, scans["ain2"], label="$V_X$")
            plt.ylabel("Volts")
            plt.xlabel("Time")
            plt.legend()
            plt.savefig(raw_v)

            t = t[:-1]
            plt.clf()
            plt.plot(t, (scans["ain1"] - scans["ain0"])[:-1], label="$\Delta P$")
            plt.plot(t, np.diff(scans["ain2"]), label="$\Delta V_X$")
            plt.ylabel("Volts")
            plt.xlabel("Time")
            plt.legend()
            plt.savefig(delta_v)

        return [raw_v, delta_v]

    @staticmethod
    def analyze(test_entry: Test) -> Test:
        constants = db.session.get(Constants, test_entry.constants_id)
        dtype = [(f"ain{i}", "f8") for i in range(3)]
        scans = np.array(
            test_entry.scans[test_entry.window_start : test_entry.window_finish],
            dtype=dtype,
        )
        num_scans = len(scans)
        test_entry.window_n = num_scans - 1

        test_entry.avg_uain0 = str(
            np.average(
                unumpy.umatrix(
                    scans["ain0"], np.ones(num_scans) * constants.ain0_uncertainty
                )[:-1]
            )
        )
        test_entry.avg_uain1 = str(
            np.average(
                unumpy.matrix(
                    scans["ain1"], np.ones(num_scans) * constants.ain1_uncertainty
                )[:-1]
            )
        )
        test_entry.avg_uain2_diff = str(
            np.average(
                unumpy.matrix(
                    np.diff(scans["ain2"]),
                    np.ones(num_scans - 1) * pow(2, 0.5) * constants.ain2_uncertainty,
                )
            )
        )

        db.session.add(test_entry)
        db.session.commit()

        return test_entry


class ResultService:
    @staticmethod
    def get_vars(t: Test, c: Constants):
        dx = ResultService.v2l(ufloat_fromstr(t.avg_uain2_diff) * ur.volt)
        p1 = ResultService.v2p(ufloat_fromstr(t.avg_uain0) * ur.volt, "p1", c)
        p2 = ResultService.v2p(ufloat_fromstr(t.avg_uain1) * ur.volt, "p2", c)
        return dx, p1, p2

    @staticmethod
    def analyze(test_entry: Test, constants_id: int = None) -> ufloat:
        constants = db.session.get(
            Constants, test_entry.constants_id if constants_id is None else constants_id
        )

        d, d1, d2, rho = ConstantsService.get_vars(constants)
        dx, p1, p2 = ResultService.get_vars(test_entry, constants)

        dt = 1 / test_entry.scan_rate_actual
        num = 4 * (d / 2) ** 2 * dx / dt
        rad_num = 2 * (p1 - p2)
        rad_den = rho * (1 - (d2 / d1) ** 4)
        den = d2**2 * (rad_num / rad_den) ** (1 / 2)
        cd = num / den
        print(cd.dimensionless == True)

        return cd.magnitude

    @staticmethod
    def v2p(v: Quantity, p: str, c: Constants) -> Quantity:
        return (
            (
                (v / (20 * 5.9 * ur.ohm) - 0.004 * ur.A)
                * (200 * ur.psi)
                / (0.016 * ur.A)
                * getattr(c, f"{p}_slope")
                + getattr(c, f"{p}_offset")
            )
        ).to("Pa")

    @staticmethod
    def v2l(v: Quantity) -> Quantity:
        return (v * 7.853 * ur.inch / ur.V).to("m")

    @staticmethod
    def get_images(test_id):
        # check if images exist, render if not
        # image 1: cd with dp and dxdt, include shaded region for +/-stdev
        # https://stackoverflow.com/a/43069856/14410691
        # image 2: x position, p1, p2 with all scales
        # image 3: bar chart of relative uncertainties of each variable
        # maybe include calculation window
        # return paths in dict
        pass


@app.route("/", methods=["GET", "POST"])
def index():
    #!!! include image of bar chart of partial derivative UMF of each variable
    return render_template("base.html")


@app.route("/constants", methods=["GET"])
def get_constants():
    constants = db.session.execute(select(Constants)).scalars()
    return render_template("constants.html", constants=constants)


@app.route("/constants/add", methods=["GET"])
def constant_form():
    constants_form = ConstantsForm()
    return render_template("constants_add.html", constants_form=constants_form)


@app.route("/constants/add", methods=["POST"])
def add_constant():
    constants_form = ConstantsForm()
    if constants_form.validate_on_submit():
        constants_entry = ConstantsService.create(constants_form)
        return redirect(
            url_for("activate_constant", constants_id=constants_entry.id), code=307
        )
    else:
        return render_template("constants_add.html", constants_form=constants_form)


@app.route("/constants/activate/<int:constants_id>", methods=["POST"])
def activate_constant(constants_id):
    ConstantsService.activate(constants_id)
    return redirect(url_for("get_constants"))


@app.route("/ljconfig", methods=["GET"])
def get_ljconfigs():
    ljconfigs = db.session.execute(select(Ljconfig)).scalars()
    return render_template("ljconfig.html", ljconfigs=ljconfigs)


@app.route("/ljconfig/add", methods=["GET"])
def ljconfig_form():
    ljconfig_form = LjconfigForm()
    return render_template("ljconfig_add.html", ljconfig_form=ljconfig_form)


@app.route("/ljconfig/add", methods=["POST"])
def add_ljconfig():
    ljconfig_form = LjconfigForm()
    if ljconfig_form.validate_on_submit():
        ljconfig_entry = LjconfigService.create(ljconfig_form)
        return redirect(
            url_for("activate_ljconfig", ljconifg_id=ljconfig_entry.id), code=307
        )
    else:
        return render_template("ljconfig_add.html", ljconfig_form=ljconfig_form)


@app.route("/ljconfig/activate/<int:ljconfig_id>", methods=["POST"])
def activate_ljconfig(ljconfig_id):
    LjconfigService.activate(ljconfig_id)
    return redirect(url_for("get_ljconfigs"))


@app.route("/test", methods=["GET"])
def get_tests():
    # display list of tests, with buttons to view result or view test
    tests = db.session.execute(select(Test)).scalars()
    return render_template("test.html", tests=tests)


@app.route("/test", methods=["POST"])
def execute_test():
    test_entry = TestService.execute(live=True)
    db.session.add(test_entry)
    db.session.commit()
    return redirect(url_for("get_test", test_id=test_entry.id), code=307)


@app.route("/test/<int:test_id>", methods=["GET"])
def get_test(test_id):
    bound_form = TestBoundForm()
    test = TestService.get(test_id)
    images = TestService.get_images(test)
    return render_template("test.html", test=test, images=images, bound_form=bound_form)


@app.route("/test/set/<int:test_id>", methods=["PUT"])
def set_test_bound(test_id):
    referrer = request.referrer
    if referrer:
        bound_form = TestBoundForm()
        if bound_form.validate_on_submit():
            TestService.set_bounds(bound_form, test_id)
        return redirect(referrer)
    else:
        return redirect(url_for("index"))


@app.route("/results/<int:test_id>", methods=["GET"])
def get_result(test_id):
    # display result for test with active constant applied. Provide option to
    # use different constants
    pass


@app.route("/results", methods=["GET"])
def results():
    # show list of aggregated results with active constants applied
    # provide option to show new constants applied with checkboxes and new constants dropdown or something
    pass
