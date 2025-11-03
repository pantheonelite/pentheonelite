import tailwindcssTypography from '@tailwindcss/typography';
import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';

const config: Config = {
  darkMode: ['class', 'class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    fontFamily: {
      sans: [
        'Inter',
        'IBM Plex Mono',
        'sans-serif'
      ],
      mono: [
        'IBM Plex Mono',
        'monospace'
      ],
      mythic: [
        'Cinzel',
        'serif'
      ]
    },
    extend: {
      fontSize: {
        title: [
          '0.875rem',
          {
            lineHeight: '1.25rem'
          }
        ],
        subtitle: [
          '0.625rem',
          {
            lineHeight: '1rem'
          }
        ]
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        panel: 'hsl(var(--panel-bg))',
        'ramp-grey': {
          '100': 'var(--ramp-grey-100)',
          '200': 'var(--ramp-grey-200)',
          '300': 'var(--ramp-grey-300)',
          '400': 'var(--ramp-grey-400)',
          '500': 'var(--ramp-grey-500)',
          '600': 'var(--ramp-grey-600)',
          '700': 'var(--ramp-grey-700)',
          '800': 'var(--ramp-grey-800)',
          '900': 'var(--ramp-grey-900)',
          '1000': 'var(--ramp-grey-1000)'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        node: {
          DEFAULT: 'hsl(var(--node))',
          foreground: 'hsl(var(--node-foreground))',
          handle: 'hsl(var(--node-handle))',
          border: 'hsl(var(--node-border))'
        },
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
          ring: 'hsl(var(--sidebar-ring))'
        },
        pantheon: {
          primary: {
            '300': 'hsl(var(--pantheon-primary-300))',
            '500': 'hsl(var(--pantheon-primary-500))',
            '600': 'hsl(var(--pantheon-primary-600))'
          },
          secondary: {
            '300': 'hsl(var(--pantheon-secondary-300))',
            '500': 'hsl(var(--pantheon-secondary-500))',
            '600': 'hsl(var(--pantheon-secondary-600))'
          },
          accent: {
            orange: 'hsl(var(--pantheon-accent-orange))',
            red: 'hsl(var(--pantheon-accent-red))',
            blue: 'hsl(var(--pantheon-accent-blue))'
          },
          cosmic: {
            bg: 'hsl(var(--pantheon-cosmic-bg))',
            surface: 'hsl(var(--pantheon-cosmic-surface))'
          },
          text: {
            primary: 'hsl(var(--pantheon-text-primary))',
            secondary: 'hsl(var(--pantheon-text-secondary))'
          },
          border: 'hsl(var(--pantheon-border))'
        }
      },
      keyframes: {
        'accordion-down': {
          from: {
            height: '0'
          },
          to: {
            height: 'var(--radix-accordion-content-height)'
          }
        },
        'accordion-up': {
          from: {
            height: 'var(--radix-accordion-content-height)'
          },
          to: {
            height: '0'
          }
        }
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        'cosmic-float': 'cosmicFloat 4s ease-in-out infinite',
        'star-twinkle': 'starTwinkle 2s ease-in-out infinite'
      },
      spacing: {
        '1': '0.25rem',
        '2': '0.5rem',
        '3': '0.75rem',
        '4': '1rem',
        '6': '1.5rem',
        '8': '2rem',
        '12': '3rem'
      }
    }
  },
  plugins: [
    tailwindcssAnimate,
    tailwindcssTypography
  ],
};

export default config;
