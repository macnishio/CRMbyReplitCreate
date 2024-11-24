// モバイルフィルター用のJavaScript
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    const activeFilters = document.createElement('div');
    activeFilters.className = 'active-filters';
    filterForm.appendChild(activeFilters);

    // フィルタータグの作成と管理
    function updateFilterTags() {
        activeFilters.innerHTML = '';
        const formData = new FormData(filterForm);

        for (let [key, value] of formData.entries()) {
            if (value && key !== 'sort_order' && key !== 'page') {
                const tag = document.createElement('span');
                tag.className = 'filter-tag';
                
                // フィルター名の日本語化
                const filterName = {
                    'status': 'ステータス',
                    'date_range': '期間',
                    'lead_search': 'リード検索',
                    'date_from': '開始日',
                    'date_to': '終了日'
                }[key] || key;

                tag.innerHTML = `
                    ${filterName}: ${value}
                    <button type="button" class="remove-filter" data-filter="${key}" aria-label="フィルターを削除">
                        ×
                    </button>
                `;
                activeFilters.appendChild(tag);
            }
        }
    }

    // フィルタープリセットの設定
    const presets = {
        'today': {
            date_range: 'today',
            status: ''
        },
        'pending': {
            status: 'Pending',
            date_range: ''
        },
        'this_week': {
            date_range: 'week',
            status: ''
        }
    };

    // プリセットボタンの作成
    const filterPresets = document.createElement('div');
    filterPresets.className = 'filter-presets';
    Object.keys(presets).forEach(preset => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'preset-button';
        button.textContent = {
            'today': '今日',
            'pending': '保留中',
            'this_week': '今週'
        }[preset];
        
        button.addEventListener('click', () => {
            Object.entries(presets[preset]).forEach(([key, value]) => {
                const input = filterForm.elements[key];
                if (input) {
                    input.value = value;
                }
            });
            filterForm.requestSubmit();
        });
        
        filterPresets.appendChild(button);
    });
    filterForm.insertBefore(filterPresets, filterForm.firstChild);

    // フィルター削除の処理
    activeFilters.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-filter')) {
            const filterKey = e.target.dataset.filter;
            const input = filterForm.elements[filterKey];
            if (input) {
                input.value = '';
                filterForm.requestSubmit();
            }
        }
    });

    // フォーム変更時のイベント処理
    filterForm.addEventListener('change', () => {
        updateFilterTags();
    });

    // 初期フィルタータグの表示
    updateFilterTags();

    // タッチイベントの最適化
    const touchElements = filterForm.querySelectorAll('select, input, button');
    touchElements.forEach(element => {
        element.addEventListener('touchstart', function(e) {
            e.target.style.opacity = '0.7';
        });

        element.addEventListener('touchend', function(e) {
            e.target.style.opacity = '1';
        });
    });
});
