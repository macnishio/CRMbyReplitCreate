document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('leadFilterForm');
  const filterActions = document.querySelector('.filter-actions');

  // Add loading class during form submission
  filterForm.addEventListener('submit', function() {
    filterForm.classList.add('loading');
  });

  // Add input event listeners for real-time validation
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach(input => {
    input.addEventListener('input', function() {
      if (this.value < 0) {
        this.value = 0;
      }
    });
  });

  // Date range validation
  const dateFrom = document.getElementsByName('date_from')[0];
  const dateTo = document.getElementsByName('date_to')[0];

  if (dateFrom && dateTo) {
    dateFrom.addEventListener('change', function() {
      if (dateTo.value && this.value > dateTo.value) {
        this.value = dateTo.value;
      }
    });

    dateTo.addEventListener('change', function() {
      if (dateFrom.value && this.value < dateFrom.value) {
        this.value = dateFrom.value;
      }
    });
  }

  // Add debounced auto-submit for search input
  const searchInput = document.getElementById('search_name');
  let debounceTimer;

  if (searchInput) {
    searchInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        filterForm.submit();
      }, 500);
    });
  }

  // Toggle filter group content visibility
  function toggleFilterGroup(groupId) {
    const content = document.querySelector(`#${groupId}-content`);
    const icon = document.querySelector(`#${groupId}-icon`);

    if (content && icon) {
      content.classList.toggle('active');

      if (content.classList.contains('active')) {
        icon.textContent = '▼';
        content.style.display = 'block';
      } else {
        icon.textContent = '▶';
        content.style.display = 'none';
      }
    }
  }

  // Toggle all checkboxes
  function toggleAllCheckboxes() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.lead-checkbox');

    checkboxes.forEach(checkbox => {
      checkbox.checked = selectAll.checked;
    });
  }

  // Bulk action handling
  const bulkActionSelect = document.getElementById('bulk-action');

  if (bulkActionSelect) {
    bulkActionSelect.addEventListener('change', function() {
      const newStatusSelect = document.getElementById('new-status');
      const newScoreInput = document.getElementById('new-score');

      if (newStatusSelect && newScoreInput) {
        newStatusSelect.style.display = this.value === 'change_status' ? 'inline-block' : 'none';
        newScoreInput.style.display = this.value === 'update_score' ? 'inline-block' : 'none';
      }
    });
  }

  // Confirm bulk action before submission
  window.confirmBulkAction = function() {
    const action = document.getElementById('bulk-action').value;
    if (!action) {
      alert('操作を選択してください。');
      return false;
    }
    return true;
  };
});
