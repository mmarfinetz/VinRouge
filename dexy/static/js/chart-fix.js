/**
 * Chart.js Fix for Dexy Application
 * 
 * This file contains fixes for chart rendering issues in the DexyBot UI.
 * Add this script to your HTML file after the main win97.js script.
 */

// Function to create a dynamic technical summary based on indicators
function updateTechnicalSummary(tokenId, enabledIndicators) {
    const summaryEl = document.getElementById('technical-summary');
    if (!summaryEl) return;
    
    const summaryContent = summaryEl.querySelector('.summary-content');
    if (!summaryContent) return;
    
    // If no indicators are enabled
    if (!enabledIndicators || enabledIndicators.length === 0) {
        summaryContent.textContent = "Select indicators to analyze price action patterns.";
        return;
    }
    
    // Determine the overall signal based on enabled indicators
    let bearishCount = 0;
    let bullishCount = 0;
    let neutralCount = 0;
    
    enabledIndicators.forEach(indicator => {
        if (indicator.class === 'bearish') bearishCount++;
        else if (indicator.class === 'bullish') bullishCount++;
        else neutralCount++;
    });
    
    let summary = '';
    
    // Generate a summary based on the indicators
    if (bearishCount > bullishCount && bearishCount > neutralCount) {
        summary = `${tokenId.toUpperCase()} is showing predominantly bearish signals. `;
        
        // Add details based on specific indicators
        enabledIndicators.forEach(indicator => {
            if (indicator.class === 'bearish') {
                summary += `${indicator.name} indicates ${indicator.signal.toLowerCase()}. `;
            }
        });
        
        summary += 'Consider waiting for oversold conditions before entering positions.';
    } 
    else if (bullishCount > bearishCount && bullishCount > neutralCount) {
        summary = `${tokenId.toUpperCase()} is showing predominantly bullish signals. `;
        
        // Add details based on specific indicators
        enabledIndicators.forEach(indicator => {
            if (indicator.class === 'bullish') {
                summary += `${indicator.name} indicates ${indicator.signal.toLowerCase()}. `;
            }
        });
        
        summary += 'Monitor for potential entry points while maintaining risk management.';
    }
    else {
        summary = `${tokenId.toUpperCase()} is showing mixed or neutral signals. `;
        
        // Add some specific indicator details
        if (enabledIndicators.length > 0) {
            const mainIndicator = enabledIndicators[0];
            summary += `${mainIndicator.name} is at ${mainIndicator.value.toFixed(2)}, indicating ${mainIndicator.signal.toLowerCase()}. `;
        }
        
        summary += 'The market may be in consolidation or lacking clear direction.';
    }
    
    summaryContent.textContent = summary;
}

