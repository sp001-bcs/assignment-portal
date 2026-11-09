import json, os, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

xml_path = sys.argv[1] if len(sys.argv) > 1 else "results.xml"
out_path = sys.argv[2] if len(sys.argv) > 2 else "testreport.json"

tests = []
if os.path.exists(xml_path):
    root = ET.parse(xml_path).getroot()
    for tc in root.iter("testcase"):
        failure = tc.find("failure")
        if failure is None:
            failure = tc.find("error")
        if failure is not None:
            result = "failed"
            message = failure.get("message") or (failure.text or "")[:500]
        elif tc.find("skipped") is not None:
            result, message = "skipped", None
        else:
            result, message = "passed", None
        tests.append({
            "name": tc.get("name"),
            "classname": tc.get("classname"),
            "result": result,
            "failure_message": message,
            "duration_seconds": float(tc.get("time", 0)),
        })

passed = sum(t["result"] == "passed" for t in tests)
failed = sum(t["result"] == "failed" for t in tests)
status = "passed" if tests and failed == 0 else "failed"

repo = os.getenv("GITHUB_REPOSITORY", "local")
run_id = os.getenv("GITHUB_RUN_ID", "local")
report = {
    "repository": repo,
    "branch": os.getenv("GITHUB_REF_NAME", "local"),
    "commit_sha": os.getenv("GITHUB_SHA", "local"),
    "pipeline_run_id": run_id,
    "pipeline_run_number": os.getenv("GITHUB_RUN_NUMBER", "local"),
    "pipeline_run_url": f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run_id}",
    "execution_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "tests": tests,
    "summary": {"total": len(tests), "passed": passed, "failed": failed, "overall_status": status},
}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

lines = [f"Overall: {status.upper()}  ({passed}/{len(tests)} passed, {failed} failed)",
         f"Repository: {report['repository']}  Branch: {report['branch']}",
         f"Commit: {report['commit_sha']}",
         f"Run: {report['pipeline_run_url']}", "", "Tests:"]
for t in tests:
    lines.append(f"  [{t['result'].upper()}] {t['name']}" + (f"  -> {t['failure_message']}" if t["failure_message"] else ""))
with open("report_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Report written to {out_path}: {status} ({passed}/{len(tests)})")
