# Quick Deployment Checklist

## Before Deploying to Streamlit Cloud

1. **Build the frontend:**
   ```bash
   cd diagram-prototype
   npm install  # Only needed first time
   npm run build
   cd ..
   ```

2. **Verify the build exists:**
   ```bash
   ls diagram-prototype/dist/index.html
   ```

3. **Add and commit the dist folder:**
   ```bash
   git add diagram-prototype/dist/
   git commit -m "Add frontend build for deployment"
   git push
   ```

4. **Deploy to Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Connect your repo: `punnkrit/Apocrypha_Miro`
   - Main file: `app.py`
   - Add secrets if needed (OPENAI_API_KEY)

## The Problem

Streamlit Cloud doesn't have Node.js, so it can't build your frontend. The `diagram-prototype/dist` folder **must be committed to git**.

## The Fix

I've updated:
- ✅ `streamlit_miro_component/__init__.py` - Better error messages
- ✅ `diagram-prototype/.gitignore` - Now allows `dist/` folder

## Next Steps

1. Run `cd diagram-prototype && npm run build` to build
2. Commit the `diagram-prototype/dist/` folder
3. Push to GitHub
4. Deploy on Streamlit Cloud

