let chartInstance = null;

function setLoading(isLoading) {
  const button = document.getElementById('fetch-button');
  const buttonText = button.querySelector('.button-text');
  const buttonLoader = button.querySelector('.loader');
  const loadingOverlay = document.getElementById('loading-overlay');
  const selects = document.querySelectorAll('select');

  if (isLoading) {
    button.disabled = true;
    buttonText.style.display = 'none';
    buttonLoader.style.display = 'inline-block';
    loadingOverlay.style.display = 'flex';
    selects.forEach(select => select.disabled = true);
  } else {
    button.disabled = false;
    buttonText.style.display = 'inline-block';
    buttonLoader.style.display = 'none';
    loadingOverlay.style.display = 'none';
    selects.forEach(select => select.disabled = false);
  }
}

function showError(message) {
  const errorElement = document.getElementById('error-message');
  const errorText = errorElement.querySelector('.error-text');
  errorText.textContent = message;
  errorElement.style.display = 'flex';

  // Hide error after 5 seconds
  setTimeout(() => {
    errorElement.style.display = 'none';
  }, 5000);
}

function hideError() {
  const errorElement = document.getElementById('error-message');
  errorElement.style.display = 'none';
}

async function fetchAndRenderData() {
  const fromCurrency = document.getElementById('from-currency').value;
  const toCurrency = document.getElementById('to-currency').value;
  const period = document.getElementById('period').value;

  if (!fromCurrency || !toCurrency || !period) {
    showError('Please select valid currencies and period');
    return;
  }

  if (fromCurrency === toCurrency) {
    showError('To and From currencies cannot be the same');
    return;
  }

  hideError();
  setLoading(true);

  try {
    const response = await fetch('http://127.0.0.1:5000/api/forex-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ from: fromCurrency, to: toCurrency, period: period })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    renderChart(data);
  } catch (error) {
    console.error('Error fetching forex data:', error);
    showError('Failed to fetch forex data. Please try again later.');
  } finally {
    setLoading(false);
  }
}

function renderChart(data) {
  const ctx = document.getElementById('forex-chart').getContext('2d');

  // Destroy the previous chart instance if it exists
  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(item => item.date),
      datasets: [{
        label: `${data[0].from_currency} to ${data[0].to_currency}`,
        data: data.map(item => item.exchange_rate),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false
        }
      }
    }
  });
}