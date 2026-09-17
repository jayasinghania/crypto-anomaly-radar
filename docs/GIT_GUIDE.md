# Git guide for this project

You don't need to know git deeply to contribute — just these commands,
used the same way every time.

## One-time setup

1. Install git: https://git-scm.com/downloads
2. Tell git who you are:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
3. Create a free GitHub account if you don't have one.
4. Get added as a collaborator on the repo (the repo owner does this from
   GitHub → Settings → Collaborators → Add people).
5. Clone the repo to your machine:
   ```bash
   git clone <repo-url>
   cd crypto-pulse
   ```

## Core concepts, one paragraph each

- **Repository (repo)** — the project folder, tracked by git. You have one
  as soon as you clone.
- **Commit** — a saved snapshot of your changes, with a message describing
  what changed.
- **Branch** — an independent line of work. `main` is the shared,
  always-working version. You never commit directly to `main` — you work
  on your own branch, then merge in through a pull request.
- **Remote** — the copy of the repo hosted on GitHub, called `origin` by
  default.
- **Pull request (PR)** — a request to merge your branch into `main`,
  which your teammate reviews before it's merged.

## The commands you'll actually use, every time

```bash
git checkout main                          # switch to the main branch
git pull                                   # get the latest changes from GitHub
git checkout -b yourname/phase1-fetcher    # create and switch to a new branch

# ... make your changes in your editor ...

git status                                 # see what you've changed
git add .                                  # stage all your changes
git commit -m "Add price fetcher for Binance API"   # save a snapshot
git push -u origin yourname/phase1-fetcher # upload your branch to GitHub
```

Then go to GitHub — it will prompt you to open a pull request from your
branch into `main`. Open it, ask your teammate to review, and merge once
approved.

## Our workflow for this project

1. Agree on the two sub-tasks for the phase.
2. Each person creates their own branch off `main` for their sub-task.
3. Work independently; commit often, with clear messages.
4. Push your branch and open a PR.
5. Review each other's PR — comment, ask questions, then merge.
6. Both run `git checkout main && git pull` before starting the next phase.

## If something goes wrong

- **Merge conflict** — git will tell you exactly which file(s) conflict.
  Open the file, find the `<<<<<<<`, `=======`, `>>>>>>>` markers, decide
  what the code should actually say, delete the markers, then `git add`
  and `git commit` again.
- **Committed to the wrong branch, or things feel messy** — stop and ask
  before running anything destructive (`git reset --hard`,
  `git push --force`). These can lose work permanently; it's always
  cheaper to ask first.

## Your first exercise (before any real code)

A zero-risk way to run the full cycle once before it matters:

1. `git checkout -b yourname/setup-practice`
2. Open `CONTRIBUTORS.md`, add your name on a new line.
3. `git add CONTRIBUTORS.md`
4. `git commit -m "Add myself to contributors"`
5. `git push -u origin yourname/setup-practice`
6. Open a pull request on GitHub into `main`, and get it merged.

Once that PR is merged, you've done everything you'll ever need to do in
this project, git-wise — every future phase is the same six steps with
different files.
