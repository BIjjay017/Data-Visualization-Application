# Production Deployment Configuration

## URLs
- **Frontend (Vercel)**: https://data-visualization-application-1t87.vercel.app/
- **Backend (Render)**: https://data-visualization-application-1.onrender.com/

## Configuration Changes

### Frontend (Next.js on Vercel)

1. **Environment Variables**
   - Created `.env.production` with production API URL
   - Created `.env.local` for local development
   - Updated `Upload.js` to use `NEXT_PUBLIC_API_URL`

2. **Vercel Setup**
   - Add environment variable in Vercel dashboard:
     - Key: `NEXT_PUBLIC_API_URL`
     - Value: `https://data-visualization-application-1.onrender.com`

### Backend (FastAPI on Render)

1. **CORS Configuration**
   - Updated to allow Vercel domain
   - Supports both production and preview deployments

2. **Dependencies**
   - Ensure `requirements.txt` is up to date
   - Install: `PyPDF2`, `python-docx`, `openpyxl`, `xlrd`

## Deployment Steps

### Backend (Render)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Command**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables** (if needed)
   - Set in Render dashboard

### Frontend (Vercel)

1. **Push Changes**
   ```bash
   git add .
   git commit -m "Configure production deployment"
   git push
   ```

2. **Vercel Environment Variables**
   - Go to Vercel Dashboard → Project Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://data-visualization-application-1.onrender.com`

3. **Redeploy**
   - Vercel will auto-deploy on push
   - Or manually redeploy from dashboard

## Testing

1. Visit: https://data-visualization-application-1t87.vercel.app/
2. Upload a CSV/Excel/PDF/Word file
3. Verify data is processed by Render backend
4. Check for any CORS errors in browser console

## Troubleshooting

### CORS Errors
- Verify backend CORS includes Vercel domain
- Check Render logs for errors

### API Connection Issues
- Verify `NEXT_PUBLIC_API_URL` is set in Vercel
- Check Render backend is running
- Test backend directly: https://data-visualization-application-1.onrender.com/docs

### File Upload Errors
- Ensure all dependencies are installed on Render
- Check Render logs for Python errors
- Verify file size limits (50MB max)
