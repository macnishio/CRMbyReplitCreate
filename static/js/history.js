// static/js/history.js

const historyState = {
    currentPage: 1,
    hasMore: false,
    isLoading: false,
    searchParams: {
        query: '',
        type: 'content',
        dateFrom: '',
        dateTo: ''
    }
};

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

        // 検索パラメータを含むURLを構築
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

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
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

// Timeline functions
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
        }
    };
    return styles[type] || { icon: 'fa-circle', color: 'var(--color-primary)' };
}

async function loadTimeline(leadId) {
    const timelineContainer = document.getElementById('timeline');
    try {
        showLoading(true);
        const response = await fetch(`/history/api/leads/${leadId}/timeline`);
        if (!response.ok) throw new Error('タイムラインの取得に失敗しました');

        const data = await response.json();

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
            throw new Error(data.error || 'データの取得に失敗しました');
        }
    } catch (error) {
        console.error('Timeline error:', error);
        showError(timelineContainer, error.message || 'タイムラインの読み込み中にエラーが発生しました');
    } finally {
        showLoading(false);
    }
}

function showLoading(isLoading) {
    const loadingElement = document.querySelector('#timeline .loading');
    if (loadingElement) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
    }
}

function displayTimelineEvents(events) {
    const timelineContainer = document.getElementById('timeline');
    // 既存のタイムラインイベントをクリア
    timelineContainer.innerHTML = '';
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

function getEventMetadata(event) {
    if (!event.metadata) return '';

    let metadataHtml = '';
    switch (event.type) {
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

// AI Analysis Functions
async function analyzeCustomerBehavior() {
    const pathParts = window.location.pathname.split('/');
    const leadIdIndex = pathParts.indexOf('leads') + 1;
    const leadId = pathParts[leadIdIndex];

    const analysisResults = document.getElementById('analysisResults');
    const analysisData = document.getElementById('analysisData');

    try {
        analysisResults.style.display = 'block';
        analysisData.innerHTML =
            '<div class="loading"><i class="fas fa-spinner fa-spin"></i> AI分析を実行中...</div>';

        const response = await fetch(`/history/api/leads/${leadId}/analyze`, {
            method: 'POST'
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '分析中にエラーが発生しました');
        }

        const result = await response.json();
        if (result.error) throw new Error(result.error);

        displayAnalysisResult(result.data);
    } catch (error) {
        console.error('Analysis error:', error);
        analysisData.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <span>${error.message}</span>
            </div>
        `;
    }
}

function displayAnalysisResult(data) {
    const analysisData = document.getElementById('analysisData');

    let html = `
        <div class="analysis-grid">
            <!-- コミュニケーションパターン -->
            <div class="analysis-card wide">
                <div class="card-header">
                    <i class="fas fa-comments text-primary"></i>
                    <h4>コミュニケーションパターン</h4>
                </div>
                <div class="card-content">
                    <div class="metrics-grid">
                        ${createMetricCard('頻度', data.communication_patterns.frequency, 'fa-clock')}
                        ${createMetricCard('好みの時間帯', data.communication_patterns.preferred_time, 'fa-sun')}
                        ${createMetricCard('応答時間', data.communication_patterns.response_time, 'fa-hourglass-half')}
                        ${createMetricCard('エンゲージメント', data.communication_patterns.engagement_level, 'fa-chart-line', true)}
                    </div>
                </div>
            </div>

            <!-- 興味・関心事項 -->
            <div class="analysis-card">
                <div class="card-header">
                    <i class="fas fa-star text-primary"></i>
                    <h4>興味・関心事項</h4>
                </div>
                <div class="card-content scroll-area">
                    <div class="tag-cloud">
                        ${data.interests.map(interest => `
                            <span class="badge">${interest}</span>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- 重要ポイント -->
            <div class="analysis-card">
                <div class="card-header">
                    <i class="fas fa-key text-primary"></i>
                    <h4>重要ポイント</h4>
                </div>
                <div class="card-content scroll-area">
                    <ul class="point-list">
                        ${data.key_points.map(point => `
                            <li>
                                <span class="bullet"></span>
                                <span>${point}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>

            <!-- リスクファクター -->
            <div class="analysis-card">
                <div class="card-header">
                    <i class="fas fa-exclamation-triangle text-destructive"></i>
                    <h4>リスクファクター</h4>
                </div>
                <div class="card-content scroll-area">
                    <ul class="risk-list">
                        ${data.risk_factors.map(risk => `
                            <li>
                                <span class="bullet"></span>
                                <span>${risk}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>

            <!-- 推奨アクション -->
            <div class="analysis-card wide">
                <div class="card-header">
                    <i class="fas fa-lightbulb text-primary"></i>
                    <h4>推奨アクション</h4>
                </div>
                <div class="card-content">
                    <div class="action-grid">
                        ${data.recommended_actions.map(action => `
                            <div class="action-item">
                                <span class="bullet"></span>
                                <span>${action}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- 分析サマリー -->
            <div class="analysis-card wide">
                <div class="card-header">
                    <i class="fas fa-chart-bar text-primary"></i>
                    <h4>分析サマリー</h4>
                </div>
                <div class="card-content">
                    <p class="summary-text">${data.analysis_summary.replace(/\n/g, '<br>')}</p>
                </div>
            </div>
        </div>
    `;

    analysisData.innerHTML = html;
}

function createMetricCard(label, value, iconClass, highlight = false) {
    return `
        <div class="metric-card ${highlight ? 'highlight' : ''}">
            <div class="metric-header">
                <i class="fas ${iconClass}"></i>
                <span class="metric-label">${label}</span>
            </div>
            <div class="metric-value">${value || 'N/A'}</div>
        </div>
    `;
}

// Initialization functions
function initializeAnalysis() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeCustomerBehavior);
    }
}

function initializeHistory(leadId) {
    loadMessages(leadId);
    setupSearch(leadId);

    const timelineContainer = document.getElementById('timeline-events');
    if (timelineContainer) {
        loadTimeline(leadId);
    }

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
                localStorage.setItem(`scroll_position_${leadId}`, messagesContainer.scrollTop);
            }, 100);
        });

        const savedPosition = localStorage.getItem(`scroll_position_${leadId}`);
        if (savedPosition) {
            messagesContainer.scrollTop = parseInt(savedPosition);
        }
    }
}

// DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    const pathParts = window.location.pathname.split('/');
    const leadIdIndex = pathParts.indexOf('leads') + 1;
    const leadId = pathParts[leadIdIndex];

    if (leadId && !isNaN(leadId)) {
        initializeHistory(leadId);
    }
});
