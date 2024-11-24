document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filterForm');
  const resetButton = document.querySelector('button[onclick="resetFilters()"]');
  const exportButton = document.querySelector('button[onclick="exportOpportunities()"]');
  const searchInput = document.getElementById('lead_search');
  const dateFrom = document.getElementsByName('date_from')[0];
  const dateTo = document.getElementsByName('date_to')[0];

  // Add loading class during form submission
  if (filterForm) {
    filterForm.addEventListener('submit', function(e) {
      if (filterForm.classList) {
        filterForm.classList.add('loading');
      }
    });
  }

  // Reset filters function
  window.resetFilters = function() {
    const form = document.getElementById('filterForm');
    if (form) {
      form.reset();

      // Clear range inputs if they exist
      const minAmount = document.getElementsByName('min_amount')[0];
      const maxAmount = document.getElementsByName('max_amount')[0];
      if (minAmount) minAmount.value = '';
      if (maxAmount) maxAmount.value = '';
      if (dateFrom) dateFrom.value = '';
      if (dateTo) dateTo.value = '';

      form.submit();
    }
  };

  // Export opportunities function
  window.exportOpportunities = function() {
    if (!filterForm) return;

    const exportBtn = document.querySelector('.btn-info');
    if (exportBtn) {
      exportBtn.disabled = true;
      exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> エクスポート中...';
    }

    const formData = new FormData(filterForm);
    const params = new URLSearchParams(formData);
    params.append('export', 'true');
    window.location.href = `${window.location.pathname}?${params.toString()}`;

    if (exportBtn) {
      setTimeout(() => {
        exportBtn.disabled = false;
        exportBtn.innerHTML = '<i class="fas fa-file-export"></i> エクスポート';
      }, 2000);
    }
  };

  // Add input event listeners for real-time validation
  const numberInputs = document.querySelectorAll('input[type="number"]');
  if (numberInputs.length > 0) {
    numberInputs.forEach(input => {
      input.addEventListener('input', function() {
        if (this.value < 0) {
          this.value = 0;
        }
      });
    });
  }

  // Date range validation
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
  if (searchInput && filterForm) {
    let debounceTimer;
    searchInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        filterForm.submit();
      }, 500);
    });
  }
});