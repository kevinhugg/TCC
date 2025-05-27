document.addEventListener('DOMContentLoaded', function() {
  const ctx = document.getElementById('graficoOcorrencias').getContext('2d');
  const grafico = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Sem1', 'Sem2', 'Sem3', 'Sem4' ],
      datasets: [{
        label: 'Ocorrências',
        data: [12, 19, 7, 3],
        backgroundColor: 'rgba(106, 189, 249, 0.7)',
        borderColor: 'rgba(8, 26, 49, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
            labels: {
                color: 'white'
            }
        }
      },
      scales: {
        x: {
            ticks: {color: 'white'},
            grid: { color: 'rgba(255, 255, 255, 0.2' }
        },
        y: { 
            beginAtZero: true,
            ticks: {color: 'white'},
            grid: { color: 'rgba(255, 255, 255, 0.2' }
        }
      }
    }
  });
});