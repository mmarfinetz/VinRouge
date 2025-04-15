# Dexy Railway Deployment Guide

This guide explains how to deploy the Dexy backend to Railway and connect it to your existing frontend.

## Prerequisites

- A Railway account: [Sign up here](https://railway.app/login)
- Your OpenAI API key

## Deployment Steps

### 1. Create a New Project in Railway

1. Log in to your Railway account
2. Click "New Project" and select "Deploy from GitHub repo"
3. Connect your GitHub account and select the VinRouge repository
4. Railway will automatically detect the Python project

### 2. Configure Environment Variables

Add the following environment variables in the Railway dashboard:

- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: 5050 (Railway will automatically assign a port, but we use this to match our code)
- `PYTHONUNBUFFERED`: 1 (Ensures logs are printed immediately)

### 3. Configure Deployment Settings

1. In the Railway dashboard, go to Settings
2. Under "Start Command", enter: `gunicorn server:app`
3. Verify the Python version matches what's in the runtime.txt file (3.10.0)

### 4. Deploy and Verify Backend

1. Click "Deploy" (Railway may automatically deploy when you add the GitHub repository)
2. Once deployment is complete, click on your deployment and find the generated URL
3. Test the backend by visiting `<your-railway-url>/status` - you should see a JSON response: `{"status": "AgentKit is running"}`

### 5. Update Frontend Configuration

After successful deployment, copy your Railway URL and update the `API_BASE_URL` value in the `win97.js` file:

```javascript
function getApiBaseUrl() {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return 'https://your-railway-url-here'; // Replace with your actual Railway URL
    }
    return '';
}
```

### 6. Verify Frontend-Backend Integration

1. Visit your deployed frontend (on Vercel/Replit)
2. Try using the chat feature 
3. Test the analysis tools to ensure they're communicating with the backend

## Troubleshooting

### API Connection Issues

- Check browser console for CORS errors
- Verify the Railway URL is correct in the frontend code
- Check Railway logs for any backend errors

### Railway Deployment Issues

- Check the Railway deployment logs
- Verify all required environment variables are set
- Make sure the `requirements.txt` file includes all necessary dependencies

### OpenAI API Issues

- Verify your API key is correct
- Check if your account has sufficient credits
- Look for rate limiting errors in the logs

## Scaling Up

- Railway offers auto-scaling options under "Settings > Scaling"
- Consider enabling auto-scaling if you expect high traffic

## Monitoring

- Use Railway's built-in monitoring tools to track:
  - CPU and memory usage
  - Request volume and latency
  - Error rates

## Support

If you encounter any issues, contact the VinRouge team or refer to:

- [Railway Documentation](https://docs.railway.app/)
- [Flask Documentation](https://flask.palletsprojects.com/)