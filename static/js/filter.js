document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filterForm');
  const resetButton = document.querySelector('button[onclick="resetFilters()"]');
  const exportButton = document.querySelector('button[onclick="exportOpportunities()"]');
  
  // Add loading class during form submission
  filterForm.addEventListener('submit', function(e) {
    filterForm.classList.add('loading');
  });
  
  // Reset filters function
  window.resetFilters = function() {
    const form = document.getElementById('filterForm');
    form.reset();
    
    // Clear range inputs
    document.getElementsByName('min_amount')[0].value = '';
    document.getElementsByName('max_amount')[0].value = '';
    document.getElementsByName('date_from')[0].value = '';
    document.getElementsByName('date_to')[0].value = '';
    
    // Submit form after reset
    form.submit();
  };
  
  // Export opportunities function
  window.exportOpportunities = function() {
    const exportButton = document.querySelector('.btn-info');
    exportButton.disabled = true;
    exportButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> エクスポート中...';
    
    // Get current filter parameters
    const formData = new FormData(filterForm);
    const params = new URLSearchParams(formData);
    
    // Add export parameter
    params.append('export', 'true');
    
    // Trigger download
    window.location.href = `${window.location.pathname}?${params.toString()}`;
    
    // Reset button after short delay
    setTimeout(() => {
      exportButton.disabled = false;
      exportButton.innerHTML = '<i class="fas fa-file-export"></i> エクスポート';
    }, 2000);
  };
  
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
  
  // Add debounced auto-submit for search input
  const searchInput = document.getElementById('lead_search');
  let debounceTimer;
  
  searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      filterForm.submit();
    }, 500);
  });
});
