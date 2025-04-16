# VinRouge Railway Deployment Steps

Follow these exact steps to deploy your application to Railway:

## 1. Install Railway CLI (Optional)

If you want to deploy from your local machine:

```bash
npm i -g @railway/cli
railway login
```

## 2. Set Up Railway Project (Web Interface)

1. Log in to your Railway account at https://railway.app/dashboard
2. Click "New Project" 
3. Choose "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository
5. Railway will automatically detect the Dockerfile

## 3. Set Required Environment Variables

In the Railway dashboard:
1. Go to your project
2. Click the "Variables" tab
3. Add the following variables:
   - `OPENAI_API_KEY`: Your OpenAI API key (REQUIRED)
   - `PORT`: 8080 (matches Dockerfile and gunicorn.conf.py)
   - `PYTHONUNBUFFERED`: 1
   - `PRODUCTION`: 1
   - (Optional) `CDP_WALLET_DATA`: If you want a persistent wallet

## 4. Deploy Your Application

Railway will auto-deploy when variables are set. If not:
1. Go to the "Deployments" tab
2. Click "Deploy Now"

## 5. Verify Deployment

1. Once deployed, Railway will provide a public URL
2. Visit `YOUR_URL/status` to verify the server is running
3. You should see: `{"status": "AgentKit is running"}`

## Troubleshooting

If you encounter issues:

1. Check Railway logs in the Deployments tab
2. Verify all environment variables are set properly
3. Ensure OPENAI_API_KEY is valid
4. Check for any PORT configuration issues

## Additional Configuration (Optional)

- Set up custom domain in Settings > Domains
- Configure auto-scaling in Settings > Scaling
- Set up monitoring in the Metrics tab

## Testing the API

Use these endpoints to verify functionality:
- `/status`: Check server health
- `/query`: Post a message to test the chatbot
- `/analyze`: Test crypto analysis (POST with token_id parameter)
- `/wallet`: Get wallet information

## Updating Your Deployment

Any changes pushed to your GitHub repository will automatically trigger a new deployment if you set up continuous deployment. 