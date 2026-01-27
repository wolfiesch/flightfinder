import { createRoot } from 'react-dom/client';
import { TripResultsView } from '@/views/TripResults';
import '@/index.css';

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<TripResultsView />);
}
