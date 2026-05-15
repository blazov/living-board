# GitHub Action Marketplace Checklist

## Completed (automated)
- [x] action.yml at repo root with name, description, author, branding
- [x] branding: icon=cpu, color=purple
- [x] 3 helper scripts in action/ directory
- [x] ACTION_README.md with Quick Start, Inputs, Outputs, Examples, Troubleshooting
- [x] Example workflow in .github/workflows/agent-cycle.example.yml
- [x] Input validation step with GitHub ::error:: annotations
- [x] if:always() on post-run steps for resilience
- [x] All files pushed to origin/master

## Remaining (manual, requires GitHub UI)
- [ ] Create a v1.0.0 tag and release on GitHub
  - Go to Releases > Draft a new release
  - Tag: v1.0.0, Target: master
  - Check "Publish this Action to the GitHub Marketplace"
  - Use ACTION_README.md content as the release body
- [ ] Create a v1 tag pointing to same commit (for major-version pinning)
- [ ] Add repo topics: github-actions, autonomous-agent, claude, supabase, ai-agent