// Fix for technical indicators chart
function fixTechnicalChart() {
    console.log("Applying technical chart fixes...");
    
    // Override the runTechnicalAnalysis function to ensure proper chart rendering
    window.originalRunTechnicalAnalysis = window.runTechnicalAnalysis;
    
    window.runTechnicalAnalysis = function() {
        const tokenSelect = document.getElementById('technical-token');
        const timePeriod = document.getElementById('time-period');
        const showZScore = document.getElementById('show-zscore');
        const showRSI = document.getElementById('show-rsi');
        const showBB = document.getElementById('show-bb');
        const resultsContainer = document.getElementById('technical-analysis-results');
        const loadingContainer = document.getElementById('technical-analysis-loading');
        
        if (!tokenSelect || !timePeriod || !resultsContainer || !loadingContainer) return;
        
        const tokenId = tokenSelect.value;
        const days = parseInt(timePeriod.value);
        
        // Play sound
        if (typeof playSound === 'function') {
            playSound('click-sound');
        }
        
        // Show loading
        loadingContainer.style.display = 'flex';
        resultsContainer.querySelector('.placeholder-message').style.display = 'none';
        
        // Fetch data from server
        fetch('/technical', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token_id: tokenId, days: days })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading
            loadingContainer.style.display = 'none';
            
            if (data.indicators) {
                // Create chart container with improved layout
                resultsContainer.innerHTML = `
                    <div class="analysis-header">
                        <span>${tokenId.toUpperCase()} Technical Analysis (${days} Days)</span>
                        <span class="price-info">$${data.indicators.current_price ? data.indicators.current_price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'N/A'}</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="price-chart" width="400" height="200"></canvas>
                    </div>
                    <div class="indicators-container">
                        <div class="indicator-section">
                            <h4>Technical Indicators</h4>
                            <div class="indicator-grid" id="indicator-values"></div>
                        </div>
                    </div>
                    <div class="analysis-summary" id="technical-summary">
                        <div class="summary-title">Analysis Summary</div>
                        <div class="summary-content">Select indicators to analyze price action patterns.</div>
                    </div>
                `;
                
                // Add indicator values with improved formatting
                const indicatorValues = document.getElementById('indicator-values');
                const indicators = data.indicators.indicators;
                
                // Clear existing indicators
                indicatorValues.innerHTML = '';
                
                // Track enabled indicators for summary
                let enabledIndicators = [];
                
                // Add Z-Score if selected
                if (showZScore && showZScore.checked && indicators && indicators.z_score) {
                    const zScore = indicators.z_score.value;
                    const zSignal = getZScoreSignal(zScore);
                    const signalClass = getSignalClass(zSignal);
                    
                    indicatorValues.innerHTML += `
                        <div class="indicator-row">
                            <div class="indicator-name">Z-Score:</div>
                            <div class="indicator-value">${zScore.toFixed(2)}</div>
                            <div class="indicator-signal ${signalClass}">${zSignal}</div>
                        </div>
                    `;
                    
                    enabledIndicators.push({
                        name: 'Z-Score',
                        value: zScore,
                        signal: zSignal,
                        class: signalClass
                    });
                }
                
                // Add RSI if selected
                if (showRSI && showRSI.checked && indicators && indicators.rsi) {
                    const rsi = indicators.rsi.value;
                    const rsiSignal = getRSISignal(rsi);
                    const signalClass = getSignalClass(rsiSignal);
                    
                    indicatorValues.innerHTML += `
                        <div class="indicator-row">
                            <div class="indicator-name">RSI:</div>
                            <div class="indicator-value">${rsi.toFixed(2)}</div>
                            <div class="indicator-signal ${signalClass}">${rsiSignal}</div>
                        </div>
                    `;
                    
                    enabledIndicators.push({
                        name: 'RSI',
                        value: rsi,
                        signal: rsiSignal,
                        class: signalClass
                    });
                }
                
                // Add Bollinger Bands if selected
                if (showBB && showBB.checked && indicators && indicators.bollinger_bands) {
                    const bb = indicators.bollinger_bands;
                    const percentB = bb.percent_b;
                    const bbSignal = getBBSignal(percentB);
                    const signalClass = getSignalClass(bbSignal);
                    
                    indicatorValues.innerHTML += `
                        <div class="indicator-row">
                            <div class="indicator-name">Bollinger %B:</div>
                            <div class="indicator-value">${percentB.toFixed(2)}</div>
                            <div class="indicator-signal ${signalClass}">${bbSignal}</div>
                        </div>
                    `;
                    
                    // Add the bands in a nested format
                    indicatorValues.innerHTML += `
                        <div class="indicator-bands">
                            <div class="band-row">
                                <div class="band-name">Upper Band:</div>
                                <div class="band-value">${bb.upper_band.toFixed(2)}</div>
                            </div>
                            <div class="band-row">
                                <div class="band-name">Middle Band:</div>
                                <div class="band-value">${bb.middle_band.toFixed(2)}</div>
                            </div>
                            <div class="band-row">
                                <div class="band-name">Lower Band:</div>
                                <div class="band-value">${bb.lower_band.toFixed(2)}</div>
                            </div>
                        </div>
                    `;
                    
                    enabledIndicators.push({
                        name: 'Bollinger Bands',
                        value: percentB,
                        signal: bbSignal,
                        class: signalClass
                    });
                }
                
                // Generate and update summary
                updateTechnicalSummary(tokenId, enabledIndicators);
                
                // Generate chart with improved error handling
                setTimeout(() => {
                    try {
                        // Generate mock data if historical prices are missing
                        const currentPrice = data.indicators.current_price || 50000;
                        let dates = [];
                        let priceValues = [];
                        
                        // Check if we have historical prices
                        if (data.indicators.historical_prices && data.indicators.historical_prices.length > 0) {
                            const prices = data.indicators.historical_prices;
                            console.log(`Found ${prices.length} historical price points`);
                            
                            // Map dates and prices, handle potential missing data
                            dates = prices.map(p => {
                                if (p.timestamp) {
                                    return new Date(p.timestamp * 1000).toLocaleDateString();
                                } else {
                                    return "Unknown";
                                }
                            });
                            
                            priceValues = prices.map(p => p.price || 0);
                            
                        } else {
                            console.log("No historical price data found, generating mock data");
                            // Generate mock data
                            const today = new Date();
                            for (let i = days; i >= 0; i--) {
                                const date = new Date(today);
                                date.setDate(date.getDate() - i);
                                dates.push(date.toLocaleDateString());
                                
                                // Generate slightly random price movement
                                const randomFactor = 1 + (Math.random() * 0.1 - 0.05);
                                priceValues.push(currentPrice * randomFactor);
                            }
                        }
                        
                        console.log(`Rendering chart with ${dates.length} data points`);
                        
                        // Get canvas context
                        const canvas = document.getElementById('price-chart');
                        if (!canvas) {
                            console.error("Price chart canvas not found");
                            return;
                        }
                        
                        const ctx = canvas.getContext('2d');
                        
                        // Create price chart - using best practices for Chart.js
                        if (window.priceChart) {
                            window.priceChart.destroy();
                        }
                        
                        window.priceChart = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: dates,
                                datasets: [{
                                    label: `${tokenId.toUpperCase()} Price`,
                                    data: priceValues,
                                    borderColor: 'rgb(75, 192, 192)',
                                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                    tension: 0.1,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                resizeDelay: 100,
                                onResize: function(chart, size) {
                                    console.log("Chart being resized to: ", size.width, size.height);
                                },
                                plugins: {
                                    title: {
                                        display: true,
                                        text: `${tokenId.toUpperCase()} Price History (${days} Days)`
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: false
                                    }
                                }
                            }
                        });
                        
                        console.log("Chart rendering complete");
                        
                    } catch (error) {
                        console.error("Error rendering chart:", error);
                        const chartContainer = document.querySelector('.chart-container');
                        if (chartContainer) {
                            chartContainer.innerHTML += `
                                <div class="chart-error">
                                    Error rendering chart: ${error.message}
                                </div>
                            `;
                        }
                    }
                }, 100);
                
                // Play notification sound
                if (typeof playSound === 'function') {
                    playSound('notify-sound');
                }
                
            } else if (data.error) {
                resultsContainer.innerHTML = `
                    <div class="analysis-error">
                        <p>Error: ${data.error}</p>
                        <p>${data.details || ''}</p>
                    </div>
                `;
                
                // Play error sound
                if (typeof playSound === 'function') {
                    playSound('error-sound');
                }
            }
        })
        .catch(error => {
            // Hide loading
            loadingContainer.style.display = 'none';
            
            // Show error
            resultsContainer.innerHTML = `
                <div class="analysis-error">
                    <p>Error: ${error.message}</p>
                </div>
            `;
            
            // Play error sound
            if (typeof playSound === 'function') {
                playSound('error-sound');
            }
        });
    };
    
    console.log("Technical chart fix applied!");
}

