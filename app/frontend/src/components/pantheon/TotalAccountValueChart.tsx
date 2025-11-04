import { useEffect, useState } from 'react';
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
import { systemCouncilsService, type TotalAccountValueResponse } from '../../services/system-councils-api';
import { Skeleton } from '../ui/skeleton';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface TotalAccountValueChartProps {
  days?: number;
  className?: string;
}

export function TotalAccountValueChart({ days = 72, className = '' }: TotalAccountValueChartProps) {
  const [data, setData] = useState<TotalAccountValueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeFilter, setTimeFilter] = useState<'ALL' | '72H'>('ALL');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await systemCouncilsService.getTotalAccountValue(timeFilter === '72H' ? 3 : days);
        setData(response);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load total account value');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeFilter, days]);

  if (loading) {
    return (
      <div className={`p-6 bg-pantheon-cosmic-surface rounded-lg border border-pantheon-border ${className}`}>
        <Skeleton className="h-12 w-48 mb-4" />
        <Skeleton className="h-64 md:h-80" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`p-6 bg-pantheon-cosmic-surface rounded-lg border border-pantheon-border ${className}`}>
        <p className="text-pantheon-accent-red">{error || 'Failed to load data'}</p>
      </div>
    );
  }

  // Prepare chart data with multiple council lines
  // Collect all unique timestamps across all councils
  const allTimestamps = new Set<string>();
  data.councils.forEach((council) => {
    council.data_points.forEach((point) => {
      allTimestamps.add(point.timestamp);
    });
  });

  // Sort timestamps
  const sortedTimestamps = Array.from(allTimestamps).sort();

  // Create labels from timestamps
  const labels = sortedTimestamps.map((timestamp) => {
    const date = new Date(timestamp);
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
  });

  // Color palette for multiple councils
  const councilColors = [
    'rgb(139, 92, 246)',   // Primary purple
    'rgb(16, 185, 129)',   // Emerald green
    'rgb(59, 130, 246)',   // Blue
    'rgb(245, 158, 11)',   // Amber
    'rgb(236, 72, 153)',   // Pink
    'rgb(168, 85, 247)',   // Violet
    'rgb(34, 211, 238)',   // Cyan
    'rgb(251, 191, 36)',   // Yellow
  ];

  // Create datasets for each council
  const datasets = data.councils.map((council, index) => {
    // Create a map of timestamp -> value for this council
    const valueMap = new Map<string, number>();
    council.data_points.forEach((point) => {
      valueMap.set(point.timestamp, point.total_value);
    });

    // Map values to sorted timestamps (use previous value if missing)
    const values: (number | null)[] = [];
    let lastValue: number | null = null;
    sortedTimestamps.forEach((timestamp) => {
      const value = valueMap.get(timestamp);
      if (value !== undefined) {
        values.push(value);
        lastValue = value;
      } else {
        // Use previous value or null for gaps
        values.push(lastValue);
      }
    });

    const color = councilColors[index % councilColors.length];

    return {
      label: council.council_name,
      data: values,
      borderColor: color,
      backgroundColor: `${color}20`,
      borderWidth: 2,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: color,
      pointHoverBorderColor: '#fff',
      pointHoverBorderWidth: 2,
      fill: false,
      spanGaps: true, // Allow gaps in data
    };
  });

  const chartData = {
    labels,
    datasets,
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
          color: 'rgb(243, 244, 246)',
          font: {
            family: 'Inter, sans-serif',
            size: 12,
          },
          usePointStyle: true,
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: 'rgb(26, 26, 58)',
        titleColor: 'rgb(243, 244, 246)',
        bodyColor: 'rgb(159, 166, 178)',
        borderColor: 'rgb(45, 45, 74)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const value = context.parsed.y;
            if (value === null || value === undefined) return 'N/A';
            return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(45, 45, 74, 0.5)',
          lineWidth: 0.5,
        },
        ticks: {
          color: 'rgb(159, 166, 178)',
          font: {
            family: 'IBM Plex Mono, monospace',
            size: 10,
          },
          maxRotation: 45,
          minRotation: 45,
          autoSkip: true,
          maxTicksLimit: 10,
        },
      },
      y: {
        grid: {
          color: 'rgba(45, 45, 74, 0.5)',
          lineWidth: 0.5,
        },
        ticks: {
          color: 'rgb(159, 166, 178)',
          font: {
            family: 'IBM Plex Mono, monospace',
            size: 10,
          },
          callback: (value) => {
            const numValue = typeof value === 'number' ? value : parseFloat(value);
            if (numValue >= 1000000) {
              return `$${(numValue / 1000000).toFixed(1)}M`;
            }
            if (numValue >= 1000) {
              return `$${(numValue / 1000).toFixed(1)}K`;
            }
            return `$${numValue.toFixed(0)}`;
          },
        },
      },
    },
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className={`p-6 bg-pantheon-cosmic-surface rounded-lg border border-pantheon-border ${className}`}>
      {/* Header with title and time filters */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h3 className="text-2xl font-mythic font-semibold text-pantheon-text-primary mb-2">
            TOTAL ACCOUNT VALUE
          </h3>
          <div className="flex items-baseline gap-4">
            <div className="text-3xl font-bold text-pantheon-text-primary">
              {formatCurrency(data.total_current_value)}
            </div>
            <div className={`text-lg font-semibold ${data.total_change_dollar >= 0 ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'}`}>
              {formatCurrency(data.total_change_dollar)}
            </div>
            <div className={`text-lg font-semibold ${data.total_change_percentage >= 0 ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'}`}>
              {formatPercentage(data.total_change_percentage)}
            </div>
          </div>
        </div>
        {/* Time filter buttons */}
        <div className="flex gap-2 mt-4 md:mt-0">
          <button
            onClick={() => setTimeFilter('ALL')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              timeFilter === 'ALL'
                ? 'bg-pantheon-primary-500 text-white'
                : 'bg-pantheon-cosmic-bg text-pantheon-text-secondary hover:text-pantheon-text-primary'
            }`}
          >
            ALL
          </button>
          <button
            onClick={() => setTimeFilter('72H')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              timeFilter === '72H'
                ? 'bg-pantheon-primary-500 text-white'
                : 'bg-pantheon-cosmic-bg text-pantheon-text-secondary hover:text-pantheon-text-primary'
            }`}
          >
            72H
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 md:h-80">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

