import http from 'k6/http';

export const options = {
  vus: 100,          // usuarios simultáneos
  duration: '30s',   // tiempo de prueba
};

export default function () {
  http.get('https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx?y=2025&ap=ActProy');
}
