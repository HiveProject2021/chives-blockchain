import { useState } from 'react';
import { useGetMasterNodeListsQuery, useGetMasterNodeListsCountQuery } from '@chives/api-react';
import type { Transaction } from '@chives/api';

export default function useWalletMasterNodeLists(
  walletId: number, 
  defaultRowsPerPage = 10, 
  defaultPage = 0, 
  sortKey?: 'CONFIRMED_AT_HEIGHT' | 'RELEVANCE',
  reverse?: boolean,
): {
  isLoading: boolean;
  transactions?: Transaction[];
  count?: number;
  error?: Error;
  page: number;
  rowsPerPage: number;
  pageChange: (rowsPerPage: number, page: number) => void;
} {
  const [rowsPerPage, setRowsPerPage] = useState<number>(defaultRowsPerPage);
  const [page, setPage] = useState<number>(defaultPage);

  const { data: count, isLoading: isTransactionsCountLoading, error: transactionsCountError } = useGetMasterNodeListsCountQuery({
    walletId,
  }, {
    pollingInterval: 60000,
  });

  const all = rowsPerPage === -1;

  const start = all 
    ? 0 
    : page * rowsPerPage;

  const end = all 
    ? count ?? 0 
    : start + rowsPerPage;

  const { data: transactions, isLoading: isTransactionsLoading, error: transactionsError } = useGetMasterNodeListsQuery({
    walletId,
    start,
    end,
    sortKey,
    reverse,
  }, {
    skipToken: count === undefined,
    pollingInterval: 60000,
  });

  const isLoading = isTransactionsLoading || isTransactionsCountLoading;
  const error = transactionsError || transactionsCountError;

  // TODO move sorting to the backend
  const transactionsOrdered = transactions;

  function handlePageChange(rowsPerPage: number, page: number) {
    setRowsPerPage(rowsPerPage);
    setPage(page);
  }

  return { 
    transactions: transactionsOrdered, 
    count,
    page, 
    rowsPerPage,
    isLoading,
    error,
    pageChange: handlePageChange,
  };
}
