# Metrics card — maintenance & anti-spam runbook

Local reference (git-ignored, not published). If the daily auto-commits from the
`Metrics build` Action ever feel like too much, use the ready-made fixes below.

Reminder of current behaviour:
- The Action runs daily (cron `0 4 * * *`) + on every push + manually.
- It commits **only when a stat actually changed** (`git commit ... || echo "No changes"`).
- Commits are authored by `github-actions-bot` → they do **NOT** count toward your
  green contribution graph. At most **1 commit/day**, only on days your stats moved.

---

## 1. Update LESS often (fewer commits)

Edit `.github/workflows/build.yaml`, the `schedule:` block. Replace the cron line:

```yaml
schedule:
  # Daily 4:00 UTC  (current)
  - cron: "0 4 * * *"

  # --- pick ONE of these instead ---
  # Weekly, Sundays 4:00 UTC
  # - cron: "0 4 * * 0"
  # Monthly, 1st of the month 4:00 UTC
  # - cron: "0 4 1 * *"
```

Then commit + push:
```bash
git add .github/workflows/build.yaml
git commit -m "Slow down stats refresh"
git push
```

---

## 2. Update ONLY when I choose (no schedule at all)

Remove the whole `schedule:` block so it runs only on push / manual "Run workflow":

```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:
```

---

## 3. Pause auto-updates entirely (no code change)

GitHub → repo → **Actions** tab → left sidebar **Metrics build** →
top-right **⋯ → Disable workflow**. Re-enable the same way anytime.

---

## 4. Clean up accumulated bot commits (squash history)

If a pile of "Update GitHub stats" commits has built up and you want them gone,
squash them into one. Replace `N` with how many recent commits to collapse:

```bash
cd ~/Documents/purnasth
git reset --soft HEAD~N     # keep the files, drop the N commit records
git commit -m "Update GitHub stats"
git push --force-with-lease
```

Or squash every bot commit since a known-good commit `<SHA>`:
```bash
git reset --soft <SHA>
git commit -m "Update GitHub stats"
git push --force-with-lease
```

> `--force-with-lease` rewrites history — safe here because it's your own profile
> repo and you're the only committer. Don't do this on shared repos.

---

## 5. Regenerate the ASCII portrait (if you change your photo)

```bash
cd ~/Documents/purnasth/metrics
python3 generate_portrait.py purna-shrestha.png --invert --contrast 1.6 \
        --width 82 --char-aspect 0.565 --line-height 8.5 --start-y 55
```

---

## 6. Token expired? (stats stop updating)

The fine-grained PAT has an expiry. When it lapses, the Action fails on the API call.
Fix: GitHub → Settings → Developer settings → Fine-grained tokens → regenerate →
update the repo secret `ACCESS_TOKEN` (Settings → Secrets and variables → Actions).
