import React from 'react';
import { Flex, LayoutDashboardSub } from '@chives/core';
import { Navigate } from 'react-router-dom'
import { Routes, Route } from 'react-router-dom';
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
