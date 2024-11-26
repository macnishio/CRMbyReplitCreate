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
function loadTimeline() {
    const leadId = window.location.pathname.split('/').pop();
    const timelineContainer = document.getElementById('timeline-events');
    const loadingElement = document.querySelector('.timeline-loading');

    if (!timelineContainer || !loadingElement) return;

    fetch(`/history/api/leads/${leadId}/timeline`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadingElement.style.display = 'none';
                displayTimelineEvents(data.timeline);
            } else {
                throw new Error(data.error || 'タイムラインの読み込みに失敗しました');
            }
        })
        .catch(error => {
            console.error('Timeline error:', error);
            loadingElement.innerHTML = `<div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                タイムラインの読み込み中にエラーが発生しました
            </div>`;
        });
}

function displayTimelineEvents(events) {
    const timelineContainer = document.getElementById('timeline-events');
    if (!events || !timelineContainer) return;

    const eventsHtml = events.map(event => `
        <div class="timeline-event ${event.type}">
            <div class="event-icon">
                <i class="fas ${event.icon}"></i>
            </div>
            <div class="event-content">
                <div class="event-title">${event.title}</div>
                <div class="event-description">${event.description}</div>
                <div class="event-date">${new Date(event.date).toLocaleString('ja-JP')}</div>
            </div>
        </div>
    `).join('');

    timelineContainer.innerHTML = eventsHtml;
}

// Call loadTimeline when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadTimeline();
});