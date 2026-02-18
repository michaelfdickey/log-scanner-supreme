Defines common log types and what to look for in each log type.  This will be used to determine which log types to prompt the user for and also to determine which log types to analyze when the user provides a log file.

# ARC logs

## Controller Log

This is a GitHub Actions Runner Controller (ARC) controller log from the `gha-runner-scale-set-controller` pod running in Kubernetes. The controller manages the lifecycle of ephemeral self-hosted runner scale sets.

### What to look for

**Reconciliation & Scale Set Management**
- `Reconciling` / `Successfully reconciled` — controller reconciliation loop health
- `AutoscalingRunnerSet` / `EphemeralRunnerSet` / `AutoscalingListener` — CRD lifecycle events
- Desired runner count vs. actual runner count mismatches
- Scale-up and scale-down events and whether they completed successfully

**Runner Provisioning Failures**
- Pods stuck in `Pending`, `ContainerCreating`, or `CrashLoopBackOff`
- `EphemeralRunner` creation failures or timeouts
- Image pull errors (`ErrImagePull`, `ImagePullBackOff`)
- Resource quota exceeded or insufficient CPU/memory for runner pods
- Node affinity/taint/toleration mismatches preventing scheduling

**Listener & Webhook Issues**
- `AutoscalingListener` pod failures — this is the component that receives workflow job events from GitHub
- Session creation or renewal failures (`createSession`, `refreshSession`)
- `MessageQueueTokenExpired` or authentication errors against the GitHub Actions service
- Lost connection to GitHub Actions service, reconnection attempts

**GitHub API & Authentication**
- GitHub App or PAT authentication failures
- Rate limiting from the GitHub API (`403`, `rate limit exceeded`)
- Registration token generation failures
- Runner registration/deregistration errors

**Kubernetes & Infrastructure**
- Leader election issues (controller HA)
- Webhook server startup or TLS certificate errors
- RBAC permission errors (`forbidden`, `cannot list/watch/create`)
- Namespace or resource not found errors
- etcd or API server connectivity issues

**Performance & Timing**
- Slow reconciliation loops (high `reconcile_duration_seconds`)
- Job queue buildup — jobs waiting but no runners scaling up
- Runner startup latency — time from scale-up decision to runner ready
- Excessive controller restarts

### Analysis prompt

```
You are analyzing a GitHub Actions Runner Controller (ARC) controller log from a Kubernetes deployment, from the perspective of GitHub Support. This controller (gha-runner-scale-set-controller) manages ephemeral self-hosted runner scale sets for GitHub Actions.

IMPORTANT CONTEXT: GitHub's support boundary for ARC extends only to ARC sending requests to scale runners up and down. Everything else (Kubernetes scheduling, networking, resource limits, pod failures) is the customer's infrastructure responsibility.

=== PRIORITY 1: SCALING STATUS (report this FIRST) ===
This is the single most important thing to determine. Look for evidence that scale sets are successfully scaling up and down:
- Look for log lines showing runner count changes: desired count going up (scale-up) and back down (scale-down)
- Look for `AutoscalingRunnerSet` reconciliation events that show `desiredReplicas`, `currentReplicas`, or replica count changes
- Look for `EphemeralRunner` creation (scale-up) and deletion (scale-down) events
- Look for `EphemeralRunnerSet` updates showing runner count changes
- Identify each scale set by name and track its runner count over time
- Look for patterns like: idle (0 runners) → scale up (N runners) → scale back down (0 or fewer runners)

You MUST include a "scaling_status" object in your response with:
- "is_scaling": true/false — whether there is clear evidence of scale sets scaling up AND down
- "summary": a human-readable statement like "Scale set 'my-runner-set' scales from 0 runners up to 5 runners and back down to 0 runners."
- "scale_sets": an array of objects with {"name": "scale-set-name", "min_observed": 0, "max_observed": 5, "scales_up": true, "scales_down": true}

If scaling is working correctly, this is strong evidence that ARC itself is functioning properly and any remaining issues are likely in the customer's Kubernetes environment.

=== PRIORITY 2: Standard analysis ===
After reporting scaling status, also analyze:
1. Reconciliation health — are resources being reconciled successfully?
2. Listener connectivity — is the AutoscalingListener maintaining its connection to GitHub Actions?
3. Authentication & API — GitHub API errors, rate limiting, or auth failures?
4. Kubernetes issues — RBAC errors, resource quota, scheduling failures, pod crashes (note: these are customer-side)
5. Performance — slow reconciliation, job queue buildup, runner startup latency

Flag any errors, warnings, repeated failures, or patterns that indicate degraded operation. For Kubernetes-side issues, note that these fall outside GitHub's ARC support boundary.
```

## Listener Log

## Api Log

## config files

# Actions logs

## Workflow Run Log

