# Tracking Data + Git Workshop

**Triton Ball · UC San Diego**

Learn Git and GitHub by building a real football analytics pipeline: load SkillCorner broadcast tracking data with [kloppy](https://kloppy.pysport.org/), filter dynamic events down to off-ball runs, compute speed, acceleration, direction and distances from raw positions, then plot and animate the run. Every step ships as its own branch and pull request.

![workflow](https://img.shields.io/badge/workflow-branch%20%E2%86%92%20commit%20%E2%86%92%20PR%20%E2%86%92%20merge-blue)

## Before the workshop (15 minutes)

1. **Make a GitHub account** at [github.com](https://github.com) if you don't have one.
2. **Install Git** and check it works: `git --version`
   - macOS: `xcode-select --install` · Windows: [git-scm.com](https://git-scm.com/download/win) · Linux: `sudo apt install git`
3. **Install Python 3.10 or newer**: `python3 --version`
4. **Tell Git who you are** (use the email on your GitHub account):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@ucsd.edu"
   ```

## Get the code: fork, then clone

You will work in **your own copy** (a fork) of this repo, so you can push branches and merge pull requests without needing access to the original.

1. Click **Fork** (top right of this page) → keep "Copy the `main` branch only" checked → **Create fork**.
2. Clone **your fork** (replace `<your-username>`):
   ```bash
   git clone https://github.com/<your-username>/tracking-workshop.git
   cd tracking-workshop
   ```
3. Link the original repo as `upstream`, so you can pull fixes during the workshop:
   ```bash
   git remote add upstream https://github.com/zcochran27/tracking-workshop.git
   git remote -v        # origin = your fork, upstream = the workshop repo
   ```
4. Create a virtual environment and install the packages.
   A **virtual environment** (venv) is a private set of packages for this project only, so installing kloppy here can't break your other classes' code. The `.venv` folder is gitignored: you commit `requirements.txt`, never the environment.
   ```bash
   python3 -m venv .venv                     # Windows: python -m venv .venv
   source .venv/bin/activate                 # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python -m ipykernel install --user --name tracking-workshop --display-name "tracking-workshop"
   nbstripout --install                      # keeps notebook outputs out of your commits
   ```
   Your prompt now starts with `(.venv)`. Run `activate` again each time you open a new terminal.
5. Check everything works (needs internet, takes about a minute):
   ```bash
   python check_setup.py
   ```
6. Open the notebook and pick the **tracking-workshop** kernel (top-right corner):
   ```bash
   jupyter lab notebooks/workshop.ipynb
   ```
   Using VS Code instead? Open the notebook, click *Select Kernel* and choose `.venv` or **tracking-workshop**.

## What's in here

```
tracking-workshop/
├── notebooks/workshop.ipynb   # the guided notebook: start here
├── src/
│   ├── load.py                # loading helpers (complete, read it as an example)
│   ├── events.py              # Part 2: YOU write get_off_ball_runs
│   ├── kinematics.py          # Part 3: YOU write add_velocity
│   └── viz.py                 # Part 4: plot a frame, animate a sequence (complete)
├── check_setup.py
└── requirements.txt
```

Two functions marked `TODO` in `src/` are yours to write. The notebook has a **Check** cell after each one that tells you when it works.

## The workshop loop

Each part of the notebook ends with the same Git loop:

| Step | Command |
|---|---|
| 1. Start from an up-to-date main | `git switch main` then `git pull` |
| 2. Create a branch | `git switch -c feature/<part>` |
| 3. Write code | edit `src/*.py` and the notebook |
| 4. Commit | `git add <files>` then `git commit -m "What and why"` |
| 5. Push | `git push -u origin feature/<part>` |
| 6. Open a pull request | on GitHub: *Compare & pull request*, base `main` of **your fork** |
| 7. Review and merge | a neighbor leaves a comment, you **Merge** and **Delete branch** |

You write two functions and ship two pull requests. Everything else is complete and runs as-is.

| Part | You write | Branch |
|---|---|---|
| 1. Load and explore | nothing, run the cells | stay on `main` |
| 2. Find off-ball runs | `get_off_ball_runs` in `src/events.py` | `feature/off-ball-runs` → PR #1 |
| 3. Speed from positions | `add_velocity` in `src/kinematics.py` | `feature/kinematics` → PR #2 |
| 4. Plot and animate | nothing, run the cells | — |

> **Opening the PR:** GitHub may default the base to the *original* workshop repo. Change "base repository" to **your fork** so you merge into your own `main`.

## Git cheat sheet

| Command | What it does |
|---|---|
| `git status` | What changed, what is staged, which branch you're on |
| `git diff` | Line-by-line changes not yet staged |
| `git add <file>` | Stage a file for the next commit |
| `git commit -m "msg"` | Save a snapshot of the staged changes |
| `git log --oneline --graph` | History as a graph |
| `git switch <branch>` / `git switch -c <new>` | Move to a branch / create one |
| `git push -u origin <branch>` | Upload a branch to your fork |
| `git pull` | Download and merge new commits |
| `git pull upstream main` | Get fixes from the workshop repo |
| `git restore <file>` | Throw away uncommitted changes to a file |

Stuck in a merge conflict? Open the file, keep the lines you want, delete the `<<<<<<<`, `=======`, `>>>>>>>` markers, then `git add <file>` and `git commit`.

## Data

[SkillCorner Open Data](https://github.com/SkillCorner/opendata): A-League 2024/25 matches with broadcast tracking (10 fps), dynamic events and phases of play. The notebook streams the files from SkillCorner's GitHub, so nothing large is stored in this repo. If you build something with it, credit SkillCorner.

No internet? A facilitator can give you a local copy of a match folder; set `WORKSHOP_DATA_DIR` to the folder that contains `matches.json` before starting Jupyter.

## Keep learning

**Videos**
- [Friends of Tracking](https://www.youtube.com/@friendsoftracking755): YouTube channel with live sessions from people working in football analytics, many on tracking data.
- Laurie Shaw's tracking-data series on Friends of Tracking: [1. Getting started and visualizing](https://www.youtube.com/watch?v=8TrleFklEsE) · [2. Movies, velocities and physical reports](https://www.youtube.com/watch?v=VX3T-4lB2o0) · [3. Pitch control](https://www.youtube.com/watch?v=5X1cSehLg6s) · [4. EPV and decision-making](https://www.youtube.com/watch?v=KXSLKwADXKI)

**Code to follow along**
- [LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking): the code behind Laurie's videos (velocities, pitch control, EPV) on Metrica data.
- [Friends of Tracking on GitHub](https://github.com/Friends-of-Tracking-Data-FoTD): passing networks, Last Row tracking data, Soccermatics for Python.
- [SkillCorner Open Data tutorials](https://github.com/SkillCorner/opendata/tree/master/notebooks/tutorials): notebooks for dynamic events, phases of play, off-ball runs and tracking.

**Courses and articles**
- Soccermatics: [Pitch control](https://soccermatics.readthedocs.io/en/latest/lesson6/PitchControl.html) · [Off-ball runs](https://soccermatics.readthedocs.io/en/latest/lesson7/OffBallRuns.html) · [Physical data](https://soccermatics.readthedocs.io/en/latest/lesson8/PhysicalData.html)
- SkillCorner: [Visualising Off-Ball Runs](https://skillcorner.com/articles/skillcorner-open-data-4-visualising-off-ball-runs)

**More data and libraries**
- [Metrica Sports sample data](https://github.com/metrica-sports/sample-data): free anonymized tracking and event data.
- [kloppy](https://kloppy.pysport.org/) · [mplsoccer](https://mplsoccer.readthedocs.io/en/latest/) · [floodlight](https://github.com/floodlight-sports/floodlight)

## For facilitators

Reference solutions (`get_off_ball_runs` and `add_velocity` filled in) live on the `solutions` branch. Forks made with "Copy the `main` branch only" do not include it.
