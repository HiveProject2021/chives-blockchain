import React from 'react';
import { Flex, LayoutDashboardSub } from '@chives/core';
import { Navigate } from 'react-router-dom'
import WalletCreate from './create/WalletCreate';
import { Routes, Route } from 'react-router-dom';
import WalletsSidebar from './WalletsSidebar';
import MasterNode from './MasterNode';

export default function MasterNodes() {
  return (
    <LayoutDashboardSub>
      <Flex flexDirection="column" gap={3}>
        <Routes>
          <Route path=":walletId" element={<MasterNode />} />
          <Route path="*" element={<Navigate to="1" />} />
        </Routes>
      </Flex>
    </LayoutDashboardSub>
  );
}
