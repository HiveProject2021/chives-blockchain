import { createApi } from '@reduxjs/toolkit/query/react';
import chivesLazyBaseQuery from './chivesLazyBaseQuery';

export const baseQuery = chivesLazyBaseQuery({});

export default createApi({
  reducerPath: 'chivesApi',
  baseQuery,
  endpoints: () => ({}),
});
