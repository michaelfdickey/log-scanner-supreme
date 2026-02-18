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

## PRIORITY 1: SCALING STATUS (report this FIRST)
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

## PRIORITY 2: Standard analysis
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

## Workflow run log

## self-hosted runner logs

## actions workflow yml file

