# Pipeline Security Contract

`ci/pipeline-policy.json` is the machine-readable acceptance contract for
NEKO-70. CI must fail when maintained-source line coverage is below 95 percent
or when any required report is missing. Coverage XML is the SonarQube Cloud
input; JSON, text, HTML, and JUnit reports are retained as downloadable evidence.

Every third-party action reference is an exact 40-character commit SHA. Workflow
permissions are read-only. Checkout must not persist credentials. No workflow may
use `pull_request_target`.

Fork pull requests run tests and generate reports without repository secrets.
Sonar analysis is skipped for fork pull requests because their code must never
execute with `SONAR_TOKEN`. Trusted branch and same-repository pull-request runs
may scan only after tests and the coverage gate pass.

CodeSee is restricted to trusted `push` and manual events. It does not check out
or execute pull-request code with its token.
