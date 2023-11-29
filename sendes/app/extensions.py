from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from pint import UnitRegistry

from rich.console import Console


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
ur = UnitRegistry()
console = Console()




