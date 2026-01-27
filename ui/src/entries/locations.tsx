import { createRoot } from 'react-dom/client';
import { LocationResultsView } from '@/views/LocationResults';
import '@/index.css';

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<LocationResultsView />);
}
