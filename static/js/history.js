// Refactored and full version of the script with added debugging capabilities and improvements.

const historyState = {
    currentPage: 1,
    hasMore: false,
    isLoading: false,
    searchParams: {
        query: '',
        type: 'content',
        dateFrom: '',
        dateTo: ''
    },
    debug: true // Enable debug mode for logging
};

function debugLog(...args) {
    if (historyState.debug) {
        console.log(...args);
    }
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return {
        full: date.toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }),
        time: date.toLocaleString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit'
        }),
        date: date.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    };
}

function createDateSeparator(dateStr) {
    const separator = document.createElement('div');
    separator.className = 'date-separator';
    separator.innerHTML = `<span>${dateStr}</span>`;
    return separator;
}

function createMessageElement(message) {
    const formattedDate = formatDate(message.received_date);
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_from_lead ? 'from-lead' : 'from-system'}`;

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-bubble">
                ${message.content}
            </div>
            <div class="message-metadata">
                <span class="message-time">${formattedDate.time}</span>
                ${!message.is_from_lead ? '<span class="message-status"><i class="fas fa-check-double"></i></span>' : ''}
            </div>
        </div>
    `;
    return messageDiv;
}

function showError(container, message) {
    container.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        </div>
    `;
}

async function loadMessages(leadId, page = 1) {
    if (historyState.isLoading) return;

    try {
        historyState.isLoading = true;
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> メッセージを読み込み中...';
        document.getElementById('messages').appendChild(loadingIndicator);

        // Build the URL with search parameters
        let url = `/history/api/leads/${leadId}/messages?page=${page}`;
        if (historyState.searchParams.query) {
            url += `&query=${encodeURIComponent(historyState.searchParams.query)}`;
            url += `&type=${encodeURIComponent(historyState.searchParams.type)}`;
            if (
                historyState.searchParams.type === 'date' &&
                historyState.searchParams.dateFrom &&
                historyState.searchParams.dateTo
            ) {
                url += `&date_from=${encodeURIComponent(historyState.searchParams.dateFrom)}`;
                url += `&date_to=${encodeURIComponent(historyState.searchParams.dateTo)}`;
            }
        }

        debugLog('Fetching messages from URL:', url);
        const response = await fetch(url);
        if (!response.ok) {
            debugLog('Response error status:', response.status, response.statusText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        debugLog('Messages data received:', data);
        const messagesContainer = document.getElementById('messages');
        loadingIndicator.remove();

        if (page === 1) {
            messagesContainer.innerHTML = '';
        }

        if (data.messages && Array.isArray(data.messages)) {
            let lastDate = null;
            data.messages.forEach(message => {
                const currentDate = new Date(message.received_date).toDateString();
                if (lastDate !== currentDate) {
                    messagesContainer.appendChild(createDateSeparator(formatDate(message.received_date).date));
                    lastDate = currentDate;
                }
                messagesContainer.appendChild(createMessageElement(message));
            });

            historyState.hasMore = data.has_next;
            const loadMoreButton = document.getElementById('loadMore');
            if (loadMoreButton) {
                loadMoreButton.style.display = historyState.hasMore ? 'block' : 'none';
            }
        } else {
            throw new Error('Invalid data format received from server');
        }
    } catch (error) {
        console.error('メッセージの読み込み中にエラーが発生しました:', error);
        showError(document.getElementById('messages'), 'メッセージの読み込みに失敗しました。再度お試しください。');
    } finally {
        historyState.isLoading = false;
    }
}

function setupSearch(leadId) {
    const searchInput = document.getElementById('messageSearch');
    const searchType = document.getElementById('searchType');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    const searchButton = document.getElementById('searchButton');

    searchType.addEventListener('change', () => {
        const isDateSearch = searchType.value === 'date';
        dateFrom.style.display = isDateSearch ? 'block' : 'none';
        dateTo.style.display = isDateSearch ? 'block' : 'none';
        searchInput.style.display = isDateSearch ? 'none' : 'block';
    });

    searchButton.addEventListener('click', () => {
        historyState.searchParams = {
            query: searchInput.value,
            type: searchType.value,
            dateFrom: dateFrom.value,
            dateTo: dateTo.value
        };
        historyState.currentPage = 1;
        loadMessages(leadId, 1);
    });

    searchInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') {
            searchButton.click();
        }
    });
}

// HTMLエスケープ関数
const escapeHtml = (str) => {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
};

// 安全なデータアクセス関数
const safeAccess = (obj, path, defaultValue = '') => {
    try {
        return path.split('.').reduce((acc, part) => acc[part], obj) || defaultValue;
    } catch (e) {
        return defaultValue;
    }
};

// 配列を安全にレンダリングする関数
const renderList = (items) => {
    if (!Array.isArray(items)) return '';
    return items.map(item => `<li>${escapeHtml(item)}</li>`).join('');
};


async function loadTimeline(leadId) {
    const timelineContainer = document.getElementById('timeline');
    try {
        debugLog('Starting to fetch timeline data');
        showLoading(true, timelineContainer);
        const response = await fetch(`/history/api/leads/${leadId}/timeline`);
        debugLog('Timeline response:', response);
        if (!response.ok) {
            console.error('Timeline response error:', response.status, response.statusText);
            throw new Error('タイムラインの取得に失敗しました');
        }

        const data = await response.json();
        debugLog('Timeline data received:', data);

        if (data.success) {
            if (data.timeline && Array.isArray(data.timeline) && data.timeline.length > 0) {
                displayTimelineEvents(data.timeline);
            } else {
                timelineContainer.innerHTML += `
                    <div class="no-events">
                        <i class="fas fa-info-circle"></i>
                        <p>タイムラインに表示するイベントがありません</p>
                    </div>
                `;
            }

            if (data.lead) {
                updateLeadInfo(data.lead);
            }
        } else {
            console.error('Server error fetching timeline:', data.error);
            throw new Error(data.error || 'データの取得に失敗しました');
        }
    } catch (error) {
        console.error('Timeline error:', error);
        showError(timelineContainer, error.message || 'タイムラインの読み込み中にエラーが発生しました');
    } finally {
        showLoading(false, timelineContainer);
    }
}

function showLoading(isLoading, container) {
    let loadingElement = container.querySelector('.loading');
    if (!loadingElement) {
        loadingElement = document.createElement('div');
        loadingElement.className = 'loading';
        loadingElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 読み込み中...';
        container.appendChild(loadingElement);
    }
    loadingElement.style.display = isLoading ? 'block' : 'none';
}

function getEventTypeStyle(eventType) {
    switch (eventType) {
        case 'email':
            return {
                color: 'lightblue',
                icon: 'fas fa-envelope'
            };
        case 'meeting':
            return {
                color: 'lightgreen',
                icon: 'fas fa-user-friends'
            };
        case 'call':
            return {
                color: 'lightcoral',
                icon: 'fas fa-phone'
            };
        default:
            return {
                color: 'lightgrey',
                icon: 'fas fa-info-circle'
            };
    }
}

function getEventMetadata(event) {
    // ここでイベントに基づいてメタデータを構築します
    return {
        timestamp: new Date(event.timestamp).toLocaleString(),
        description: event.description || '詳細がありません',
    };
}

function displayTimelineEvents(events) {
    const timelineContainer = document.getElementById('timeline');
    timelineContainer.innerHTML = '';
    
    // Sort events by timestamp in descending order
    events.sort((a, b) => b.timestamp - a.timestamp);
    
    let currentDate = null;
    events.forEach(event => {
        const eventDate = new Date(event.date).toLocaleDateString('ja-JP');
        if (currentDate !== eventDate) {
            const dateHeader = document.createElement('div');
            dateHeader.className = 'timeline-date-header';
            dateHeader.innerHTML = eventDate;
            timelineContainer.appendChild(dateHeader);
            currentDate = eventDate;
        }

        const eventStyle = getEventTypeStyle(event.type);
        const timelineItem = document.createElement('div');
        timelineItem.className = `timeline-event ${event.type}`;

        timelineItem.innerHTML = `
            <div class="event-icon" style="background-color: ${eventStyle.color}">
                <i class="fas ${eventStyle.icon}"></i>
            </div>
            <div class="event-content">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-time">${formatDate(event.date).time}</div>
                </div>
                <div class="event-description">${event.description.replace(/\n/g, '<br>')}</div>
                ${getEventMetadata(event)}
            </div>
        `;

        timelineContainer.appendChild(timelineItem);
    });

    if (events.length === 0) {
        timelineContainer.innerHTML = `
            <div class="no-events">
                <i class="fas fa-info-circle"></i>
                <p>タイムラインに表示するイベントがありません</p>
            </div>
        `;
    }
}

function updateLeadInfo(lead) {
    const leadInfoContainer = document.querySelector('.lead-info');
    if (leadInfoContainer && lead) {
        leadInfoContainer.innerHTML = `
            <h2>${lead.name || '名前なし'}</h2>
            <div class="lead-details">
                <div><i class="fas fa-envelope"></i> ${lead.email}</div>
                <div><i class="fas fa-info-circle"></i> ${lead.status}</div>
            </div>
        `;
    }
}

function initializeHistory(leadId) {
    loadMessages(leadId);
    setupSearch(leadId);
    loadTimeline(leadId);

    const loadMoreButton = document.getElementById('loadMore');
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', () => {
            if (historyState.hasMore && !historyState.isLoading) {
                historyState.currentPage++;
                loadMessages(leadId, historyState.currentPage);
            }
        });
    }

    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        let scrollTimeout;
        messagesContainer.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                sessionStorage.setItem(`scroll_position_${leadId}`, messagesContainer.scrollTop);
            }, 100);
        });

        const savedPosition = sessionStorage.getItem(`scroll_position_${leadId}`);
        if (savedPosition) {
            messagesContainer.scrollTop = parseInt(savedPosition);
        }
    }
}


// 修正されたカスタム分析結果の表示関数
function displayCustomAnalysisResults(data) {
    console.log('displayCustomAnalysisResults called with data:', data);

    const analysisContainer = document.getElementById('analysisContainer');
    const customAnalysisResults = document.getElementById('customAnalysisResults');
    const customInsightsElement = document.getElementById('customInsights');
    const analysisLoading = document.getElementById('analysisLoading');
    const analysisError = document.getElementById('analysisError');

    if (!analysisContainer || !customInsightsElement || !customAnalysisResults) {
        console.error('分析結果表示用の要素が見つかりません');
        return;
    }

    // ローディングやエラー表示を隠す
    if (analysisLoading) analysisLoading.style.display = 'none';
    if (analysisError) analysisError.style.display = 'none';

    // カスタム分析結果を表示
    customAnalysisResults.style.display = 'block';

    const customAnalysis = data.data ? data.data.custom_analysis : null;
    if (!customAnalysis) {
        console.error('Analysis property is missing in the response');
        customInsightsElement.innerHTML += '<p>カスタム分析結果の取得に失敗しました。</p>';
        return;
    }

    customInsightsElement.innerHTML += `
        <div class="analysis-section">
            <h4>カスタム分析結果</h4>
            <pre>${customAnalysis}</pre>
        </div>
    `;
}

// 修正された標準分析結果の表示関数
function displayStandardAnalysisResults(data) {
    console.log('displayStandardAnalysisResults called with data:', data);

    const analysisContainer = document.getElementById('analysisContainer');
    const standardAnalysisResults = document.getElementById('standardAnalysisResults');
    const standardInsights = document.getElementById('standardInsights');
    const analysisLoading = document.getElementById('analysisLoading');
    const analysisError = document.getElementById('analysisError');

    if (!analysisContainer || !standardInsights || !standardAnalysisResults) {
        console.error('Analysis display elements not found');
        return;
    }

    // ローディングやエラー表示を隠す
    if (analysisLoading) analysisLoading.style.display = 'none';
    if (analysisError) analysisError.style.display = 'none';

    // 標準分析結果を表示
    standardAnalysisResults.style.display = 'block';

    if (!data.data) {
        console.error('Data object is missing "data" property');
        standardInsights.innerHTML = '<p>分析結果の取得に失敗しました。</p>';
        return;
    }

    const { tasks, opportunities, communication, schedules } = data.data;

    standardInsights.innerHTML = `
        <div class="analysis-section">
            <h4>タスク分析</h4>
            <p>完了タスク数: ${tasks && tasks.completed_tasks ? tasks.completed_tasks : '不明'}</p>
            <p>完了率: ${tasks && tasks.completion_rate ? tasks.completion_rate : '不明'}%</p>
            <p>総タスク数: ${tasks && tasks.total_tasks ? tasks.total_tasks : '不明'}</p>
        </div>
        <div class="analysis-section">
            <h4>商談分析</h4>
            <p>総商談数: ${opportunities && opportunities.total_opportunities ? opportunities.total_opportunities : '不明'}</p>
            <p>総額: ${opportunities && opportunities.total_amount ? opportunities.total_amount.toLocaleString() : '不明'}円</p>
            <p>平均額: ${opportunities && opportunities.average_amount ? opportunities.average_amount.toLocaleString() : '不明'}円</p>
        </div>
        <div class="analysis-section">
            <h4>コミュニケーション分析</h4>
            <p>メール送信数: ${communication && communication.sent_emails ? communication.sent_emails : '不明'}件</p>
            <p>メール受信数: ${communication && communication.received_emails ? communication.received_emails : '不明'}件</p>
            <p>総メール数: ${communication && communication.total_emails ? communication.total_emails : '不明'}件</p>
            <p>最終連絡日: ${communication && communication.last_contact ? new Date(communication.last_contact).toLocaleDateString('ja-JP') : '不明'}</p>
        </div>
        <div class="analysis-section">
            <h4>スケジュール分析</h4>
            <p>総スケジュール数: ${schedules && schedules.total_schedules ? schedules.total_schedules : '不明'}</p>
            <p>最近のスケジュール数: ${schedules && schedules.recent_schedules ? schedules.recent_schedules : '不明'}</p>
            <p>今後のスケジュール数: ${schedules && schedules.upcoming_schedules ? schedules.upcoming_schedules : '不明'}</p>
        </div>
    `;
}