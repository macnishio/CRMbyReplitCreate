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
            if (historyState.searchParams.type === 'date' && 
                historyState.searchParams.dateFrom && 
                historyState.searchParams.dateTo) {
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
        showError('メッセージの読み込みに失敗しました。再度お試しください。');
    } finally {
        historyState.isLoading = false;
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
        <div class="message-bubble">
            ${message.content}
        </div>
        <div class="message-metadata">
            <span class="message-time">${formattedDate.time}</span>
            ${message.is_from_lead ? '<span class="message-status"><i class="fas fa-check-double"></i></span>' : ''}
        </div>
    `;

    return messageDiv;
}

function showError(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
    `;

    const messagesContainer = document.getElementById('messages');
    messagesContainer.appendChild(errorElement);
    setTimeout(() => errorElement.remove(), 3000);
}

function setupSearch(leadId) {
    const searchInput = document.getElementById('messageSearch');
    const searchType = document.getElementById('searchType');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    const searchButton = document.getElementById('searchButton');

    // 検索タイプが変更された時の処理
    searchType.addEventListener('change', () => {
        const isDateSearch = searchType.value === 'date';
        dateFrom.style.display = isDateSearch ? 'block' : 'none';
        dateTo.style.display = isDateSearch ? 'block' : 'none';
        searchInput.style.display = isDateSearch ? 'none' : 'block';
    });

    // 検索ボタンクリック時の処理
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

    // Enterキーでの検索実行
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchButton.click();
        }
    });
}

function initializeHistory(leadId) {
    const loadMoreButton = document.getElementById('loadMore');
    const messagesContainer = document.getElementById('messages');

    setupSearch(leadId);

    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', () => {
            if (historyState.hasMore && !historyState.isLoading) {
                historyState.currentPage++;
                loadMessages(leadId, historyState.currentPage);
            }
        });
    }

    if (messagesContainer) {
        let scrollTimeout;
        messagesContainer.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                localStorage.setItem(`scroll_position_${leadId}`, messagesContainer.scrollTop);
            }, 100);
        });

        loadMessages(leadId).then(() => {
            const savedPosition = localStorage.getItem(`scroll_position_${leadId}`);
            if (savedPosition) {
                messagesContainer.scrollTop = parseInt(savedPosition);
            }
        });
    }

    window.addEventListener('beforeunload', () => {
        localStorage.removeItem(`scroll_position_${leadId}`);
    });
}


