import { createRoot } from 'react-dom/client';
import { FlightResultsView } from '@/views/FlightResults';
import '@/index.css';

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<FlightResultsView />);
}
