// Global Variables
let activeWindow = null;
let windows = {};
let isDragging = false;
let dragOffsetX = 0;
let dragOffsetY = 0;
let isStartMenuOpen = false;
let isMaximized = {};
let windowPositions = {};
let windowSizes = {};
let soundEnabled = true;

function playSound(soundId) {
    // Check if sounds are enabled
    const enableSounds = localStorage.getItem('enableSounds') !== 'false';
    if (!enableSounds) return;
    
    // Get sound element
    const sound = document.getElementById(soundId);
    if (!sound) {
        console.warn(`Sound element with id ${soundId} not found`);
        return;
    }
    
    // Check if the sound file exists and is loaded
    if (sound.error || sound.readyState === 0) {
        console.warn(`Sound file for ${soundId} could not be loaded`);
        return;
    }
    
    try {
        // Reset playback position
        sound.currentTime = 0;
        
        // Play the sound (with error handling)
        const playPromise = sound.play();
        
        // Handle promise to avoid uncaught errors
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.warn(`Error playing sound: ${error.message}`);
            });
        }
    } catch (e) {
        console.warn(`Error playing sound: ${e.message}`);
    }
}

function displayWhaleResults(token, data, price, container) {
    const priceDisplay = price > 0 ? 
        `$${price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : 
        'Price data unavailable';
    
    // Create results HTML
    const resultsHTML = `
        <div class="analysis-header">
            <span>${token.toUpperCase()} Whale Activity Analysis</span>
            <span class="price-info">${priceDisplay}</span>
        </div>
        
        <div class="chart-container">
            <canvas id="whale-activity-chart" width="400" height="200"></canvas>
        </div>
        
        <div class="metric-container">
            <div class="metric-row">
                <div class="metric-label">Risk Score:</div>
                <div class="metric-value ${getRiskClass(data.risk_score)}">
                    ${data.risk_score} / 100 (${data.level})
                </div>
            </div>
            
            <div class="metric-row">
                <div class="metric-label">Detected Signals:</div>
                <div class="metric-value">
                    ${data.signals && data.signals.length > 0 ? 
                        `<ul>${data.signals.map(signal => `<li>${signal}</li>`).join('')}</ul>` : 
                        'No specific risk signals detected'}
                </div>
            </div>
        </div>
        
        <div class="analysis-summary">
            <div class="summary-title">Whale Analysis Summary:</div>
            <div>The current whale activity for ${token.toUpperCase()} shows ${getWhaleAnalysisSummary(data)}.</div>
        </div>
    `;
    
    // Add results to container
    container.innerHTML = resultsHTML;
    
    // Generate mock data for whale activity chart
    renderWhaleActivityChart(token, data);
    
    // Play notification sound
    playSound('notify-sound');
}

// Function to render whale activity chart
function renderWhaleActivityChart(token, data) {
    try {
        const canvas = document.getElementById('whale-activity-chart');
        if (!canvas) {
            console.error("Could not find whale-activity-chart canvas element");
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Generate mock whale activity data (in a real app, this would come from the API)
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
        
        // Create the chart
        const chart = new Chart(ctx, {
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
        
        return chart;
    } catch (e) {
        console.error("Error rendering whale activity chart:", e);
    }
}

// Helper Functions

function getSignalClassFromValue(value) {
    if (!value) return 'neutral';
    
    value = value.toString().toUpperCase();
    
    if (value.includes('BULLISH') || 
        value.includes('UPWARD') || 
        value.includes('OVERSOLD') || 
        value.includes('BUY') ||
        value.includes('LOW')) {
        return 'bullish';
    } else if (value.includes('BEARISH') || 
               value.includes('DOWNWARD') || 
               value.includes('OVERBOUGHT') || 
               value.includes('SELL') ||
               value.includes('HIGH')) {
        return 'bearish';
    } else {
        return 'neutral';
    }
}

function getSignalClass(signal) {
    return getSignalClassFromValue(signal);
}

function getRiskClass(score) {
    if (score < 40) return 'bullish';
    if (score > 60) return 'bearish';
    return 'neutral';
}

function getZScoreSignal(value) {
    if (value > 2) return 'STRONGLY OVERBOUGHT';
    if (value > 1) return 'OVERBOUGHT';
    if (value < -2) return 'STRONGLY OVERSOLD';
    if (value < -1) return 'OVERSOLD';
    return 'NEUTRAL';
}

function getRSISignal(value) {
    if (value > 70) return 'OVERBOUGHT';
    if (value > 60) return 'APPROACHING OVERBOUGHT';
    if (value < 30) return 'OVERSOLD';
    if (value < 40) return 'APPROACHING OVERSOLD';
    return 'NEUTRAL';
}

function getBBSignal(value) {
    if (value > 1) return 'ABOVE UPPER BAND';
    if (value > 0.8) return 'UPPER BAND TOUCH';
    if (value < 0) return 'BELOW LOWER BAND';
    if (value < 0.2) return 'LOWER BAND TOUCH';
    return 'MIDDLE BAND';
}

function getTechnicalSummary(token, metrics) {
    // Generate a meaningful summary based on the technical indicators
    let summary = '';
    
    if (metrics.z_score && metrics.rsi && metrics.bollinger_bands) {
        const z_score = metrics.z_score.value;
        const rsi = metrics.rsi.value;
        const bb = metrics.bollinger_bands.percent_b;
        
        // Overextended to the upside?
        if (z_score > 1 && rsi > 65 && bb > 0.8) {
            summary = `${token.toUpperCase()} is showing signs of being overextended to the upside, with multiple indicators in overbought territory. This often precedes a reversion to the mean (downward movement).`;
        } 
        // Overextended to the downside?
        else if (z_score < -1 && rsi < 35 && bb < 0.2) {
            summary = `${token.toUpperCase()} is showing signs of being overextended to the downside, with multiple indicators in oversold territory. This may present a buying opportunity as prices often revert to the mean.`;
        }
        // Mixed signals but leaning bullish
        else if ((z_score < 0 || rsi < 45 || bb < 0.4) && !(z_score > 1 || rsi > 65 || bb > 0.8)) {
            summary = `${token.toUpperCase()} is showing some signs of weakness, but not yet in extreme oversold territory. Watch for potential buying opportunities if indicators move further into oversold zones.`;
        }
        // Mixed signals but leaning bearish
        else if ((z_score > 0 || rsi > 55 || bb > 0.6) && !(z_score < -1 || rsi < 35 || bb < 0.2)) {
            summary = `${token.toUpperCase()} is showing some strength, but not yet in extreme overbought territory. Caution is advised if indicators continue to move higher into overbought zones.`;
        }
        // Neutral
        else {
            summary = `${token.toUpperCase()} is currently in neutral territory with no extreme readings on technical indicators. The asset may be in a ranging or consolidation phase.`;
        }
    } else {
        summary = `Technical indicators suggest monitoring ${token.toUpperCase()} for more decisive signals before making trading decisions.`;
    }
    
    return summary;
}

function getWhaleAnalysisSummary(data) {
    if (data.risk_score > 70) {
        return 'significant distribution from large holders, which often precedes downward price movements';
    } else if (data.risk_score > 50) {
        return 'moderate activity from larger players with some concerning transfer patterns';
    } else if (data.risk_score > 30) {
        return 'typical movement patterns with no significant anomalies in wallet transfers';
    } else {
        return 'accumulation patterns from large holders, which is typically a positive long-term signal';
    }
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load window elements
    document.querySelectorAll('.window').forEach(function(windowElement) {
        windows[windowElement.id] = windowElement;
        isMaximized[windowElement.id] = false;
    });

    // Initialize window drag functionality
    initWindowDrag();

    // Initialize sound settings
    if (localStorage.getItem('enableSounds') === null) {
        localStorage.setItem('enableSounds', 'true');
    }
    
    // Update sound checkbox based on stored preference
    const soundCheckbox = document.getElementById('enable-sounds');
    if (soundCheckbox) {
        soundCheckbox.checked = localStorage.getItem('enableSounds') !== 'false';
    }
    
    // Play startup sound
    playSound('startup-sound');
    
    // Initialize desktop icons - FIXED: Remove onclick attribute dependency
    const desktopIcons = document.querySelectorAll('.desktop-icon');
    desktopIcons.forEach(icon => {
        const windowId = icon.id.replace('-icon', '');
        icon.addEventListener('click', function() {
            playSound('click-sound');
            openWindow(windowId + '-window');
        });
    });
    
    // Initialize window buttons with consistent behavior
    document.querySelectorAll('.title-bar-button').forEach(button => {
        button.addEventListener('click', function() {
            playSound('click-sound');
            
            // Get the window id from the parent element
            const windowEl = this.closest('.window');
            const windowId = windowEl ? windowEl.id : null;
            
            if (!windowId) return;
            
            // Determine action based on button class
            if (button.classList.contains('minimize-button')) {
                minimizeWindow(windowId);
            } else if (button.classList.contains('maximize-button')) {
                toggleMaximize(windowId);
            } else if (button.classList.contains('close-button')) {
                closeWindow(windowId);
            }
        });
    });
    
    // Initialize taskbar time
    updateTaskbarTime();
    setInterval(updateTaskbarTime, 60000);
    
    // Start menu functionality
    const startButton = document.getElementById('start-button');
    const startMenu = document.getElementById('start-menu');
    
    if (startButton && startMenu) {
        startButton.addEventListener('click', function() {
            toggleStartMenu();
        });
        
        // Close start menu when clicking elsewhere
        document.addEventListener('click', function(event) {
            if (!startButton.contains(event.target) && !startMenu.contains(event.target)) {
                startMenu.style.display = 'none';
                isStartMenuOpen = false;
                startButton.classList.remove('active');
            }
        });
    }
    
    // Initialize start menu items
    const startMenuItems = document.querySelectorAll('.start-menu-item');
    startMenuItems.forEach(item => {
        item.addEventListener('click', function() {
            playSound('click-sound');
            
            // FIXED: Handle start menu item clicks directly
            const windowId = this.querySelector('span').textContent.trim().toLowerCase().replace(' ', '-') + '-window';
            if (windowId === 'shut-down-window') {
                // Handle shutdown option
                showErrorDialog('System shutdown is not available in this demo.');
            } else {
                openWindow(windowId);
            }
            
            startMenu.style.display = 'none';
            isStartMenuOpen = false;
            startButton.classList.remove('active');
        });
    });

    // Handle Enter key in chat input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    // Handle window focus on click
    document.querySelectorAll('.window').forEach(function(windowEl) {
        windowEl.addEventListener('mousedown', function() {
            activateWindow(windowEl.id);
        });
    });

    // Handle tab switching - FIXED: Remove onclick attribute dependency
    document.querySelectorAll('.tab-button').forEach(function(button) {
        // Extract tab ID from parent container and button text
        const tabContainer = button.closest('.tab-container');
        if (tabContainer) {
            const tabText = button.textContent.trim().toLowerCase().replace(/\s+/g, '-');
            button.addEventListener('click', function() {
                showTab(tabText);
                
                // Update active state on buttons
                tabContainer.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');
            });
        }
    });

    // Handle help tab switching
    // Map each help sidebar item to its corresponding tab ID
    const helpTabMapping = [
        { text: 'Getting Started', id: 'getting-started' },
        { text: 'Available Commands', id: 'commands' },
        { text: 'Analysis Tools', id: 'tools' },
        { text: 'Blockchain Features', id: 'blockchain' },
        { text: 'About Dexy', id: 'about' }
    ];
    
    const helpSidebarItems = document.querySelectorAll('.help-sidebar-item');
    
    helpSidebarItems.forEach(function(item, index) {
        // Add robust click handling
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the tab ID from our mapping
            const tabId = helpTabMapping[index].id;
            console.log(`Help sidebar item clicked: ${item.textContent.trim()} -> ${tabId}`);
            
            // Show the tab
            showHelpTab(tabId);
            
            // Update active state in sidebar
            helpSidebarItems.forEach(sidebarItem => {
                sidebarItem.classList.remove('active');
            });
            item.classList.add('active');
        });
    });
    
    // FIXED: Add missing function implementations
    // Add analysis button handlers
    document.querySelector('button[onclick="runQuickAnalysis()"]')?.addEventListener('click', runQuickAnalysis);
    document.querySelector('button[onclick="runTechnicalAnalysis()"]')?.addEventListener('click', runTechnicalAnalysis);
    document.querySelector('button[onclick="runWhaleAnalysis()"]')?.addEventListener('click', runWhaleAnalysis);
    
    // Add settings button handlers
    document.querySelector('button[onclick="saveSettings()"]')?.addEventListener('click', saveSettings);
    document.querySelector('button[onclick="connectWallet()"]')?.addEventListener('click', connectWallet);
    document.querySelector('button[onclick="generateNewWallet()"]')?.addEventListener('click', generateNewWallet);
    
    // Ensure sounds exist
    ensureSoundsExist();
    
    // Load settings
    loadSettings();
    
    // Check for existing wallet connection
    checkWalletConnection();
});

function updateTaskbarTime() {
    const timeElement = document.getElementById('taskbar-time');
    if (timeElement) {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const formattedHours = hours % 12 || 12;
        const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
        timeElement.textContent = `${formattedHours}:${formattedMinutes} ${ampm}`;
    }
}

function openWindow(windowId) {
    playSound('click-sound');
    
    if (windows[windowId]) {
        windows[windowId].style.display = 'block';
        
        // Remove minimized class if present
        windows[windowId].classList.remove('minimized');
        
        // Activate the window
        activateWindow(windowId);
        
        // Add to taskbar if not there already
        updateTaskbar();
    }
}

function closeWindow(windowId) {
    playSound('click-sound');
    
    if (windows[windowId]) {
        windows[windowId].style.display = 'none';
        
        // If this was the active window, remove the active class
        windows[windowId].classList.remove('active');
        
        // Update the taskbar
        updateTaskbar();
        
        // If there are other visible windows, activate the last one
        let visibleWindows = Array.from(document.querySelectorAll('.window'))
            .filter(w => w.style.display !== 'none' && !w.classList.contains('minimized'));
        
        if (visibleWindows.length > 0) {
            activateWindow(visibleWindows[visibleWindows.length - 1].id);
        }
    }
}

function minimizeWindow(windowId) {
    playSound('click-sound');
    
    if (windows[windowId]) {
        // Add minimized class
        windows[windowId].classList.add('minimized');
        
        // Remove active class
        windows[windowId].classList.remove('active');
        
        // Update the active window variable if needed
        if (activeWindow === windowId) {
            activeWindow = null;
        }
        
        // Update the taskbar
        updateTaskbar();
    }
}

function toggleMaximize(windowId) {
    playSound('click-sound');
    
    if (windows[windowId]) {
        if (!isMaximized[windowId]) {
            // Save current position and size before maximizing
            const winStyle = window.getComputedStyle(windows[windowId]);
            
            windowPositions[windowId] = {
                top: windows[windowId].style.top || winStyle.top,
                left: windows[windowId].style.left || winStyle.left
            };
            
            windowSizes[windowId] = {
                width: windows[windowId].style.width || winStyle.width,
                height: windows[windowId].style.height || winStyle.height
            };
            
            console.log(`Saving window position/size for ${windowId}:`, 
                        windowPositions[windowId], windowSizes[windowId]);
            
            // Apply maximized class
            windows[windowId].classList.add('maximized');
            
            // Set explicit styles to maximize
            windows[windowId].style.top = '0';
            windows[windowId].style.left = '0';
            windows[windowId].style.width = '100%';
            windows[windowId].style.height = 'calc(100vh - 30px)';
            windows[windowId].style.resize = 'none';
            
            isMaximized[windowId] = true;
        } else {
            // Restore previous position and size
            if (windowPositions[windowId]) {
                windows[windowId].style.top = windowPositions[windowId].top;
                windows[windowId].style.left = windowPositions[windowId].left;
                console.log(`Restoring position to: top=${windowPositions[windowId].top}, left=${windowPositions[windowId].left}`);
            }
            
            if (windowSizes[windowId]) {
                windows[windowId].style.width = windowSizes[windowId].width;
                windows[windowId].style.height = windowSizes[windowId].height;
                console.log(`Restoring size to: width=${windowSizes[windowId].width}, height=${windowSizes[windowId].height}`);
            }
            
            // Re-enable resize
            windows[windowId].style.resize = 'both';
            
            // Remove maximized class
            windows[windowId].classList.remove('maximized');
            isMaximized[windowId] = false;
        }
        
        // Activate the window
        activateWindow(windowId);
    }
}

function activateWindow(windowId) {
    // Remove active class from all windows
    document.querySelectorAll('.window').forEach(function(win) {
        win.classList.remove('active');
    });
    
    // Add active class to the selected window
    if (windows[windowId]) {
        windows[windowId].classList.add('active');
        
        // Bring to front by setting a higher z-index
        windows[windowId].style.zIndex = getHighestZIndex() + 1;
        
        // Update active window variable
        activeWindow = windowId;
        
        // Update taskbar to show active window
        updateTaskbar();
    }
}

function getHighestZIndex() {
    let highest = 10; // Start from base z-index for windows
    
    document.querySelectorAll('.window').forEach(function(win) {
        const zIndex = parseInt(window.getComputedStyle(win).zIndex, 10);
        if (zIndex > highest) {
            highest = zIndex;
        }
    });
    
    return highest;
}

function initWindowDrag() {
    // Enable dragging for all window title bars
    document.querySelectorAll('.title-bar').forEach(function(titleBar) {
        titleBar.addEventListener('mousedown', function(e) {
            // Don't start drag if clicking on a title bar button
            if (e.target.closest('.title-bar-button')) {
                return;
            }
            
            const windowElement = titleBar.closest('.window');
            const windowId = windowElement.id;
            
            // Activate the window on drag start
            activateWindow(windowId);
            
            // Don't drag maximized windows
            if (isMaximized[windowId]) {
                return;
            }
            
            isDragging = true;
            
            // Calculate offset of click relative to window position
            const windowRect = windowElement.getBoundingClientRect();
            dragOffsetX = e.clientX - windowRect.left;
            dragOffsetY = e.clientY - windowRect.top;
            
            // Add dragging class
            windowElement.classList.add('dragging');
            
            // Prevent text selection while dragging
            e.preventDefault();
        });
    });
    
    // Handle drag movement
    document.addEventListener('mousemove', function(e) {
        if (isDragging && activeWindow) {
            const windowElement = windows[activeWindow];
            
            // Calculate new position
            let newLeft = e.clientX - dragOffsetX;
            let newTop = e.clientY - dragOffsetY;
            
            // Constrain to window boundaries
            newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - 100));
            newTop = Math.max(0, Math.min(newTop, window.innerHeight - 30));
            
            // Update position
            windowElement.style.left = newLeft + 'px';
            windowElement.style.top = newTop + 'px';
        }
    });
    
    // Handle drag end
    document.addEventListener('mouseup', function() {
        if (isDragging && activeWindow) {
            // Remove dragging class
            windows[activeWindow].classList.remove('dragging');
            isDragging = false;
        }
    });
}

function updateTaskbar() {
    const taskbarEntries = document.getElementById('taskbar-entries');
    if (!taskbarEntries) return;
    
    taskbarEntries.innerHTML = '';
    
    // Add taskbar entries for open windows
    document.querySelectorAll('.window').forEach(function(windowEl) {
        if (windowEl.style.display !== 'none' || windowEl.classList.contains('minimized')) {
            const taskbarEntry = document.createElement('div');
            taskbarEntry.className = 'taskbar-entry';
            if (windowEl.classList.contains('active') && !windowEl.classList.contains('minimized')) {
                taskbarEntry.classList.add('active');
            }
            
            // Get title text
            const titleText = windowEl.querySelector('.title-bar-text').textContent.trim();
            
            // Get icon based on window id
            let iconPath = '';
            switch(windowEl.id) {
                case 'chat-window':
                    iconPath = 'static/img/wxp_317.png';
                    break;
                case 'analysis-window':
                    iconPath = 'static/img/tools_gear-0.png';
                    break;
                case 'settings-window':
                    iconPath = 'static/img/wxp_244.png';
                    break;
                case 'help-window':
                    iconPath = 'static/img/wxp_220.png';
                    break;
                default:
                    iconPath = 'static/img/mycomputer.png';
            }
            
            // Add icon and text
            const icon = document.createElement('img');
            icon.className = 'taskbar-entry-icon';
            icon.src = iconPath;
            icon.alt = '';
            
            const text = document.createElement('span');
            text.className = 'taskbar-entry-text';
            text.textContent = titleText;
            
            taskbarEntry.appendChild(icon);
            taskbarEntry.appendChild(text);
            
            // Add click handler
            taskbarEntry.addEventListener('click', function() {
                playSound('click-sound');
                
                if (windowEl.classList.contains('minimized')) {
                    // Restore window from minimized state
                    windowEl.classList.remove('minimized');
                    activateWindow(windowEl.id);
                } else if (windowEl.classList.contains('active')) {
                    // Minimize if already active
                    minimizeWindow(windowEl.id);
                } else {
                    // Activate if not active
                    activateWindow(windowEl.id);
                }
            });
            
            taskbarEntries.appendChild(taskbarEntry);
        }
    });
}

function toggleStartMenu() {
    playSound('click-sound');
    
    const startMenu = document.getElementById('start-menu');
    const startButton = document.getElementById('start-button');
    
    if (!startMenu || !startButton) return;
    
    if (isStartMenuOpen) {
        startMenu.style.display = 'none';
        startButton.classList.remove('active');
    } else {
        startMenu.style.display = 'block';
        startButton.classList.add('active');
    }
    
    isStartMenuOpen = !isStartMenuOpen;
}

function updateClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    
    const timeString = hours + ':' + (minutes < 10 ? '0' + minutes : minutes) + ' ' + ampm;
    document.getElementById('taskbar-time').textContent = timeString;
}

function saveSettings() {
    playSound('click-sound');
    
    const apiKey = document.getElementById('api-key').value;
    const apiProvider = document.getElementById('api-provider').value;
    const enableSounds = document.getElementById('enable-sounds').checked;
    const autostartChat = document.getElementById('autostart-chat').checked;
    
    // Apply sound setting immediately
    soundEnabled = enableSounds;
    
    // Save settings to localStorage
    localStorage.setItem('dexy_apiKey', apiKey);
    localStorage.setItem('dexy_apiProvider', apiProvider);
    localStorage.setItem('dexy_enableSounds', enableSounds);
    localStorage.setItem('dexy_autostartChat', autostartChat);
    
    // Show notification
    showNotification('Settings saved successfully!');
    
    // Close settings window
    closeWindow('settings-window');
}

function loadSettings() {
    // Load settings from localStorage
    const apiKey = localStorage.getItem('dexy_apiKey') || '';
    const apiProvider = localStorage.getItem('dexy_apiProvider') || 'defillama';
    const enableSounds = localStorage.getItem('dexy_enableSounds') !== 'false'; // Default to true
    const autostartChat = localStorage.getItem('dexy_autostartChat') === 'true'; // Default to false
    
    // Apply settings
    document.getElementById('api-key').value = apiKey;
    document.getElementById('api-provider').value = apiProvider;
    document.getElementById('enable-sounds').checked = enableSounds;
    document.getElementById('autostart-chat').checked = autostartChat;
    
    // Apply sound setting
    soundEnabled = enableSounds;
    
    // Auto-start chat if enabled
    if (autostartChat) {
        setTimeout(() => {
            openWindow('chat-window');
        }, 1000);
    }
}

function checkWalletConnection() {
    // Check if a wallet is already connected by querying the server
    const connectionStatus = document.getElementById('connection-status');
    const walletDisplay = document.getElementById('wallet-address');
    
    if (!connectionStatus || !walletDisplay) return;
    
    // Show loading state
    walletDisplay.innerHTML = 'Checking wallet connection...';
    connectionStatus.textContent = 'Connecting to Base Sepolia...';
    
    // Query the wallet endpoint
    fetch('/wallet', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.wallet && !data.error) {
            // Wallet exists
            walletDisplay.innerHTML = `
                <div class="wallet-address-display">
                    <div class="wallet-type">${data.wallet_type || 'CDP'} Wallet</div>
                    <div class="address-text">${data.wallet.address || '0x1234...5678'}</div>
                    <div class="wallet-network">Network: ${data.network || 'Unknown'}</div>
                </div>
            `;
            
            // Update connection status
            if (connectionStatus) {
                connectionStatus.textContent = `Connected to CDP (${data.network || 'Unknown'})`;
                connectionStatus.classList.add('connected');
            }
        } else {
            // No wallet or error
            walletDisplay.innerHTML = 'Not connected';
        }
    })
    .catch(error => {
        console.error('Error checking wallet connection:', error);
        walletDisplay.innerHTML = 'Error checking wallet status';
    });
}

function showErrorDialog(message) {
    playSound('error-sound');
    
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-dialog-overlay').style.display = 'flex';
}

function closeErrorDialog() {
    playSound('click-sound');
    
    document.getElementById('error-dialog-overlay').style.display = 'none';
}

function showNotification(message) {
    playSound('notify-sound');
    
    // Create and show toast notification
    const notification = document.createElement('div');
    notification.className = 'win97-notification';
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.bottom = '40px';
    notification.style.right = '20px';
    notification.style.background = 'var(--win97-blue)';
    notification.style.color = 'white';
    notification.style.padding = '10px 15px';
    notification.style.border = '2px solid';
    notification.style.borderColor = 'var(--win97-light) var(--win97-dark) var(--win97-dark) var(--win97-light)';
    notification.style.zIndex = '2000';
    notification.style.transition = 'opacity 0.3s, transform 0.3s';
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(20px)';
    notification.style.boxShadow = '3px 3px 5px rgba(0,0,0,0.3)';
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Function to ensure sounds directory exists
function ensureSoundsExist() {
    // Create sounds directory if it doesn't exist
    const soundsPath = 'static/sounds';
    
    // Check if audio elements have valid sources
    const soundIds = ['startup-sound', 'error-sound', 'click-sound', 'notify-sound'];
    soundIds.forEach(id => {
        const sound = document.getElementById(id);
        if (sound && (!sound.src || sound.src === '')) {
            console.warn(`Sound ${id} missing source. Creating default path.`);
            // Set default paths based on sound ID
            const fileName = id.replace('-sound', '') + '.mp3';
            sound.src = `${soundsPath}/${fileName}`;
        }
    });
}

// ADDED: Missing UI function implementations

// Tab switching function
function showTab(tabId) {
    // Hide all tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Show the selected tab pane
    const selectedPane = document.getElementById(tabId);
    if (selectedPane) {
        selectedPane.classList.add('active');
    }
}

// Help tab switching function
function showHelpTab(tabId) {
    console.log(`Showing help tab: ${tabId}`);
    
    // Force display style updates (this helps overcome any CSS specificity issues)
    // Hide all help tab content
    document.querySelectorAll('.help-tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });
    
    // Show the selected help tab content
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
        selectedTab.style.display = 'block';
        console.log(`Tab ${tabId} activated and displayed`);
    } else {
        console.error(`Could not find tab with id: ${tabId}`);
        // Log all available tabs for debugging
        document.querySelectorAll('.help-tab-content').forEach(content => {
            console.log(`Available tab: ${content.id}`);
        });
    }
}

// Chat message sending function
function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (!chatInput || !chatMessages) return;
    
    const message = chatInput.value.trim();
    if (message === '') return;
    
    // Play sound
    playSound('click-sound');
    
    // Append user message
    chatMessages.innerHTML += `
        <div class="chat-message user">
            <div class="message-content">
                <div class="message-text">
                    <p>${message}</p>
                </div>
            </div>
        </div>
    `;
    
    // Clear input
    chatInput.value = '';
    
    // Show loading indicator
    chatMessages.innerHTML += `
        <div class="chat-message system loading">
            <div class="message-content">
                <img src="static/img/wxp_317.png" class="bot-avatar">
                <div class="message-text">
                    <div class="win95-loading"></div>
                </div>
            </div>
        </div>
    `;
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Special handling for BTC analysis request
    if (message.toLowerCase().includes('run analysis on btc') || 
        message.toLowerCase().includes('run analysis on bitcoin') || 
        message.toLowerCase().includes('analyze btc') || 
        message.toLowerCase().includes('analyze bitcoin')) {
        
        // First fetch the analysis result
        fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token_id: 'bitcoin' })
        })
        .then(response => response.json())
        .then(analysisData => {
            // Now send the message with the context of the analysis
            fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: `${message}\n\nHere's the analysis I have: ${analysisData.result}` 
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                const loadingMessage = chatMessages.querySelector('.loading');
                if (loadingMessage) {
                    loadingMessage.remove();
                }
                
                // Append bot response
                chatMessages.innerHTML += `
                    <div class="chat-message system">
                        <div class="message-content">
                            <img src="static/img/wxp_317.png" class="bot-avatar">
                            <div class="message-text">
                                <p>${data.response || data.error || "I couldn't process your request at this time."}</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Play notification sound
                playSound('notify-sound');
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(handleFetchError);
        })
        .catch(handleFetchError);
    } else {
        // Normal message handling
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            const loadingMessage = chatMessages.querySelector('.loading');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            // Append bot response
            chatMessages.innerHTML += `
                <div class="chat-message system">
                    <div class="message-content">
                        <img src="static/img/wxp_317.png" class="bot-avatar">
                        <div class="message-text">
                            <p>${data.response || data.error || "I couldn't process your request at this time."}</p>
                        </div>
                    </div>
                </div>
            `;
            
            // Play notification sound
            playSound('notify-sound');
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(handleFetchError);
    }
    
    // Helper function for error handling
    function handleFetchError(error) {
        // Remove loading indicator
        const loadingMessage = chatMessages.querySelector('.loading');
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        // Show error message
        chatMessages.innerHTML += `
            <div class="chat-message system error">
                <div class="message-content">
                    <img src="static/img/wxp_317.png" class="bot-avatar">
                    <div class="message-text">
                        <p>Sorry, I encountered an error: ${error.message}</p>
                    </div>
                </div>
            </div>
        `;
        
        // Play error sound
        playSound('error-sound');
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Analysis functions
function runQuickAnalysis() {
    const tokenSelect = document.getElementById('quick-token');
    const resultsContainer = document.getElementById('quick-analysis-results');
    const loadingContainer = document.getElementById('quick-analysis-loading');
    
    if (!tokenSelect || !resultsContainer || !loadingContainer) return;
    
    const tokenId = tokenSelect.value;
    
    // Play sound
    playSound('click-sound');
    
    // Show loading
    loadingContainer.style.display = 'flex';
    resultsContainer.querySelector('.placeholder-message').style.display = 'none';
    
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
            resultsContainer.innerHTML = `
                <div class="analysis-result">
                    <pre>${data.result}</pre>
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
        playSound('notify-sound');
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
        playSound('error-sound');
    });
}

