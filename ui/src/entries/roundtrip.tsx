import { createRoot } from 'react-dom/client';
import { RoundTripResultsView } from '@/views/RoundTripResults';
import '@/index.css';

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<RoundTripResultsView />);
}