async function analyzeCustomerBehavior() {
    const leadId = window.location.pathname.split('/').pop();
    const analysisResults = document.getElementById('analysisResults');
    const analysisData = document.getElementById('analysisData');
    
    try {
        const response = await fetch(`/history/api/leads/${leadId}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('分析中にエラーが発生しました');
        }
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            analysisData.innerHTML = `
                <div class="analysis-section">
                    <h4>コミュニケーションパターン</h4>
                    <p>頻度: ${data.communication_patterns.frequency}</p>
                    <p>好みの時間帯: ${data.communication_patterns.preferred_time}</p>
                    <p>応答時間: ${data.communication_patterns.response_time}</p>
                    <p>エンゲージメントレベル: ${data.communication_patterns.engagement_level}</p>
                </div>
                
                <div class="analysis-section">
                    <h4>興味・関心事項</h4>
                    <ul>
                        ${data.interests.map(interest => `<li>${interest}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="analysis-section">
                    <h4>重要ポイント</h4>
                    <ul>
                        ${data.key_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="analysis-section">
                    <h4>リスクファクター</h4>
                    <ul>
                        ${data.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="analysis-section">
                    <h4>推奨アクション</h4>
                    <ul>
                        ${data.recommended_actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="analysis-section">
                    <h4>分析サマリー</h4>
                    <p>${data.analysis_summary}</p>
                </div>
            `;
            
            analysisResults.style.display = 'block';
        } else {
            throw new Error(result.error || '分析に失敗しました');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        alert(error.message);
    }
}

// AI分析関連の処理を追加
function displayAnalysisResult(data) {
    const analysisResult = document.getElementById('analysisResult');

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
                            <i class="fas fa-exclamation-circle text-destructive"></i>
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
    </div>`;

    analysisResult.innerHTML = html;
    analysisResult.style.display = 'block';
    document.getElementById('analysisPlaceholder').style.display = 'none';
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

// AI分析ボタンのイベントハンドラー内で使用
runAnalysisBtn.addEventListener('click', async () => {
    try {
        runAnalysisBtn.disabled = true;
        analysisPlaceholder.textContent = '分析中...';

        const response = await fetch(`/history/leads/${leadId}/analyze`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('分析に失敗しました');

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        displayAnalysisResult(data.data);
    } catch (error) {
        console.error('Analysis Error:', error);
        analysisPlaceholder.textContent = `エラーが発生しました: ${error.message}`;
    } finally {
        runAnalysisBtn.disabled = false;
    }
});
// Timeline functionality
function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }).format(date);
    } catch (e) {
        console.error('Date formatting error:', e);
        return dateStr;
    }
}

function showError(container, message, code) {
    container.innerHTML = `
        <div class="timeline-error">
            <i class="fas fa-exclamation-circle"></i>
            <div class="error-message">${message}</div>
            ${code ? `<div class="error-code">${code}</div>` : ''}
        </div>
    `;
}

function showLoading(show = true) {
const loadingIndicator = document.querySelector('.timeline .loading');
const timelineContainer = document.getElementById('timeline');

async function loadTimeline(leadId) {
    showLoading(true);
    try {
        const response = await fetch(`/history/api/leads/${leadId}/timeline`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'タイムラインの読み込みに失敗しました');
        }

        renderTimeline(data.timeline);
    } catch (error) {
        console.error('Timeline error:', error);
        showError(timelineContainer, error.message, error.code);
    } finally {
        showLoading(false);
    }
}

function renderTimeline(events) {
    if (!events || events.length === 0) {
        timelineContainer.innerHTML = `
            <div class="timeline-empty">
                <i class="fas fa-info-circle"></i>
                <p>イベントがありません</p>
            </div>
        `;
        return;
    }

    timelineContainer.innerHTML = events.map(event => `
        <div class="timeline-item">
            <div class="timeline-icon">
                <i class="fas ${event.icon || 'fa-circle'}"></i>
            </div>
            <div class="timeline-content">
                <div class="timeline-header">
                    <h4 class="timeline-title">${event.title}</h4>
                    <span class="timeline-date">${formatDate(event.date)}</span>
                </div>
                <div class="timeline-description">${event.description}</div>
                ${event.metadata ? `
                    <div class="timeline-metadata">
                        ${Object.entries(event.metadata)
                            .filter(([_, value]) => value !== null)
                            .map(([key, value]) => `
                                <div class="metadata-item">
                                    <span class="metadata-label">${key}:</span>
                                    <span class="metadata-value">${value}</span>
                                </div>
                            `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Initialize timeline when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const leadId = window.location.pathname.split('/').pop();
    if (leadId) {
        loadTimeline(leadId);
    }
});
    const loadingElement = document.querySelector('.timeline-loading');
    if (loadingElement) {
        loadingElement.style.display = show ? 'block' : 'none';
    }
}

async function loadTimeline() {
    const timelineContainer = document.getElementById('timeline-events');
    const loadingElement = document.querySelector('.timeline-loading');

    if (!timelineContainer || !loadingElement) {
        console.error('Required DOM elements not found');
        return;
    }

    try {
        const pathParts = window.location.pathname.split('/');
        const leadId = pathParts[pathParts.indexOf('leads') + 1];
        
        if (!leadId) {
            throw new Error('リードIDが見つかりません');
        }

        showLoading(true);

        const response = await fetch(`/history/api/leads/${leadId}/timeline`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || `サーバーエラー: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            showLoading(false);
            if (Array.isArray(data.timeline)) {
                displayTimelineEvents(data.timeline);
            } else {
                console.error('Invalid timeline data format:', data);
                throw new Error('タイムラインデータの形式が不正です');
            }
            
            if (data.lead) {
                updateLeadInfo(data.lead);
            }
        } else {
            throw new Error(data.error || 'データの取得に失敗しました');
        }
    } catch (error) {
        console.error('Timeline error:', error);
        showLoading(false);
        showError(timelineContainer, 
            error.message || 'タイムラインの読み込み中にエラーが発生しました',
            error.code || 'UNKNOWN_ERROR');
    }
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
        }
    };
    return styles[type] || { icon: 'fa-circle', color: 'var(--color-primary)' };
}

