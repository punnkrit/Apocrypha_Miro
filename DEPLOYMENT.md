# Streamlit Cloud Deployment Guide

This guide will help you deploy your Apocrypha Miro app to Streamlit Cloud.

## Prerequisites

- Node.js 16+ installed locally
- Git repository set up
- Streamlit Cloud account

## Step 1: Build the Frontend

The `diagram-prototype/dist` folder **must be committed to your repository** for Streamlit Cloud deployment, as Streamlit Cloud doesn't have Node.js available to build the frontend.

Simply run:

```bash
cd diagram-prototype
npm install  # Only needed first time or after package.json changes
npm run build
cd ..
```

That's it! The `dist` folder will be created in `diagram-prototype/dist/`.

## Step 2: Verify the Build

Check that the `diagram-prototype/dist` folder exists and contains:
- `index.html`
- `assets/` directory with JS and CSS files

```bash
ls diagram-prototype/dist/
```

## Step 3: Commit the Build to Git

**Important**: The `dist` folder must be in your git repository for Streamlit Cloud.

```bash
# Check git status to see if dist is tracked
git status

# If dist folder is not tracked, add it explicitly
git add diagram-prototype/dist/
git add diagram-prototype/dist/**

# Commit
git commit -m "Add frontend build for Streamlit Cloud deployment"

# Push to your repository
git push
```

### Troubleshooting: If dist is still ignored

If git is still ignoring the `dist` folder, check your `.gitignore`:

1. Ensure these lines exist in `.gitignore`:
   ```
   !diagram-prototype/dist/
   !diagram-prototype/dist/**
   ```

2. Force add the directory:
   ```bash
   git add -f diagram-prototype/dist/
   ```

3. Verify it's tracked:
   ```bash
   git ls-files diagram-prototype/dist/
   ```

## Step 4: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository: `punnkrit/Apocrypha_Miro`
4. Set the main file path: `app.py`
5. Add your secrets (if needed):
   - Go to "Settings" → "Secrets"
   - Add:
     ```toml
     OPENAI_API_KEY = "sk-your-key-here"
     ```
6. Click "Deploy"

## Step 5: Verify Deployment

After deployment, check:
- The app loads without errors
- The diagram board renders correctly
- The chat interface works

## Rebuilding After Frontend Changes

Whenever you make changes to the frontend (`diagram-prototype/src/`):

1. Rebuild: `python build_frontend.py` or `cd diagram-prototype && npm run build`
2. Commit the updated `dist` folder
3. Push to your repository
4. Streamlit Cloud will automatically redeploy

## Local Development

For local development with hot-reloading:

1. In one terminal:
   ```bash
   cd diagram-prototype
   npm run dev
   ```

2. In another terminal, set the environment variable and run Streamlit:
   ```bash
   # Windows PowerShell
   $env:MIRO_DEV_URL="http://localhost:5173"
   streamlit run app.py

   # Linux/Mac
   export MIRO_DEV_URL=http://localhost:5173
   streamlit run app.py
   ```

## Troubleshooting

### Error: "No such component directory"

- **Cause**: The `diagram-prototype/dist` folder is missing or not committed to git
- **Fix**: 
  1. Run `python build_frontend.py`
  2. Verify `git ls-files diagram-prototype/dist/` shows files
  3. If not, use `git add -f diagram-prototype/dist/`
  4. Commit and push

### Error: "Build directory exists but is missing index.html"

- **Cause**: The build didn't complete successfully
- **Fix**: 
  1. Delete `diagram-prototype/dist` folder
  2. Run `cd diagram-prototype && npm run build`
  3. Verify `index.html` exists
  4. Commit and push

### Component not updating after changes

- **Cause**: Streamlit Cloud is using cached build
- **Fix**: 
  1. Rebuild the frontend
  2. Commit the new `dist` folder
  3. Push to trigger redeployment
  4. Clear browser cache if needed

