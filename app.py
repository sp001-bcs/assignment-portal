from datetime import datetime, timezone
from flask import Flask, render_template, request
from validation import validate_submission
import storage


def create_app(data_file="submissions.json"):
    app = Flask(__name__)
    app.config["DATA_FILE"] = data_file

    def page(errors=None, form=None, success=None, status=200):
        subs = storage.load(app.config["DATA_FILE"])
        return render_template("index.html", submissions=subs,
                               errors=errors or [], form=form or {},
                               success=success), status

    @app.get("/")
    def index():
        return page()

    @app.post("/submit")
    def submit():
        clean, errors = validate_submission(request.form)
        if errors:
            return page(errors=errors, form=clean, status=400)
        clean["submitted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        storage.save(app.config["DATA_FILE"], clean)
        return page(success="Submission saved.")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
