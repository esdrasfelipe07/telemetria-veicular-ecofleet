import { TelemetryLog } from '../types';

const BUFFER_KEY = 'ecofleet_offline_telemetry_queue';

export const offlineQueue = {
  /**
   * Adiciona uma leitura de telemetria ao cache/buffer local
   * (usado quando o veículo está sem sinal 3G/4G)
   */
  enqueue(item: Omit<TelemetryLog, 'id' | 'ingested_at'>): void {
    const queue = this.getAll();
    const enriched = {
      ...item,
      is_offline_sync: true
    };
    queue.push(enriched);
    localStorage.setItem(BUFFER_KEY, JSON.stringify(queue));
  },

  /**
   * Retorna todas as leituras acumuladas offline
   */
  getAll(): Omit<TelemetryLog, 'id' | 'ingested_at'>[] {
    try {
      const data = localStorage.getItem(BUFFER_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('Erro ao ler fila local:', e);
      return [];
    }
  },

  /**
   * Retorna a contagem de pacotes aguardando sincronização
   */
  getCount(): number {
    return this.getAll().length;
  },

  /**
   * Limpa o buffer local após sincronização com o servidor
   */
  clear(): void {
    localStorage.removeItem(BUFFER_KEY);
  }
};