function displayTimelineEvents(events) {
    const timelineContainer = document.getElementById('timeline-events');
    if (!events || !timelineContainer) return;

    if (events.length === 0) {
        timelineContainer.innerHTML = `
            <div class="timeline-empty">
                <i class="fas fa-info-circle"></i>
                <p>タイムラインに表示するイベントがありません</p>
            </div>
        `;
        return;
    }

    const eventsHtml = events.map(event => {
        const style = getEventTypeStyle(event.type);
        return `
            <div class="timeline-event ${event.type}" style="border-left-color: ${style.color}">
                <div class="event-icon" style="background-color: ${style.color}">
                    <i class="fas ${event.icon || style.icon}"></i>
                </div>
                <div class="event-content">
                    <div class="event-title">${event.title}</div>
                    <div class="event-description">${event.description}</div>
                    <div class="event-date">
                        <i class="fas fa-clock"></i>
                        ${formatDate(event.date)}
                    </div>
                    ${event.metadata ? `
                        <div class="event-metadata">
                            ${Object.entries(event.metadata)
                                .filter(([_, value]) => value !== null)
                                .map(([key, value]) => `
                                    <span class="metadata-item">
                                        <strong>${key}:</strong> ${value}
                                    </span>
                                `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    timelineContainer.innerHTML = eventsHtml;
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

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const isLeadDetailPage = pathParts.includes('leads') && !isNaN(pathParts[pathParts.length - 1]);
    
    if (isLeadDetailPage) {
        loadTimeline();
        
        // 分析ボタンの初期化（リード詳細ページの場合のみ）
        const runAnalysisBtn = document.getElementById('runAnalysisBtn');
        if (runAnalysisBtn) {
            runAnalysisBtn.addEventListener('click', function() {
                const leadId = pathParts[pathParts.length - 1];
                analyzeLeadBehavior(leadId);
            });
        }
    }
});

// history.js に追加
async function loadTimeline(leadId) {
    const timelineContainer = document.getElementById('timeline-events');
    const loadingElement = document.querySelector('.timeline-loading');

    try {
        const response = await fetch(`/history/api/leads/${leadId}/timeline`);
        if (!response.ok) throw new Error('Failed to load timeline');

        const data = await response.json();
        if (!data.success) throw new Error(data.error || 'Failed to load timeline');

        loadingElement.style.display = 'none';

        // タイムラインイベントを表示
        if (data.timeline && data.timeline.length > 0) {
            const eventsHtml = data.timeline.map(event => `
                <div class="timeline-event ${event.type}">
                    <div class="event-icon">
                        <i class="fas ${getEventIcon(event.type)}"></i>
                    </div>
                    <div class="event-content">
                        <div class="event-title">${event.title}</div>
                        <div class="event-description">${event.description}</div>
                        <div class="event-date">${formatDate(event.date)}</div>
                        ${getEventMetadata(event)}
                    </div>
                </div>
            `).join('');

            timelineContainer.innerHTML = eventsHtml;
        } else {
            timelineContainer.innerHTML = '<div class="no-events">タイムラインイベントがありません</div>';
        }

    } catch (error) {
        console.error('Timeline loading error:', error);
        loadingElement.style.display = 'none';
        timelineContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                タイムラインの読み込み中にエラーが発生しました
            </div>
        `;
    }
}

function getEventIcon(type) {
    const icons = {
        email: 'fa-envelope',
        status_change: 'fa-exchange-alt',
        score_update: 'fa-chart-line',
        behavior_analysis: 'fa-brain'
    };
    return icons[type] || 'fa-circle';
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
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

// 初期化関数を更新
function initializeHistory(leadId) {
    // 既存のコード...

    // タイムラインの読み込みを追加
    if (document.getElementById('timeline-events')) {
        loadTimeline(leadId);
    }
}