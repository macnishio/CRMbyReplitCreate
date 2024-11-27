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

function getEventTypeStyle(type) {
    const styles = {
        email: {
            icon: 'fa-envelope',
            color: 'var(--color-info)'
        },
        status_change: {
            icon: 'fa-exchange-alt',
            color: 'var(--color-warning)'
        },
        score_update: {
            icon: 'fa-chart-line',
            color: 'var(--color-success)'
        },
        behavior_analysis: {
            icon: 'fa-brain',
            color: '#9c27b0'
        },
        opportunity: {
            icon: 'fa-handshake',
            color: '#ff9800'
        },
        opportunity_stage_change: {
            icon: 'fa-exchange-alt',
            color: '#ff9800'
        },
        task: {
            icon: 'fa-tasks',
            color: '#4caf50'
        },
        task_status_change: {
            icon: 'fa-check-circle',
            color: '#4caf50'
        },
        schedule: {
            icon: 'fa-calendar',
            color: '#2196f3'
        },
        schedule_status_change: {
            icon: 'fa-clock',
            color: '#2196f3'
        }
    };
    return styles[type] || { icon: 'fa-circle', color: 'var(--color-primary)' };
}

function getEventMetadata(event) {
    if (!event.metadata) return '';

    let metadataHtml = '';
    switch (event.type) {
        case 'task':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="status">${event.metadata.status}</span>
                    ${event.metadata.priority ? `<span class="priority">優先度: ${event.metadata.priority}</span>` : ''}
                    ${event.metadata.due_date ? `<span class="due-date">期限: ${event.metadata.due_date}</span>` : ''}
                </div>
            `;
            break;
        case 'task_status_change':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="status-change">
                        <span class="old-status">${event.metadata.old_status}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="new-status">${event.metadata.new_status}</span>
                    </span>
                </div>
            `;
            break;
        case 'opportunity':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="stage">ステージ: ${event.metadata.stage}</span>
                    <span class="amount">金額: ¥${Number(event.metadata.amount).toLocaleString()}</span>
                    ${event.metadata.close_date ? `<span class="close-date">完了予定日: ${event.metadata.close_date}</span>` : ''}
                </div>
            `;
            break;
        case 'opportunity_stage_change':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="stage-change">
                        <span class="old-stage">${event.metadata.old_stage}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="new-stage">${event.metadata.new_stage}</span>
                    </span>
                </div>
            `;
            break;
        case 'schedule':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="schedule-type">${event.metadata.type || '予定'}</span>
                    ${event.metadata.start_date ? `<span class="start-date">開始: ${event.metadata.start_date}</span>` : ''}
                    ${event.metadata.end_date ? `<span class="end-date">終了: ${event.metadata.end_date}</span>` : ''}
                    ${event.metadata.location ? `<span class="location">場所: ${event.metadata.location}</span>` : ''}
                </div>
            `;
            break;
        case 'schedule_status_change':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="status-change">
                        <span class="old-status">${event.metadata.old_status}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="new-status">${event.metadata.new_status}</span>
                    </span>
                </div>
            `;
            break;
        case 'status_change':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="old-status">${event.metadata.old_status}</span>
                    <i class="fas fa-arrow-right"></i>
                    <span class="new-status">${event.metadata.new_status}</span>
                </div>
            `;
            break;
        case 'score_update':
            metadataHtml = `
                <div class="event-metadata">
                    <span class="score-change">スコア: ${event.metadata.old_score || '?'} → ${event.metadata.new_score}</span>
                </div>
            `;
            break;
    }
    return metadataHtml;
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

function initializeAnalysis() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeCustomerBehavior);
    }
}

async function analyzeCustomerBehavior() {
    debugLog('analyzeCustomerBehavior function called.');
    const analysisResults = document.getElementById('analysisResults');
    const analysisData = document.getElementById('analysisData');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    try {
        // URLからリードIDを取得と検証
        const pathParts = window.location.pathname.split('/');
        const leadId = pathParts[pathParts.length - 1];
        
        if (!leadId || isNaN(leadId)) {
            throw new Error('リードIDが無効です');
        }

        // 分析開始前の状態を設定
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
        analysisResults.style.display = 'block';
        analysisData.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> AI分析を実行中...</div>';

        // API呼び出し
        const response = await fetch(`/history/api/leads/${leadId}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            if (response.status === 404) {
                throw new Error('指定されたリードが見つかりません');
            } else if (response.status === 400) {
                throw new Error(errorData.error || 'リクエストが無効です');
            } else {
                throw new Error(errorData.error || 'AI分析中にエラーが発生しました');
            }
        }

        const data = await response.json();
        
        if (!data) {
            throw new Error('分析データを取得できませんでした');
        }

        // 部分的なデータがある場合は表示
        let hasAnyData = data.communication_pattern || 
                        data.behavior_prediction || 
                        data.recommended_actions;

        if (!hasAnyData) {
            throw new Error('分析データが見つかりませんでした');
        }
        
        // 分析結果の表示
        analysisData.innerHTML = `
            <div class="analysis-section">
                <h4>コミュニケーションパターン分析</h4>
                <p>${data.communication_pattern || '分析データがありません'}</p>
            </div>
            <div class="analysis-section">
                <h4>行動予測</h4>
                <p>${data.behavior_prediction || '予測データがありません'}</p>
            </div>
            <div class="analysis-section">
                <h4>推奨アクション</h4>
                <p>${data.recommended_actions || '推奨データがありません'}</p>
            </div>
        `;

    } catch (error) {
        console.error('AI分析エラー:', error);
        analysisData.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>${error.message || 'AI分析中にエラーが発生しました'}</p>
                <button onclick="retryAnalysis()" class="retry-button">
                    <i class="fas fa-sync"></i> 再試行
                </button>
            </div>
        `;
    } finally {
        // ボタンを元の状態に戻す
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-brain"></i> AI分析';
    }
}

// 分析の再試行関数
function retryAnalysis() {
    const analysisData = document.getElementById('analysisData');
    if (analysisData) {
        analysisData.innerHTML = '';
    }
    analyzeCustomerBehavior();
}

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
        timelineContainer.innerHTML = '';

        if (Array.isArray(data)) {
            displayTimelineEvents(data);
        } else {
            throw new Error('無効なデータ形式です');
        }
    } catch (error) {
        console.error('Timeline error:', error);
        showError(timelineContainer, error.message || 'タイムラインの読み込み中にエラーが発生しました');
    } finally {
        showLoading(false, timelineContainer);
    }
}

function displayTimelineEvents(events) {
    const timelineContainer = document.getElementById('timeline');
    timelineContainer.innerHTML = '';
    
    if (!events || events.length === 0) {
        timelineContainer.innerHTML = `
            <div class="no-events">
                <i class="fas fa-info-circle"></i>
                <p>タイムラインに表示するイベントがありません</p>
            </div>
        `;
        return;
    }

    events.sort((a, b) => new Date(b.date) - new Date(a.date));

    events.forEach(event => {
        const eventStyle = getEventTypeStyle(event.type);
        const timelineItem = document.createElement('div');
        timelineItem.className = 'timeline-event';

        timelineItem.innerHTML = `
            <div class="event-icon" style="background-color: ${eventStyle.color}">
                <i class="fas ${eventStyle.icon}"></i>
            </div>
            <div class="event-content">
                <div class="event-title">${event.title}</div>
                <div class="event-description">${event.description}</div>
                <div class="event-date">
                    <i class="fas fa-clock"></i>
                    ${formatDate(event.date).full}
                </div>
                ${getEventMetadata(event)}
            </div>
        `;

        timelineContainer.appendChild(timelineItem);
    });
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
    debugLog('Initializing history view for lead:', leadId);
    loadMessages(leadId);
    setupSearch(leadId);
    loadTimeline(leadId);
    initializeAnalysis();

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

document.addEventListener('DOMContentLoaded', () => {
    const pathParts = window.location.pathname.split('/');
    const leadIdIndex = pathParts.indexOf('leads') + 1;
    const leadId = pathParts[leadIdIndex];

    if (leadId && !isNaN(leadId)) {
        initializeHistory(leadId);
    }
});

export { initializeHistory };