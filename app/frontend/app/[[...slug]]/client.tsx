'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import AppKitProvider from '../../src/contexts/AppKitProvider';
import { NodeProvider } from '../../src/contexts/node-context';
import { ThemeProvider } from '../../src/providers/theme-provider';
import { CouncilWebSocketProvider } from '../../src/contexts/CouncilWebSocketProvider';

const App = dynamic(() => import('../../src/App'), { ssr: false });

export function ClientOnly() {
  return (
    <ThemeProvider>
      <AppKitProvider cookies={null}>
        <CouncilWebSocketProvider>
          <NodeProvider>
            <App />
          </NodeProvider>
        </CouncilWebSocketProvider>
      </AppKitProvider>
    </ThemeProvider>
  );
}
