import React, { useMemo } from 'react';
import { Trans } from '@lingui/macro';
import moment from 'moment';
import {
  Box,
  IconButton,
  Table as TableBase,
  TableBody,
  TableCell,
  TableRow,
  Tooltip,
  Typography,
  Chip,
} from '@mui/material';
import {
  CallReceived as CallReceivedIcon,
  CallMade as CallMadeIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import {
  Card,
  CardKeyValue,
  CopyToClipboard,
  Flex,
  Loading,
  StateColor,
  TableControlled,
  useCurrencyCode,
  useSerializedNavigationState,
  mojoToChives,
  mojoToCAT,
  FormatLargeNumber,
} from '@chives/core';
import {
  useGetOfferRecordMutation,
  useGetSyncStatusQuery,
} from '@chives/api-react';
import styled from 'styled-components';
import type { Row } from '@chives/core';
import { WalletType, TransactionType, toBech32m } from '@chives/api';
import useWallet from '../hooks/useWallet';
import useWalletMasterNodeLists from '../hooks/useWalletMasterNodeLists';

const StyledTableCellSmall = styled(TableCell)`
  border-bottom: 0;
  padding-left: 0;
  padding-right: 0 !important;
  vertical-align: top;
`;

const StyledTableCellSmallRight = styled(StyledTableCellSmall)`
  width: 100%;
  padding-left: 1rem;
`;

const StyledWarning = styled(Box)`
  color: ${StateColor.WARNING};
`;

async function handleRowClick(
  event: React.MouseEvent<HTMLTableRowElement>,
  row: Row,
  getOfferRecord,
  navigate
) {
  if (row.tradeId) {
    try {
      const { data: response } = await getOfferRecord(row.tradeId);
      const { tradeRecord, success } = response;

      if (success === true && tradeRecord) {
        navigate('/dashboard/offers/view', {
          state: { tradeRecord: tradeRecord },
        });
      }
    } catch (e) {
      console.error(e);
    }
  }
}

const getCols = (type: WalletType, isSyncing, getOfferRecord, navigate) => [
  {
    width: '100%',
    field: (row: Row) => {
      return (
        <>
          {row.counter}
        </>
      );
    },
    title: <Trans>ID</Trans>,
  },
  {
    width: '100%',
    field: (row: Row) => {
      return (
        <>
          {row.MasterNodeID}
        </>
      );
    },
    title: <Trans>MasterNodeID</Trans>,
  },
  {
    field: (row: Row, metadata) => {
      return (
        <>
          <strong>
            <FormatLargeNumber value={mojoToChives(row.StakingAmount)} />
          </strong>
          &nbsp;
          {metadata.unit}
        </>
      );
    },
    title: <Trans>StakingAmount</Trans>,
  },
  {
    field: (row: Row) => (
      <Typography color="textSecondary" variant="body2">
        {moment(row.CreateTime * 1000).format('LLL')}
      </Typography>
    ),
    title: <Trans>CreateTime</Trans>,
  },
  {
    width: '100%',
    field: (row: Row) => {
      return (
        <>
          {row.StakingHeight}
        </>
      );
    },
    title: <Trans>StakingHeight</Trans>,
  },
  {
    width: '100%',
    field: (row: Row) => {
      return (
        <>
          {row.StakingCanCancelHeight}
        </>
      );
    },
    title: <Trans>StakingCanCancelHeight</Trans>,
  },
  {
    width: '100%',
    field: (row: Row) => {
      return (
        <>
          {row.StakingPeriod}
        </>
      );
    },
    title: <Trans>StakingPeriod</Trans>,
  }
];

type Props = {
  walletId: number;
};

export default function MasterNodeList(props: Props) {
  const { walletId } = props;

  const { data: walletState, isLoading: isWalletSyncLoading } = useGetSyncStatusQuery({}, {
    pollingInterval: 10000,
  });
  const { wallet, loading: isWalletLoading, unit } = useWallet(walletId);
  const {
    transactions,
    isLoading: isWalletTransactionsLoading,
    page,
    rowsPerPage,
    count,
    pageChange,
  } = useWalletMasterNodeLists(walletId, 10, 0, 'RELEVANCE');



  const feeUnit = useCurrencyCode();
  const [getOfferRecord] = useGetOfferRecordMutation();
  const { navigate } = useSerializedNavigationState();

  const isLoading = isWalletTransactionsLoading || isWalletLoading;
  const isSyncing =
    isWalletSyncLoading || !walletState || !!walletState?.syncing;

  const metadata = useMemo(() => {
    const retireAddress =
      feeUnit &&
      toBech32m(
        '0000000000000000000000000000000000000000000000000000000000000000',
        feeUnit
      );

    const offerTakerAddress =
      feeUnit &&
      toBech32m(
        '0101010101010101010101010101010101010101010101010101010101010101',
        feeUnit
      );

    return {
      unit,
      feeUnit,
      retireAddress,
      offerTakerAddress,
    };
  }, [unit, feeUnit]);

  const cols = useMemo(() => {
    if (!wallet) {
      return [];
    }
    return getCols(wallet.type, isSyncing, getOfferRecord, navigate);
  }, [wallet?.type]);

  return (
    <Card title={<Trans>MasterNode List</Trans>} titleVariant="h6" transparent>
      <TableControlled
        cols={cols}
        rows={transactions ?? []}
        rowsPerPageOptions={[5, 10, 25, 50, 100]}
        page={page}
        rowsPerPage={rowsPerPage}
        count={count}
        onPageChange={pageChange}
        isLoading={isLoading}
        metadata={metadata}
        expandedCellShift={1}
        uniqueField="name"
        caption={
          !transactions?.length && (
            <Typography variant="body2" align="center">
              <Trans>No MasterNode Data</Trans>
            </Typography>
          )
        }
        pages={!!transactions?.length}
      />
    </Card>
  );
}