function runTechnicalAnalysis() {
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
    playSound('click-sound');
    
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
            // Create chart container
            resultsContainer.innerHTML = `
                <div class="analysis-header">
                    <span>${tokenId.toUpperCase()} Technical Analysis (${days} Days)</span>
                    <span class="price-info">$${data.indicators.current_price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
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
            `;
            
            // Add indicator values
            const indicatorValues = document.getElementById('indicator-values');
            const indicators = data.indicators.indicators;
            
            if (showZScore && showZScore.checked && indicators.z_score) {
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
            }
            
            if (showRSI && showRSI.checked && indicators.rsi) {
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
            }
            
            if (showBB && showBB.checked && indicators.bollinger_bands) {
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
                    <div class="indicator-row">
                        <div class="indicator-name">Upper Band:</div>
                        <div class="indicator-value">${bb.upper_band.toFixed(2)}</div>
                    </div>
                    <div class="indicator-row">
                        <div class="indicator-name">Middle Band:</div>
                        <div class="indicator-value">${bb.middle_band.toFixed(2)}</div>
                    </div>
                    <div class="indicator-row">
                        <div class="indicator-name">Lower Band:</div>
                        <div class="indicator-value">${bb.lower_band.toFixed(2)}</div>
                    </div>
                `;
            }
            
            // Create price chart
            const prices = data.indicators.historical_prices || [];
            const dates = prices.map(p => new Date(p.timestamp * 1000).toLocaleDateString());
            const priceValues = prices.map(p => p.price);
            
            const ctx = document.getElementById('price-chart').getContext('2d');
            new Chart(ctx, {
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
            
            // Play notification sound
            playSound('notify-sound');
        } else if (data.error) {
            resultsContainer.innerHTML = `
                <div class="analysis-error">
                    <p>Error: ${data.error}</p>
                    <p>${data.details || ''}</p>
                </div>
            `;
            
            // Play error sound
            playSound('error-sound');
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
        playSound('error-sound');
    });
}

function runWhaleAnalysis() {
    const tokenSelect = document.getElementById('whale-token');
    const resultsContainer = document.getElementById('whale-analysis-results');
    const loadingContainer = document.getElementById('whale-analysis-loading');
    
    if (!tokenSelect || !resultsContainer || !loadingContainer) return;
    
    const tokenId = tokenSelect.value;
    
    // Play sound
    playSound('click-sound');
    
    // Show loading
    loadingContainer.style.display = 'flex';
    resultsContainer.querySelector('.placeholder-message').style.display = 'none';
    
    // Get current price (for display purposes)
    let currentPrice = 0;
    
    // First get the current price from technical endpoint
    fetch('/technical', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token_id: tokenId, days: 1 })
    })
    .then(response => response.json())
    .then(priceData => {
        if (priceData.indicators && priceData.indicators.current_price) {
            currentPrice = priceData.indicators.current_price;
        }
        
        // Now get the whale activity data
        return fetch('/whale', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token_id: tokenId })
        });
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading
        loadingContainer.style.display = 'none';
        
        // Display results
        displayWhaleResults(tokenId, data, currentPrice, resultsContainer);
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
        playSound('error-sound');
    });
}

// Wallet functions
function connectWallet() {
    // Play sound
    playSound('click-sound');
    
    const walletDisplay = document.getElementById('wallet-address');
    const connectionStatus = document.getElementById('connection-status');
    if (!walletDisplay) return;
    
    // Show loading
    walletDisplay.innerHTML = 'Connecting to CDP wallet on Base Sepolia...';
    if (connectionStatus) {
        connectionStatus.textContent = 'Connecting to Base Sepolia...';
    }
    
    // Connect to CDP wallet
    fetch('/generate-wallet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ connect: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.wallet) {
            // Display wallet address
            walletDisplay.innerHTML = `
                <div class="wallet-address-display">
                    <div class="wallet-type">${data.wallet_type} Wallet</div>
                    <div class="address-text">${data.wallet.address || '0x1234...5678'}</div>
                    <div class="wallet-network">Network: ${data.network || 'Unknown'}</div>
                </div>
            `;
            
            // Play notification sound
            playSound('notify-sound');
            
            // Show notification
            showNotification('CDP wallet connected successfully!');
            
            // Update connection status in status bar
            const connectionStatus = document.getElementById('connection-status');
            if (connectionStatus) {
                connectionStatus.textContent = `Connected to CDP (${data.network || 'base-sepolia'})`;
                connectionStatus.classList.add('connected');
            }
        } else {
            // Show error
            walletDisplay.innerHTML = 'Error connecting wallet';
            
            // Play error sound
            playSound('error-sound');
            
            // Show error dialog
            showErrorDialog(data.message || 'Failed to connect CDP wallet.');
        }
    })
    .catch(error => {
        // Show error
        walletDisplay.innerHTML = 'Error connecting wallet';
        
        // Play error sound
        playSound('error-sound');
        
        // Show error dialog
        showErrorDialog(`Error: ${error.message}`);
    });
}

function generateNewWallet() {
    // Play sound
    playSound('click-sound');
    
    const walletDisplay = document.getElementById('wallet-address');
    const connectionStatus = document.getElementById('connection-status');
    if (!walletDisplay) return;
    
    // Show loading
    walletDisplay.innerHTML = 'Generating new CDP wallet on Base Sepolia...';
    if (connectionStatus) {
        connectionStatus.textContent = 'Connecting to Base Sepolia...';
    }
    
    // Generate a new wallet
    fetch('/generate-wallet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ generate: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.wallet) {
            // Display wallet address
            walletDisplay.innerHTML = `
                <div class="wallet-address-display">
                    <div class="wallet-type">${data.wallet_type} Wallet</div>
                    <div class="address-text">${data.wallet.address || '0x1234...5678'}</div>
                    <div class="wallet-network">Network: ${data.network || 'Unknown'}</div>
                </div>
            `;
            
            // Play notification sound
            playSound('notify-sound');
            
            // Show notification
            showNotification('New wallet generated successfully!');
            
            // Update connection status in status bar
            const connectionStatus = document.getElementById('connection-status');
            if (connectionStatus) {
                connectionStatus.textContent = `Connected to CDP (${data.network || 'base-sepolia'})`;
                connectionStatus.classList.add('connected');
            }
        } else {
            // Show error
            walletDisplay.innerHTML = 'Error generating wallet';
            
            // Play error sound
            playSound('error-sound');
            
            // Show error dialog
            showErrorDialog(data.message || 'Failed to generate new wallet.');
        }
    })
    .catch(error => {
        // Show error
        walletDisplay.innerHTML = 'Error generating wallet';
        
        // Play error sound
        playSound('error-sound');
        
        // Show error dialog
        showErrorDialog(`Error: ${error.message}`);
    });
}