import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PnLChartProps {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color: string;
  }[];
  title?: string;
}

export function PnLChart({ labels, datasets, title }: PnLChartProps) {
  const chartData = {
    labels,
    datasets: datasets.map((dataset) => ({
      label: dataset.label,
      data: dataset.data,
      borderColor: dataset.color,
      backgroundColor: `${dataset.color}20`,
      borderWidth: 2,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: dataset.color,
      pointHoverBorderColor: '#fff',
      pointHoverBorderWidth: 2,
    })),
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: 'rgb(243, 244, 246)', // Light gray text for legend
          font: {
            family: 'Inter, sans-serif',
            size: 12,
          },
          usePointStyle: true,
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: 'rgb(26, 26, 58)', // Dark surface
        titleColor: 'rgb(243, 244, 246)', // Light gray
        bodyColor: 'rgb(159, 166, 178)', // Muted gray
        borderColor: 'rgb(45, 45, 74)', // Cosmic border
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            if (value === null || value === undefined) return `${label}: N/A`;
            return `${label}: ${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(45, 45, 74, 0.5)', // Subtle grid lines
          lineWidth: 0.5,
        },
        ticks: {
          color: 'rgb(159, 166, 178)', // Muted gray
          font: {
            family: 'IBM Plex Mono, monospace',
            size: 10,
          },
          maxRotation: 45,
          minRotation: 45,
          autoSkip: false,
          maxTicksLimit: 15, // Show more labels
        },
      },
      y: {
        grid: {
          color: 'rgba(45, 45, 74, 0.5)', // Subtle grid lines
          lineWidth: 0.5,
        },
        ticks: {
          color: 'rgb(159, 166, 178)', // Muted gray
          font: {
            family: 'IBM Plex Mono, monospace',
            size: 10,
          },
          callback: (value) => `${value}%`,
        },
      },
    },
  };

  return (
    <div className="p-6 bg-pantheon-cosmic-surface rounded-lg border border-pantheon-border">
      {title && (
        <h3 className="text-xl font-mythic font-semibold text-pantheon-text-primary mb-4">
          {title}
        </h3>
      )}
      <div className="h-64 md:h-80">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
