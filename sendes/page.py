from typing import List
from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask import render_template
from sqlalchemy import insert

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange


from datetime import datetime
import sys
#import csv
#import time
from labjack import ljm
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

app = Flask(__name__)

class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)
app.secret_key = 'test_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sendes.db"
db.init_app(app)



class Constants(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    piston_rad: Mapped[float] = mapped_column(db.Float)
    orifice_id: Mapped[float] = mapped_column(db.Float)
    downstream_id: Mapped[float] = mapped_column(db.Float)
    v2pa: Mapped[float] = mapped_column(db.Float)
    v2m: Mapped[float] = mapped_column(db.Float)
    tests: Mapped[List["Test"]] = relationship()


class Ljconfig(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    scan_rate: Mapped[int] = mapped_column(db.Integer)
    buffer_size: Mapped[int] = mapped_column(db.Integer)
    tests: Mapped[List["Test"]] = relationship()

class Test(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    start: Mapped[str] = mapped_column(db.Text)
    end: Mapped[str] = mapped_column(db.Text)
    duration: Mapped[str] = mapped_column(db.Text)
    ljconfig: Mapped[int] = mapped_column(ForeignKey("ljconfig.id"))
    constants: Mapped[int] = mapped_column(ForeignKey("constants.id"))
    stream_reads: Mapped[List["StreamRead"]] = relationship()

class StreamRead(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    stream_i: Mapped[int] = mapped_column(db.Integer)
    skipped: Mapped[int] = mapped_column(db.Integer)
    lj_backlog: Mapped[int] = mapped_column(db.Integer)
    ljm_backlog: Mapped[int] = mapped_column(db.Integer)
    scans: Mapped[List["Scan"]] = relationship()
    test: Mapped[int] = mapped_column(ForeignKey("test.id"))

class Scan(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ain0: Mapped[float] = mapped_column(db.Float)
    ain1: Mapped[float] = mapped_column(db.Float)
    ain2: Mapped[float] = mapped_column(db.Float)
    stream_read: Mapped[int] = mapped_column(ForeignKey("stream_read.id"))

    
    


class ConfigForm(FlaskForm):
    test = IntegerField('test label',validators=[NumberRange(min=0, max=10)] )

class ConfigSelect(FlaskForm):
    constants_dropdown = SelectField('Select Constant', coerce=int)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    select_form = ConfigSelect(meta={'csrf':False})
    recent_constants = Constants.query.order_by(Constants.id.desc()).limit(20).all()
    select_form.constants_dropdown.choices = [c.id for c in recent_constants]
    config_form = ConfigForm(meta={'csrf':False})
    if config_form.validate_on_submit():
        
        return render_template('index.html', config_form=config_form, select_form=select_form)
        

    return render_template('index.html', config_form=config_form, select_form=select_form)



@app.route('/call_log', methods=['GET'])
def log_get():
    return redirect(url_for('index'))

def test():
    with app.app_context():

        MAX_REQUESTS = 10  # The number of eStreamRead calls that will be performed.

        # Open first found LabJack
        handle = ljm.openS() 

        info = ljm.getHandleInfo(handle)
        #print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
        #      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
        #      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

        # Stream Configuration
        aScanListNames = ["AIN0", "AIN1", "AIN2"]  # Scan list names to stream
        numAddresses = len(aScanListNames)
        aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]
        scanRate = 3000
        scansPerRead = int(scanRate / 2)

        ljconfig_entry = Ljconfig(scan_rate=scanRate, buffer_size=scansPerRead)
        constants_entry = Constants(
            piston_rad=.3,
            orifice_id=.0127,
            downstream_id=.0254,
            v2pa=1.885e-6,
            v2m=0.2032)
        db.session.add(ljconfig_entry)
        db.session.add(constants_entry)
        db.session.commit()
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
            aValues = [ljm.constants.GND, 10.0, 10.0, 10.0, 0, 2]

            # Write the analog inputs' negative channels, ranges, stream settling time
            # and stream resolution configuration.
            ljm.eWriteNames(handle, len(aNames), aNames, aValues)



            # Configure and start stream

            sync_1 = datetime.now()
            scanRate = ljm.eStreamStart(handle, scansPerRead, numAddresses, aScanList, scanRate)
            sync_2 = datetime.now()

            start = sync_1 + (sync_2-sync_1)/2
            test_entry = Test(
                start=start.isoformat(),
                ljconfig=ljconfig_entry.id,
                constants=constants_entry.id,
                end="end",
                duration="duration"
            )
            db.session.add(test_entry)
            db.session.commit()
        
            ### clock sync
            ### goal: get timestamp of start that's correlated with core timer such that
            ### column can be added to csv containing actual datetimes associated with core timer
            print("\nStream started with a scan rate of %0.0f Hz." % scanRate)
            print("\nPerforming %i stream reads." % MAX_REQUESTS)
            totScans = 0
            totSkip = 0  # Total skipped samples

            # start test
            ljm.eWriteName(handle, "DAC0", 5)
            print('valve opened')

            #with open('app/test.csv', 'w', encoding='UTF8', newline='') as f:

            #    writer = csv.writer(f)
            #    # add start times
            #    writer.writerow(['start time', start_time])
            #    writer.writerow(['scan rate', scanRate])
            #    writer.writerow(['scan period (us)', 1/scanRate * 1e6])
            #    # header = aScanListNames
            #    writer.writerow(aScanListNames)


            ljmScanBacklog = 0
            i = 1
            while i <= MAX_REQUESTS:

                if i == MAX_REQUESTS:
                    # stop test
                    ljm.eWriteName(handle, "DAC0", 0)
                    print('valve closed')

            
                ret = ljm.eStreamRead(handle)

                aData = ret[0]
                ljmScanBacklog = ret[2]
                scans = len(aData) / numAddresses
                totScans += scans

                # Count the skipped samples which are indicated by -9999 values. Missed
                # samples occur after a device's stream buffer overflows and are
                # reported after auto-recover mode ends.
                curSkip = aData.count(-9999.0)
                skipped = curSkip/numAddresses
                totSkip += curSkip

                stream_read_entry = StreamRead(
                    stream_i=i,
                    skipped=skipped,
                    lj_backlog=ret[1],
                    ljm_backlog=ljmScanBacklog,
                    test=test_entry.id
                )
                db.session.add(stream_read_entry)
                db.session.commit()

                scan_objects = []
                for k in range(0, len(aData), numAddresses):
                    scan_entry = {
                        "ain0" : aData[k],
                        "ain1" : aData[k+1],
                        "ain2" : aData[k+2],
                        "stream_read" : stream_read_entry.id
                    }
                    scan_objects.append(scan_entry)

                db.session.execute(insert(Scan), scan_objects)
                # try writing to sqlite - instead of separate files, will need to create another table with test metadata
                #writer.writerows(rows)
            
                print("\neStreamRead %i" % i)
                ainStr = ""
                for j in range(0, numAddresses):
                    ainStr += "%s = %0.5f, " % (aScanListNames[j], aData[j])
                print("  1st scan out of %i: %s" % (scans, ainStr))
                print("  Scans Skipped = %0.0f, Scan Backlogs: Device = %i, LJM = "
                    "%i" % (skipped, ret[1], ljmScanBacklog))
                i += 1

            end = datetime.now()
            tt = (end - start).seconds + float((end - start).microseconds) / 1000000
            

            test_entry.end = end.isoformat()
            test_entry.duration = str(tt)
            db.session.commit()

            print("\nTotal scans = %i" % (totScans))
            print("Time taken = %f seconds" % (tt))
            print("LJM Scan Rate = %f scans/second" % (scanRate))
            print("Timed Scan Rate = %f scans/second" % (totScans / tt))
            print("Timed Sample Rate = %f samples/second" % (totScans * numAddresses / tt))
            print("Skipped scans = %0.0f" % (totSkip / numAddresses))

        except ljm.LJMError:
            ljme = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            print('valve closed')
            print(ljme)
        except Exception:
            e = sys.exc_info()[1]
            ljm.eWriteName(handle, "DAC0", 0)
            print('valve closed')
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

@app.route('/call_log', methods=['POST'])
def log_post():
    print('ok')
    test()
    return 'nothing', 200