from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, AnyOf


class ConstantsForm(FlaskForm):
    piston_avg = FloatField("AVG Piston", default=3.505)
    piston_uncertainty = FloatField("U Piston", default=0.3)
    orifice_avg = FloatField("AVG Orifice", default=0.0127)
    orifice_uncertainty = FloatField("U Orifice", default=0.0127)
    rho_avg = FloatField("AVG Water Density Constant", default=1000)
    rho_uncertainty = FloatField("U Water Density Constant", default=0)
    pipe_avg = FloatField("AVG Pipe", default=0.0254)
    pipe_uncertainty = FloatField("U Pipe", default=0.0254)
    p1_slope = FloatField("P1 Slope")
    p1_offset = FloatField("P1 Offset")
    p2_slope = FloatField("P2 Slope")
    p2_offset = FloatField("P2 Offset")
    submit = SubmitField("Save Constants")


class LjconfigForm(FlaskForm):
    scan_rate = IntegerField("Scan Rate", default=267)
    read_count = IntegerField("Test Duration in .5s Increments", default=10)
    stream_settling_us = IntegerField("Signal Settle Time in Microseconds", default=0)
    stream_resolution_index = IntegerField(
        "Noise Reduction", validators=[NumberRange(min=0, max=8)], default=8
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
