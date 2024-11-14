let chartInstance = null;

function fetchAndRenderData() {
  const fromCurrency = document.getElementById('from-currency').value;
  const toCurrency = document.getElementById('to-currency').value;
  const period = document.getElementById('period').value;

  if (!fromCurrency || !toCurrency || !period) {
    alert('Please select valid currencies and period');
    return;
  }

  if (fromCurrency === toCurrency) {
    alert('Please select different currencies');
    return;
  }

  fetch('http://127.0.0.1:5000/api/forex-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ from: fromCurrency, to: toCurrency, period: period })
  })
  .then(response => response.json())
  .then(data => {
    renderChart(data);
  })
  .catch(error => {
    console.error('Error fetching forex data:', error);
  });
}

function renderChart(data) {
  const ctx = document.getElementById('forex-chart').getContext('2d');

  // Destroy the previous chart instance, if it exists
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
      scales: {
        y: {
          beginAtZero: false
        }
      }
    }
  });
}