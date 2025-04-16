# Railway Environment Variables Setup

To deploy the Dexy backend to Railway, you need to set up the following environment variables in your Railway project:

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (REQUIRED) | sk-abc123... |
| `PORT` | The port for the server to listen on | 5050 |
| `PYTHONUNBUFFERED` | Ensures Python output is sent straight to terminal | 1 |
| `PRODUCTION` | Indicates production environment | 1 |

## Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CDP_WALLET_DATA` | Wallet data for blockchain interactions (optional when using on-demand generation) | {"wallet_id": "xxx", "seed": "yyy", "network_id": "base-sepolia"} |

## IMPORTANT
The `OPENAI_API_KEY` is *required* for the application to function properly. Without this variable set, the application will fail to initialize and display error messages.

## How to Set Environment Variables

1. Go to your Railway dashboard: https://railway.app/dashboard
2. Click on your project
3. Navigate to the "Variables" tab
4. Add each variable one by one:
   - Click "New Variable"
   - Enter the variable name (e.g., `OPENAI_API_KEY`)
   - Enter the value
   - Click "Add"

## Wallet Management Options

You have three options for managing CDP wallets:

### Option 1: Use Existing Wallet Data
Set the `CDP_WALLET_DATA` environment variable with the contents of your local `dexy/wallet_data.txt` file. This will use a consistent wallet across all sessions.

### Option 2: Auto-Generate on First Deployment
If you don't set `CDP_WALLET_DATA`, the system will generate a new wallet during the first deployment. You can retrieve this wallet data from the deployment logs and add it as an environment variable for future deployments if you want to keep using the same wallet.

### Option 3: On-Demand Wallet Generation (Recommended)
Don't set `CDP_WALLET_DATA` and use the built-in on-demand wallet generation feature. With this approach:
- Users can generate new wallets directly from the app's interface
- Wallets are generated on-demand when needed
- No persistent wallet data is stored on the server
- Each user interaction that requires a wallet will create a fresh one

This is the most production-ready approach as it doesn't require storing sensitive wallet data in environment variables.

## Verifying Deployment

After setting all environment variables and deploying:

1. Railway will automatically deploy your application
2. Visit `https://your-railway-url/status` to verify the server is running
3. The response should be: `{"status": "AgentKit is running"}`

If you encounter errors, check the [RAILWAY_TROUBLESHOOTING.md](RAILWAY_TROUBLESHOOTING.md) file. 