This is a GitHub Actions workflow run log from a job execution. These logs are generated when a workflow runs on GitHub-hosted or self-hosted runners and contain the output of each step in the job, including setup, checkout, build, test, and deployment steps.

### What to look for

**Job Setup & Runner**
- `Set up job` step — runner image version, OS, architecture, runner group, labels
- Runner assignment delays — long queue times before a runner picks up the job
- Runner version or image compatibility issues
- Self-hosted runner vs GitHub-hosted runner indicators
- Container or service container setup issues

**Checkout & Source Control**
- `actions/checkout` failures — auth errors, submodule failures, LFS issues
- Shallow clone depth problems
- Branch/ref resolution failures — detached HEAD, missing refs
- Sparse checkout or path filter issues
- Large repository clone timeouts

**Package & Dependency Management**
- `npm install`, `pip install`, `dotnet restore`, `maven`, `gradle` dependency failures
- Package version conflicts or resolution errors
- Registry authentication failures (npm, PyPI, NuGet, Maven Central, GitHub Packages)
- Cache hit/miss for `actions/cache` or built-in caching (setup-node, setup-python, etc.)
- Lock file inconsistencies (`package-lock.json`, `yarn.lock`, `Pipfile.lock`, `Gemfile.lock`)
- Deprecated or yanked package versions

**Build & Compilation**
- Compiler errors and warnings (TypeScript, Java, C#, Go, Rust, C/C++)
- Build tool configuration issues (webpack, vite, MSBuild, CMake)
- Out-of-memory during builds (heap allocation failures, OOM killed)
- Build timeout — step exceeding time limits
- Missing environment variables or secrets (`***` masking issues)

**Test Execution**
- Test failures — assertion errors, expected vs actual mismatches
- Test timeouts and hangs
- Flaky test patterns — tests that sometimes pass, sometimes fail
- Code coverage threshold failures
- Test framework configuration issues (Jest, pytest, JUnit, xUnit, RSpec)
- Test fixture or database setup failures

**Deployment & Release**
- Deployment step failures — auth, permissions, target environment issues
- Container image build/push failures (Docker, ACR, ECR, GCR)
- Cloud provider CLI errors (az, aws, gcloud, kubectl)
- Environment protection rule violations
- Artifact upload/download failures

**Actions & Workflow Syntax**
- Action version resolution failures (`uses: actions/xxx@version`)
- Composite action or reusable workflow errors
- Expression evaluation failures (`${{ }}` syntax)
- Matrix strategy issues — specific matrix combinations failing
- Conditional step (`if:`) evaluation problems
- Secret or variable reference errors
- GITHUB_TOKEN permission issues (`permissions:` block)

**Resource & Infrastructure**
- Disk space exhaustion — `/dev/sda1` full, no space left on device
- Memory limits — OOM killer, heap allocation failures
- Network failures — DNS resolution, proxy issues, firewall blocks
- Service container health check failures
- Rate limiting from external APIs or registries

**Annotations & Problem Matchers**
- `::error::`, `::warning::`, `::notice::` workflow commands
- Problem matcher output — file, line, column, message
- Step-level error vs warning annotations

### Analysis prompt

```
You are analyzing a GitHub Actions workflow run log. This log contains the output of a CI/CD job execution on GitHub Actions, including all steps from job setup through completion.

Focus your analysis on:

1. **Overall Job Health** — Did the job succeed or fail? Which specific step(s) failed? What was the exit code?

2. **Step-by-Step Analysis** — For each step, note:
   - Whether it succeeded or failed
   - Duration (look for step timing)
   - Any warnings or errors emitted
   - Steps that took unusually long

3. **Root Cause of Failures** — If the job failed:
   - Identify the FIRST step that failed (this is usually the root cause)
   - Distinguish between the actual error and cascading/downstream failures
   - Look for the specific error message, exit code, or exception
   - Check if the failure is in user code, a dependency, an action, or infrastructure

4. **Common Failure Patterns** — Check for:
   - Dependency installation failures (packages not found, version conflicts, auth failures)
   - Build errors (compilation failures, type errors, missing imports)
   - Test failures (assertion errors, timeouts, flaky tests)
   - Deployment issues (auth, permissions, target unavailable)
   - Resource exhaustion (disk space, memory, timeouts)
   - Secret/environment variable issues (empty values, misconfigured)
   - Action version problems (deprecated actions, breaking changes)
   - Network issues (DNS, proxy, firewall, rate limiting)

5. **Annotations** — Extract any `::error::` or `::warning::` workflow commands as they represent explicit problem signals from the workflow author or actions.

6. **Performance Observations** — Note any steps that seem unusually slow, cache misses that could be optimized, or unnecessary work being performed.

Provide actionable recommendations for fixing any failures and optimizing the workflow.
```

## self-hosted runner logs

## actions workflow yml file

