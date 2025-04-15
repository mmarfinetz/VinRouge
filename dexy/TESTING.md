# Dexy Testing Guide

This guide provides step-by-step instructions for testing the Dexy application after deployment, ensuring that both front-end and back-end components are functioning correctly.

## Prerequisites

- Access to the deployed front-end URL (Vercel/Replit)
- Access to the deployed back-end URL (Railway)
- Web browser with developer tools (Chrome/Firefox recommended)

## Backend Status Check

1. Open a browser and navigate to: `https://your-railway-url/status`
2. Verify you receive the following response:
   ```json
   {"status": "AgentKit is running"}
   ```
3. If this fails, check the Railway logs for errors

## Front-end Functionality Tests

### Basic UI Tests

1. Load the front-end URL
2. Verify the Windows 97-themed interface loads properly
3. Check that all desktop icons are visible (Dexy, Analysis, Settings, Help)
4. Click each icon to ensure the corresponding windows open
5. Test window controls (minimize, maximize, close) to ensure they work

### Chat Functionality Tests

1. Open the Dexy Chat window
2. Type a simple question: "What is the current price of Bitcoin?"
3. Verify the message is sent and a response is received
4. Check for any errors in the browser's developer console

### Analysis Tool Tests

#### Quick Analysis Test
1. Open the Analysis window
2. Select "Bitcoin" from the dropdown
3. Click "Run Analysis"
4. Verify loading indicator appears
5. Ensure analysis results are displayed with no errors

#### Technical Indicators Test
1. In the Analysis window, click the "Technical Indicators" tab
2. Select "Ethereum" and "30 Days"
3. Ensure all indicator checkboxes are selected
4. Click "Calculate Indicators"
5. Verify indicators load and display properly

#### Whale Analysis Test
1. In the Analysis window, click the "Whale Activity" tab
2. Select "Bitcoin" 
3. Click "Analyze Whale Activity"
4. Verify the risk score and signals display correctly

### Wallet Connection Test

1. Open the Settings window
2. Click the "Connect" button next to CDP Wallet
3. Verify connection status updates (either with wallet address or error message)

## Cross-browser Testing

Test the application in at least:
- Google Chrome
- Mozilla Firefox
- Microsoft Edge

## Mobile Responsiveness Testing

Though the UI is desktop-oriented, verify basic functionality on:
- iPhone (Safari)
- Android (Chrome)

## Network Request Monitoring

1. Open browser developer tools (F12) and go to the Network tab
2. Interact with the application while monitoring network requests
3. Check that API calls to `/query`, `/analyze`, `/technical`, and `/whale` endpoints return 200 status codes
4. Verify response data structure matches what the front-end expects

## Error Handling Tests

1. Test with a weak internet connection (throttle in dev tools)
2. Verify appropriate error messages are displayed
3. Disconnect from internet entirely and test error recovery
4. Enter invalid inputs where possible to test validation

## Session Persistence Testing

1. Change settings in the Settings window
2. Refresh the page
3. Verify settings are persisted (via localStorage)

## Common Issues and Solutions

### CORS Errors
If you see CORS errors in the console:
- Verify the backend has CORS properly configured
- Check that the Railway URL is correctly specified in the front-end

### Slow Responses
If API responses are slow:
- Check Railway dashboard for resource utilization
- Monitor OpenAI API response times
- Consider scaling up the Railway instance

### Missing Data
If analysis tools return empty or incomplete results:
- Check browser console for JavaScript errors
- Verify API responses in Network tab
- Check backend logs for errors in data processing

## Reporting Issues

When reporting bugs, include:
1. Steps to reproduce
2. Expected vs. actual behavior
3. Browser and OS details
4. Screenshots of errors
5. Console logs if applicable

Submit issues to the VinRouge team via GitHub or the designated communication channel.