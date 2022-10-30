import type { NFTInfo } from '@chives/api';
import { useCurrencyCode } from '@chives/core';
import useOpenExternal from './useOpenExternal';

/* ========================================================================== */

function getMintGardenURL(nft: NFTInfo, testnet: boolean) {
  const url = `https://${testnet ? 'testnet.' : ''}mintgarden.io/nfts/${
    nft.$nftId
  }`;
  return url;
}

function getSkyNFTURL(nft: NFTInfo, testnet: boolean) {
  const launcherId = nft.launcherId.startsWith('0x')
    ? nft.launcherId.substring(2)
    : nft.launcherId;
  const url = `https://${
    testnet ? 'test.' : ''
  }chives.skynft.org/item.php?NFTID=${launcherId}`;
  return url;
}

function getSpacescanURL(nft: NFTInfo, testnet: boolean) {
  const url = `https://spacescan.io/${testnet ? 'txch10' : 'xcc'}/nft/${
    nft.$nftId
  }`;
  return url;
}

/* ========================================================================== */

export enum NFTExplorer {
  SkyNFT = 'skynft',
}

const UrlBuilderMapping = {
  [NFTExplorer.SkyNFT]: getSkyNFTURL,
};

export default function useViewNFTOnExplorer() {
  const openExternal = useOpenExternal();
  const testnet = useCurrencyCode() === 'TXCC';

  function handleViewNFTOnExplorer(nft: NFTInfo, explorer: NFTExplorer) {
    const { nftId: $nftId } = nft;
    const urlBuilder = UrlBuilderMapping[explorer];
    const url = urlBuilder(nft, testnet);

    openExternal(url);
  }

  return handleViewNFTOnExplorer;
}
