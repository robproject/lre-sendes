from app.main import bp
from app.extensions import db
from app.forms import ConstantsForm, LjconfigForm, TestBoundForm, TestForm, ResultForm
from app.services import ConstantsService, LjconfigService, TestService, ResultService
from app.models import Constants, Ljconfig, Test

from flask import render_template, redirect, url_for, send_from_directory, request, current_app
from sqlalchemy import select


@bp.route("/", methods=["GET", "POST"])
def index():
    #!!! include image of bar chart of partial derivative UMF of each variable
    return render_template("base.html")


@bp.route("/constants", methods=["GET"])
def get_constants():
    constants = db.session.execute(select(Constants)).scalars()
    return render_template("constants.html", constants=constants)


@bp.route("/constants/add", methods=["GET"])
def constant_form():
    constants_form = ConstantsForm()
    return render_template("constants_add.html", constants_form=constants_form)


@bp.route("/constants/add", methods=["POST"])
def add_constant():
    constants_form = ConstantsForm()
    if constants_form.validate_on_submit():
        constants_entry = ConstantsService.create(constants_form)
        return redirect(
            url_for("main.activate_constant", constants_id=constants_entry.id), code=307
        )
    else:
        return render_template("constants_add.html", constants_form=constants_form)


@bp.route("/constants/activate/<int:constants_id>", methods=["POST"])
def activate_constant(constants_id):
    ConstantsService.activate(constants_id)
    return redirect(url_for("main.get_constants"))


@bp.route("/ljconfig", methods=["GET"])
def get_ljconfigs():
    ljconfigs = db.session.execute(select(Ljconfig)).scalars()
    return render_template("ljconfig.html", ljconfigs=ljconfigs)


@bp.route("/ljconfig/add", methods=["GET"])
def ljconfig_form():
    ljconfig_form = LjconfigForm()
    return render_template("ljconfig_add.html", ljconfig_form=ljconfig_form)


@bp.route("/ljconfig/add", methods=["POST"])
def add_ljconfig():
    ljconfig_form = LjconfigForm()
    if ljconfig_form.validate_on_submit():
        ljconfig_entry = LjconfigService.create(ljconfig_form)
        return redirect(
            url_for("main.activate_ljconfig", ljconfig_id=ljconfig_entry.id), code=307
        )
    else:
        return render_template("ljconfig_add.html", ljconfig_form=ljconfig_form)


@bp.route("/ljconfig/activate/<int:ljconfig_id>", methods=["POST"])
def activate_ljconfig(ljconfig_id):
    LjconfigService.activate(ljconfig_id)
    return redirect(url_for("main.get_ljconfigs"))


@bp.route("/test", methods=["GET"])
def get_tests():
    # display list of tests, with buttons to view result or view test
    tests = db.session.execute(select(Test)).scalars()
    return render_template("tests.html", tests=tests)


@bp.route("/test", methods=["POST"])
def execute_test():
    if current_app.config["TESTING"]:
        return redirect(url_for("main.get_tests"))
    current_app.config["TESTING"] = True
    test_entry = TestService.execute(live=True)
    db.session.add(test_entry)
    db.session.commit()
    test_entry = TestService.analyze(test_entry)
    current_app.config["TESTING"] = False
    return redirect(url_for("main.get_test", test_id=test_entry.id))


@bp.route("/test/<int:test_id>", methods=["GET"])
def get_test(test_id):
    bound_form = TestBoundForm()
    test = TestService.get(test_id)
    if test is not None:
        bound_form.window_start.data = test.window_start
        bound_form.window_finish.data = test.window_finish
        images = TestService.get_images(test)
        cd = ResultService.analyze(test.id)
        return render_template("test.html", test=test, images=images, bound_form=bound_form, cd=cd)
    return redirect(url_for("main.get_tests"))


@bp.route("/test/set/<int:test_id>", methods=["POST"])
def set_test_bound(test_id):
    referrer = request.referrer
    if referrer:
        bound_form = TestBoundForm()
        if bound_form.validate_on_submit():
            TestService.set_bounds(bound_form, test_id)
        return redirect(referrer)
    else:
        return redirect(url_for("main.index"))


@bp.route("/results/<int:test_id>", methods=["GET"])
def get_result(test_id):
    cd = ResultService.analyze(test_id)
    print(cd)
    # display result for test with active constant applied. Provide option to
    # use different constants
    return render_template("result.html", test=test, cd=cd, images=images)


@bp.route("/results", methods=["GET"])
def results():
    tests = db.session.execute(select(Test)).scalars()
    # show list of aggregated results with active constants applied
    # provide option to show new constants aplied with checkboxes and new constants dropdown or something
    return render_template("results.html", tests=tests)

@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(directory="static/favicon/", path="favicon.ico", mimetype="image/vnd.microsoft.icon")