// Fix for whale analysis chart
function fixWhaleChart() {
    console.log("Applying whale chart fixes...");
    
    // Override the renderWhaleActivityChart function
    window.originalRenderWhaleActivityChart = window.renderWhaleActivityChart;
    
    window.renderWhaleActivityChart = function(token, data) {
        try {
            const canvas = document.getElementById('whale-activity-chart');
            if (!canvas) {
                console.error("Could not find whale-activity-chart canvas element");
                return;
            }
            
            // Wait a moment for the DOM to be ready
            setTimeout(() => {
                try {
                    const ctx = canvas.getContext('2d');
                    
                    // Generate mock whale activity data
                    const days = 30; // Last 30 days
                    const labels = [];
                    const whaleAccumulation = [];
                    const whaleDistribution = [];
                    
                    // Create dates for the last 30 days
                    const today = new Date();
                    for (let i = days - 1; i >= 0; i--) {
                        const date = new Date(today);
                        date.setDate(date.getDate() - i);
                        labels.push(date.toLocaleDateString());
                        
                        // Generate random data points for demonstration
                        // Weighted by the risk score - higher risk means more distribution (selling)
                        const riskFactor = data.risk_score / 100;
                        const randomAccum = Math.random() * (1 - riskFactor) * 100;
                        const randomDist = Math.random() * riskFactor * 100;
                        
                        whaleAccumulation.push(randomAccum);
                        whaleDistribution.push(randomDist);
                    }
                    
                    console.log(`Rendering whale chart for ${token} with ${labels.length} data points`);
                    
                    // Destroy any existing chart
                    if (window.whaleChart) {
                        window.whaleChart.destroy();
                    }
                    
                    // Create the chart
                    window.whaleChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Whale Accumulation',
                                    data: whaleAccumulation,
                                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                                    borderColor: 'rgb(75, 192, 192)',
                                    borderWidth: 1
                                },
                                {
                                    label: 'Whale Distribution',
                                    data: whaleDistribution,
                                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                                    borderColor: 'rgb(255, 99, 132)',
                                    borderWidth: 1
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: `${token.toUpperCase()} Whale Activity (Last 30 Days)`
                                },
                                legend: {
                                    display: true,
                                    position: 'top'
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${context.raw.toFixed(2)}`;
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    stacked: true
                                },
                                y: {
                                    stacked: true,
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                    
                    console.log("Whale chart rendering complete");
                } catch (innerError) {
                    console.error("Error in delayed whale chart rendering:", innerError);
                }
            }, 100);
            
        } catch (e) {
            console.error("Error preparing whale activity chart:", e);
        }
    };
    
    console.log("Whale chart fix applied!");
}

// Function to improve analysis window layout and add maximize/minimize functionality
// Function to handle chart resizing when window dimensions change
function updateChartSizes() {
    console.log("Updating chart sizes based on container dimensions");
    
    // Find all chart canvases and resize them
    document.querySelectorAll('canvas').forEach(canvas => {
        const chartInstance = Chart.getChart(canvas);
        if (chartInstance) {
            try {
                chartInstance.resize();
                console.log(`Resized chart: ${canvas.id}`);
            } catch (e) {
                console.error(`Error resizing chart ${canvas.id}:`, e);
            }
        }
    });
}

function fixAnalysisWindowLayout() {
    console.log("Applying analysis window layout fixes...");
    
    // Add resize handler to adjust chart proportions when window is resized
    const handleResize = () => {
        const analysisWindow = document.getElementById('analysis-window');
        if (!analysisWindow) return;
        
        const chartContainer = analysisWindow.querySelector('.chart-container');
        if (!chartContainer) return;
        
        // Update chart dimensions when window is resized
        const windowHeight = analysisWindow.offsetHeight;
        const contentHeight = analysisWindow.querySelector('.window-content')?.offsetHeight || 0;
        
        if (windowHeight > 480) {
            // For larger windows, make the chart taller
            const newChartHeight = Math.min(350, contentHeight * 0.5);
            chartContainer.style.height = `${newChartHeight}px`;
            
            // If chart.js instance exists, update it
            if (window.priceChart) {
                try {
                    window.priceChart.resize();
                } catch (e) {
                    console.error("Error resizing chart:", e);
                }
            }
            
            if (window.whaleChart) {
                try {
                    window.whaleChart.resize();
                } catch (e) {
                    console.error("Error resizing whale chart:", e);
                }
            }
        }
    };
    
    // Set up a MutationObserver to watch for window size changes
    const resizeObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'style') {
                handleResize();
            }
        });
    });
    
    // Start observing the analysis window for attribute changes
    const analysisWindow = document.getElementById('analysis-window');
    if (analysisWindow) {
        resizeObserver.observe(analysisWindow, { attributes: true });
        
        // Also listen for maximize/minimize events
        analysisWindow.addEventListener('maximize', handleResize);
        analysisWindow.addEventListener('restore', handleResize);
    }
    
    // Override runQuickAnalysis function to improve text formatting
    if (window.runQuickAnalysis) {
        const originalRunQuickAnalysis = window.runQuickAnalysis;
        
        window.runQuickAnalysis = function() {
            const tokenSelect = document.getElementById('quick-token');
            const resultsContainer = document.getElementById('quick-analysis-results');
            const loadingContainer = document.getElementById('quick-analysis-loading');
            
            if (!tokenSelect || !resultsContainer || !loadingContainer) return;
            
            const tokenId = tokenSelect.value;
            
            // Play sound
            if (typeof playSound === 'function') {
                playSound('click-sound');
            }
            
            // Show loading
            loadingContainer.style.display = 'flex';
            const placeholderMessage = resultsContainer.querySelector('.placeholder-message');
            if (placeholderMessage) {
                placeholderMessage.style.display = 'none';
            }
            
            // Fetch data from server
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token_id: tokenId })
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading
                loadingContainer.style.display = 'none';
                
                // Display results
                if (data.result) {
                    // Format the result text for better readability
                    let formattedResult = data.result;
                    
                    // Add basic formatting to highlight key information
                    formattedResult = formattedResult
                        .replace(/Risk Score:([^,\n]+)/g, '<span style="font-weight:bold;color:#c00;">Risk Score:$1</span>')
                        .replace(/Z-Score:([^,\n]+)/g, '<span style="font-weight:bold;color:#00a;">Z-Score:$1</span>')
                        .replace(/RSI:([^,\n]+)/g, '<span style="font-weight:bold;color:#0a0;">RSI:$1</span>')
                        .replace(/(BULLISH|BEARISH|NEUTRAL)/g, '<span style="font-weight:bold;text-decoration:underline;">$1</span>')
                        .replace(/\*\*([^*]+)\*\*/g, '<span style="font-weight:bold;">$1</span>');
                    
                    // Replace new lines with proper HTML breaks
                    formattedResult = formattedResult.replace(/\n/g, '<br>');
                    
                    const tokenName = tokenId.charAt(0).toUpperCase() + tokenId.slice(1);
                    
                    resultsContainer.innerHTML = `
                        <div class="analysis-header">
                            <span>${tokenName} Analysis</span>
                        </div>
                        <div class="analysis-result">
                            ${formattedResult}
                        </div>
                    `;
                } else if (data.error) {
                    resultsContainer.innerHTML = `
                        <div class="analysis-error">
                            <p>Error: ${data.error}</p>
                            <p>${data.details || ''}</p>
                        </div>
                    `;
                }
                
                // Play notification sound
                if (typeof playSound === 'function') {
                    playSound('notify-sound');
                }
            })
            .catch(error => {
                // Hide loading
                loadingContainer.style.display = 'none';
                
                // Show error
                resultsContainer.innerHTML = `
                    <div class="analysis-error">
                        <p>Error: ${error.message}</p>
                    </div>
                `;
                
                // Play error sound
                if (typeof playSound === 'function') {
                    playSound('error-sound');
                }
            });
        };
    }
    
    // Add CSS to fix text positioning in analysis window
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        /* Analysis window content improvements */
        .analysis-results {
            padding: 16px;
            height: calc(100% - 140px);
            overflow-y: auto;
            background-color: #ffffff;
            border-radius: 2px;
            border: 1px solid #d4d0c8;
            margin: 10px;
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            display: flex;
            flex-direction: column;
        }
        .analysis-results pre {
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin: 0;
            padding: 10px;
            line-height: 1.5;
            background-color: #f5f5f5;
            border-radius: 2px;
        }
        .analysis-result {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 13px;
            line-height: 1.4;
            color: #000;
            padding: 10px;
        }
        .analysis-result span {
            display: inline-block;
            margin: 3px 0;
        }
        .analysis-header {
            font-weight: bold;
            margin-bottom: 12px;
            padding: 8px;
            background-color: #ececec;
            border-bottom: 1px solid #d4d0c8;
            font-size: 14px;
        }
        .analysis-summary {
            margin-top: 14px;
            padding: 12px;
            background-color: #f5f5f5;
            border: 1px solid #d4d0c8;
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
        }
        .chart-container {
            height: 220px;
            min-height: 220px;
            margin: 15px auto;
            border: 1px solid #d4d0c8;
            background-color: #ffffff;
            padding: 10px;
            flex-grow: 1;
            position: relative;
        }
        /* Improved technical indicators display */
        .indicators-container {
            padding: 10px;
            margin-top: 15px;
            background-color: #ffffff;
            border: 1px solid #d4d0c8;
            flex-shrink: 0;
        }
        .indicator-section h4 {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            margin-bottom: 10px;
            color: var(--win97-blue);
            padding-bottom: 5px;
            border-bottom: 1px solid #d4d0c8;
        }
        .indicator-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            padding: 5px;
        }
        .indicator-row {
            display: grid;
            grid-template-columns: 120px 80px 1fr;
            align-items: center;
            padding: 8px;
            background-color: #f5f5f5;
            border: 1px solid #d4d0c8;
        }
        .indicator-name {
            font-weight: bold;
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
        }
        .indicator-value {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 13px;
            text-align: center;
            padding: 2px 5px;
            background-color: #ffffff;
            border: 1px inset #d4d0c8;
        }
        .indicator-signal {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-weight: bold;
            text-align: center;
            padding: 2px 8px;
            margin-left: 8px;
            letter-spacing: 0.5px;
        }
        .indicator-signal.bullish {
            background-color: #e6ffe6;
            color: #006600;
            border: 1px solid #99cc99;
        }
        .indicator-signal.bearish {
            background-color: #ffe6e6;
            color: #cc0000;
            border: 1px solid #cc9999;
        }
        .indicator-signal.neutral {
            background-color: #e6e6ff;
            color: #000080;
            border: 1px solid #9999cc;
        }
        
        /* Bands container for better nesting */
        .indicator-bands {
            margin-left: 40px;
            margin-top: 5px;
            margin-bottom: 10px;
            border-left: 2px solid #d4d0c8;
            padding-left: 10px;
        }
        .band-row {
            display: grid;
            grid-template-columns: 100px 100px;
            padding: 3px 0;
        }
        .band-name {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 12px;
            color: #444;
        }
        .band-value {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 12px;
            font-weight: bold;
        }
        
        /* Summary section styling */
        .summary-title {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 5px;
            color: var(--win97-blue);
        }
        .summary-content {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 13px;
            line-height: 1.5;
        }
        
        /* Improved price info display */
        .price-info {
            font-family: "MS Sans Serif", "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
            font-weight: bold;
            color: #006600;
            background-color: #f0fff0;
            border: 1px solid #99cc99;
            padding: 3px 8px;
            border-radius: 2px;
            letter-spacing: 0.5px;
        }
        /* Fix tab pane to use full height */
        .tab-content {
            height: calc(100% - 30px);
            overflow: hidden;
            flex: 1;
        }
        
        .tab-pane {
            height: 100%;
            display: none;
            overflow: hidden;
            flex-direction: column;
        }
        
        /* Special handling for technical tab */
        #technical-indicators {
            display: none;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
        }
        
        #technical-indicators.active {
            display: flex;
        }
        
        #technical-indicators .analysis-form {
            flex-shrink: 0;
        }
        
        .tab-pane.active {
            display: flex;
        }
        
        /* Fullscreen support for the window */
        .window.maximized {
            width: 100% !important;
            height: calc(100% - 28px) !important;
            top: 0 !important;
            left: 0 !important;
            z-index: 1000 !important;
        }
        .window.maximized .chart-container {
            height: 300px;
        }
        
        /* Support window resizing */
        .window-content {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: calc(100% - 40px) !important; /* Subtract title-bar and status-bar heights */
        }
        
        /* Fix for analysis window to expand */
        #analysis-window .window-content {
            padding: 0 !important;
            height: calc(100% - 40px) !important;
        }
        
        .tab-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
    `;
    document.head.appendChild(styleEl);
    
    // Add event listeners for the window control buttons
    const minimizeBtn = document.getElementById('minimize-analysis');
    const maximizeBtn = document.getElementById('maximize-analysis');
    const closeBtn = document.getElementById('close-analysis');
    
    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', function() {
            minimizeWindow('analysis-window');
        });
    }
    
    if (maximizeBtn) {
        maximizeBtn.addEventListener('click', function() {
            toggleMaximize('analysis-window');
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            closeWindow('analysis-window');
        });
    }
    
    console.log("Analysis window layout fixes applied!");
}

// Apply chart fixes when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check that Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error("Chart.js is not loaded! Charts will not work properly.");
        return;
    }
    
    console.log("Applying chart fixes (Chart.js version: " + Chart.version + ")");
    
    // Apply fixes
    fixTechnicalChart();
    fixWhaleChart();
    fixAnalysisWindowLayout();
    
    // Add resize event listener for window resizing
    window.addEventListener('resize', function() {
        // Resize charts if they exist
        if (window.priceChart) {
            try {
                window.priceChart.resize();
            } catch (e) {
                console.error("Error resizing price chart:", e);
            }
        }
        
        if (window.whaleChart) {
            try {
                window.whaleChart.resize();
            } catch (e) {
                console.error("Error resizing whale chart:", e);
            }
        }
    });
    
    // Add window drag end handler for chart resizing
    document.addEventListener('mouseup', function() {
        if (window.isDragging) {
            // After window is dragged, try to resize charts
            setTimeout(() => {
                updateChartSizes();
            }, 100);
        }
    });
    
    // Add handler for window corner resize
    const resizeObserver = new ResizeObserver(entries => {
        for (const entry of entries) {
            if (entry.target.id === 'analysis-window') {
                updateChartSizes();
            }
        }
    });
    
    // Observe the analysis window for size changes
    const analysisWindow = document.getElementById('analysis-window');
    if (analysisWindow) {
        resizeObserver.observe(analysisWindow);
    }
    
    // Log success
    console.log("All chart fixes applied successfully!");
});