import React from 'react';import ReactDOM from 'react-dom/client';import {QueryClient,QueryClientProvider} from '@tanstack/react-query';import Router from './routes/Router';import './styles.css';import './competition.css';
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:30_000,retry:1,refetchOnWindowFocus:false}}});
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><Router/></QueryClientProvider></React.StrictMode>)
