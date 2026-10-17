# View the interactive report on GitHub Pages

The published snapshot contains the displayed report fields and CSV downloads.
Credentials, raw ESPN snapshots and local data directories remain excluded.

Enable hosting once at:
https://github.com/erinyep/Rink-Lab-2027/settings/pages

1. Under **Build and deployment**, select **Deploy from a branch**.
2. Select **main**, folder **/docs**, then **Save**.
3. Wait for the Pages deployment, then open:
   https://erinyep.github.io/Rink-Lab-2027/report/

Until Pages is enabled, GitHub shows HTML source. The repository README includes
a static chart preview that GitHub can display directly.

This is a saved October 17 report, not a live feed. Refresh local forecast/report
inputs before publishing a later snapshot. Repackage explicitly with:

```sh
rink-lab.venv/bin/python scripts/prepare_github_report.py \
  --report reports/today/2026-10-17_quinn_publishing
```

Commit `docs/report/` after reviewing the new snapshot. Pushing changes to `main`
updates the site after Pages is enabled. No ESPN credentials belong in GitHub.

[GitHub Pages publishing documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
