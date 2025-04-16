# Railway Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Application Fails to Start

**Check logs for specific errors:**
- Use `railway logs` command or check logs in Railway dashboard

**Solutions:**
- Verify all environment variables are set correctly
- Check if the OpenAI API key is valid
- Ensure gunicorn is properly installed

### 2. CORS Issues

**Symptoms:** Frontend can't connect to backend, browser console shows CORS errors

**Solutions:**
- Update allowed origins in server.py
- Check Railway URL is correctly set in frontend

### 3. Port Configuration Issues

**Symptoms:** 'Address already in use' errors or app not accessible

**Solutions:**
- Let Railway assign its own port with `PORT` env variable
- Remove hardcoded port in server.py

### 4. Environment Variable Problems

**Symptoms:** Missing credentials errors, API key issues, "openai.OpenAIError: The api_key client option must be set" errors

**Solutions:**
- Double-check all variables are set in Railway dashboard
- Make sure `OPENAI_API_KEY` is properly set (this is required)
- Escape special characters if needed
- Add `CDP_WALLET_DATA` variable with contents of wallet_data.txt
- After changing env variables, redeploy your service

### 5. Wallet Provider Errors

**Symptoms:** Wallet initialization failed errors

**Solutions:**
- Make sure MockWalletProvider is used in production mode
- Set `PRODUCTION=1` environment variable

### 6. Docker Build Errors with Poetry Files

**Symptoms:** Build fails with error: `failed to calculate checksum of ref: "/dexy/poetry.lock": not found`

**Solutions:**
- Fix the COPY commands in Dockerfile to correctly reference poetry files
- Use separate COPY commands for each file instead of combining them
- Make sure paths match the project structure (e.g., `COPY dexy/pyproject.toml ./pyproject.toml`)

## Checking Deployment Status

1. Visit `your-railway-url/status` to verify the server is running
2. Check logs for any initialization errors

