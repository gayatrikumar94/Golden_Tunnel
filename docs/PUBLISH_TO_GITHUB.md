# Publishing Golden Tunnel to GitHub (step by step)

You need: a free GitHub account (github.com), Git installed (git-scm.com), and Python 3.10+.

## 0. Check the project runs on YOUR computer first
```bash
cd golden-tunnel
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
python run_demo.py
pytest -q
```
If both work, you are ready.

## 1. One-time Git setup
```bash
git config --global user.name  "Gayatri Kumar"
git config --global user.email "gayatri.kumar94@gmail.com"
```
Use the same email as your GitHub account (or GitHub's "noreply" email in Settings > Emails if you prefer privacy).

## 2. Create the empty repository on GitHub
1. Log in to github.com, click **+** (top right) then **New repository**.
2. Repository name: `golden-tunnel`
3. Description: `Golden batch tunnel for biopharma batch monitoring (CHO fed-batch, simulated data)`
4. Choose **Public**.
5. **Do NOT** tick "Add a README", ".gitignore" or "license" (the project already has them).
6. Click **Create repository**. Keep the page open; it shows your repo URL.

## 3. Turn your folder into a Git repo and upload it
Run inside the `golden-tunnel` folder (replace `YOUR-USERNAME`):
```bash
git init
git add .
git status                       # review: no .venv or __pycache__ should be listed
git commit -m "Initial commit: golden tunnel batch monitoring"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/golden-tunnel.git
git push -u origin main
```
GitHub no longer accepts account passwords on the command line. When prompted, sign in through the browser window that opens, or use a **Personal Access Token** (Settings > Developer settings > Personal access tokens) as the password. Alternatively, install **GitHub Desktop**, choose *File > Add local repository*, then *Publish repository*.

## 4. Polish the repo page (this is what recruiters see)
- On the repo page click the gear next to **About**: add the description, and topics such as `bioprocess`, `biopharma`, `batch-monitoring`, `golden-batch`, `data-science`, `python`, `cho-cells`.
- Confirm the README renders with the images.
- Edit `README.md`: replace `<your-username>` in the clone command with your real username, commit, and push.
- Optional: **Pin** the repo on your GitHub profile (profile page > Customize your pins).

## 5. Update later
```bash
git add .
git commit -m "Describe what you changed"
git push
```

## 6. Add it to your resume / LinkedIn
Add the repo link to the project line, e.g. "Golden Tunnel Batch Monitoring (Python, pandas, matplotlib, GitHub)". Describe it as **simulated data**, and quote only results you reproduced by running the code.

## Troubleshooting
| Problem | Fix |
|---|---|
| `remote origin already exists` | `git remote set-url origin https://github.com/YOUR-USERNAME/golden-tunnel.git` |
| `failed to push ... fetch first` | You ticked "Add a README" on GitHub. Run `git pull origin main --allow-unrelated-histories`, resolve, then push. |
| `ModuleNotFoundError: golden_tunnel` | Run commands from inside the `golden-tunnel` folder, not a subfolder. |
| `AttributeError: numpy has no attribute trapezoid` | Upgrade NumPy: `pip install -U "numpy>=2.0"` |
