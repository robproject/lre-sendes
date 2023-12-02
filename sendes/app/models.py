from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    p1_slope: Mapped[float] = mapped_column(db.Float)
    p1_offset: Mapped[float] = mapped_column(db.Float)
    p2_slope: Mapped[float] = mapped_column(db.Float)
    p2_offset: Mapped[float] = mapped_column(db.Float)
    is_active: Mapped[bool] = mapped_column(db.Boolean)
    tests: Mapped[list["Test"]] = relationship()

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
    tests: Mapped[list["Test"]] = relationship()

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
    duration: Mapped[str] = mapped_column(db.String)
    scan_rate_actual: Mapped[float] = mapped_column(db.Float)
    window_start: Mapped[int] = mapped_column(db.Integer)
    window_finish: Mapped[int] = mapped_column(db.Integer)
    ufloat_vp1: Mapped[str] = mapped_column(db.String)
    ufloat_vp2: Mapped[str] = mapped_column(db.String)
    ufloat_vdx: Mapped[str] = mapped_column(db.String)
    ljconfig_id: Mapped[int] = mapped_column(db.ForeignKey("ljconfig.id"))
    constants_id: Mapped[int] = mapped_column(db.ForeignKey("constants.id"))
    stream_reads: Mapped[list["StreamRead"]] = relationship()
    scans: Mapped[list["Scan"]] = relationship(
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
    scans: Mapped[list["Scan"]] = relationship()
    test_id: Mapped[int] = mapped_column(db.ForeignKey("test.id"), index=True)


class Scan(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ain0: Mapped[float] = mapped_column(db.Float)
    ain1: Mapped[float] = mapped_column(db.Float)
    ain2: Mapped[float] = mapped_column(db.Float)
    stream_read_id: Mapped[int] = mapped_column(
        db.ForeignKey("stream_read.id"), index=True
    )
