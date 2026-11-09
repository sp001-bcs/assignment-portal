# Assignment Submission Portal

A simple web portal where students submit assignment links, protected by an automated CI pipeline. Every push runs the tests on GitHub Actions. The test report is delivered automatically to a local HTTP receiver, which saves it as `testreport.json`. The report is also emailed, and the static portal is published to GitHub Pages only when all tests pass.

- **Repository:** https://github.com/sp001-bcs/assignment-portal
- **Live demo (GitHub Pages):** https://sp001-bcs.github.io/assignment-portal/

---

## Features

- Form with **name, registration number, assignment title and submission URL**
- Validation: all fields required; URL must be a valid `http://` or `https://` link
- Valid submissions are saved to `submissions.json` and shown in a list
- Invalid submissions are rejected with a validation message and **not saved**
- 3 automated tests (pytest)
- CI pipeline (GitHub Actions) on **every push**
- JSON test report sent to a **local receiver** for both passing and failing runs
- Bonus: **conditional deployment** to GitHub Pages (only on `main` when all tests pass)
- Bonus: **email report** after every run

---

## Project structure

```
assignment-portal/
├── app.py                     Flask web server (the portal)
├── validation.py              Validation rules for the form
├── storage.py                 Save / load submissions (JSON file)
├── templates/index.html       Portal page: form + list of submissions
├── tests/test_portal.py       Automated tests
├── scripts/build_report.py    Converts pytest results into testreport.json
├── receiver/receiver.py       Local HTTP receiver that saves the report
├── docs/index.html            Static version of the portal for GitHub Pages
├── .github/workflows/ci.yml   CI pipeline
├── requirements.txt           Python dependencies (flask, pytest)
├── pytest.ini                 pytest settings
└── .gitignore
```

---

## Requirements

- Python 3.12
- Git
- Docker Desktop (for the tunnel)
- A GitHub account

---

## 1. Setup (one time)

Run these in **Command Prompt** inside the project folder:

```cmd
git clone https://github.com/sp001-bcs/assignment-portal.git
cd assignment-portal
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> On macOS/Linux use `source venv/bin/activate` instead of `venv\Scripts\activate`.

---

## 2. Run the application

```cmd
venv\Scripts\activate
python app.py
```

Open **http://127.0.0.1:5000** in the browser. Press `Ctrl + C` to stop.

---

## 3. Run the tests

```cmd
venv\Scripts\activate
pytest -v
```

| # | Test | Expected result |
|---|------|-----------------|
| 1 | `test_valid_submission_is_saved_and_listed` | Complete details and a valid URL are saved and appear in the list |
| 2 | `test_missing_registration_number_is_rejected` | Rejected with the message "Registration number is required." |
| 3 | `test_invalid_url_is_rejected_and_not_saved` | Rejected and not saved |

To generate the JSON report locally:

```cmd
pytest -v --junitxml=results.xml
python scripts\build_report.py results.xml testreport.json
```

---

## 4. Start the local report receiver

Open a **second** Command Prompt in the project folder and keep it running:

```cmd
venv\Scripts\activate
set RECEIVER_TOKEN=your-secret-token
python receiver\receiver.py
```

Output: `Receiver listening on port 5001`

The receiver accepts `POST /report`, checks the `X-Token` header, saves the body as **`testreport.json`** and keeps a copy of every run in the **`reports/`** folder.

---

## 5. Start the tunnel

GitHub's runner cannot reach `localhost` on your computer, so a tunnel is used. Open a **third** Command Prompt (Docker Desktop must be running) and keep it running:

```cmd
docker run --rm cloudflare/cloudflared:latest tunnel --no-autoupdate --url http://host.docker.internal:5001
```

Copy the URL it prints (e.g. `https://xxxx.trycloudflare.com`). Opening it in a browser should show **"Receiver is running"**.

> The URL changes every time the tunnel restarts. Update the `RECEIVER_URL` secret when it changes.

---

## 6. GitHub configuration

### Repository secrets
**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|-------|
| `RECEIVER_URL` | Tunnel URL, without a trailing `/` |
| `RECEIVER_TOKEN` | Same token used when starting the receiver |
| `MAIL_USERNAME` | Gmail address used to send the report (bonus) |
| `MAIL_PASSWORD` | Gmail **App Password**, 16 characters, no spaces (bonus) |
| `MAIL_TO` | Email address that receives the report (bonus) |

### GitHub Pages
**Settings → Pages → Source: GitHub Actions**

---

## 7. How the pipeline works

Defined in `.github/workflows/ci.yml`. Runs on **every push**.

**Job `test`:**
1. Check out the pushed commit
2. Set up Python 3.12 and install dependencies
3. Run `pytest -v --junitxml=results.xml`. A failing test fails this step and the job.
4. *(always)* Build `testreport.json` from the real test results
5. *(always)* Send the report to the local receiver via the tunnel
6. *(always)* Upload the report as a build artifact
7. *(always)* Email the report. This step uses `continue-on-error`, so an email problem never hides the test result.

Steps 4 to 7 use `if: always()`, so the report is delivered for **both passing and failing** runs.

**Job `deploy`:**
Runs only when the push is to `main` **and** the `test` job succeeded. It publishes the `docs/` folder to GitHub Pages. If tests fail, this job is skipped and the previously published version stays online.

---

## 8. Test report format

```json
{
  "repository": "sp001-bcs/assignment-portal",
  "branch": "main",
  "commit_sha": "…",
  "pipeline_run_id": "…",
  "pipeline_run_number": "…",
  "pipeline_run_url": "https://github.com/sp001-bcs/assignment-portal/actions/runs/…",
  "execution_timestamp": "2026-11-09T13:30:00+00:00",
  "tests": [
    { "name": "test_valid_submission_is_saved_and_listed", "result": "passed", "failure_message": null }
  ],
  "summary": { "total": 3, "passed": 3, "failed": 0, "overall_status": "passed" }
}
```

---

## 9. Demonstration workflow

Keep the receiver and the tunnel running, then:

1. **Passing run:** push working code → all tests pass, run is green, `testreport.json` shows `passed`, Pages is deployed.
2. **Failing run:** in `validation.py`, replace the URL error line with
   `pass  # errors.append("Submission URL must be a valid http(s) link.")`
   and push → `test_invalid_url_is_rejected_and_not_saved` fails, run is red, `testreport.json` shows `failed` with the message, deploy is skipped.
3. **Fixed run:** restore the original line and push → all tests pass again.

```cmd
git add .
git commit -m "message"
git push
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| *Send report* fails with "Could not resolve host" | The tunnel is not running or `RECEIVER_URL` is outdated |
| Receiver returns `401 Invalid token` | `RECEIVER_TOKEN` secret and the receiver's token do not match |
| *Email* fails with `535 Username and Password not accepted` | Use a Gmail App Password (2-Step Verification must be on) |
| *Deploy* fails with "Get Pages site failed" | Set **Settings → Pages → Source** to **GitHub Actions** |
| `ModuleNotFoundError: app` when running pytest | Run pytest from the project root (where `pytest.ini` is) 