import { createRoot } from 'react-dom/client';
import { HotelResultsView } from '@/views/HotelResults';
import '@/index.css';

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<HotelResultsView />);
}
