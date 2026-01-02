#!/bin/bash
# Force add everything including the renamed file
git add .
# Commit
git commit -m "Feat: Update Dashboard, Smart DCA, and Ticker Search"
# Push
git push
# Signal success
echo "Deployment script finished." > deploy_result.txt
