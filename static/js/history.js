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