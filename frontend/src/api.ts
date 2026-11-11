import { Vehicle, TelemetryLog, Alert, BatchSyncResult } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  async getVehicles(): Promise<Vehicle[]> {
    const res = await fetch(`${API_BASE_URL}/vehicles`);
    if (!res.ok) throw new Error('Falha ao buscar veículos da frota');
    return res.json();
  },

  async getVehicle(id: number): Promise<Vehicle> {
    const res = await fetch(`${API_BASE_URL}/vehicles/${id}`);
    if (!res.ok) throw new Error('Falha ao buscar detalhes do veículo');
    return res.json();
  },

  async getVehicleTrajectory(vehicleId: number, limit = 100): Promise<TelemetryLog[]> {
    const res = await fetch(`${API_BASE_URL}/telemetry/vehicles/${vehicleId}/trajectory?limit=${limit}`);
    if (!res.ok) throw new Error('Falha ao obter histórico de trajeto');
    return res.json();
  },

  async sendSingleTelemetry(data: Omit<TelemetryLog, 'id' | 'ingested_at'>): Promise<TelemetryLog> {
    const res = await fetch(`${API_BASE_URL}/telemetry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Falha no envio da telemetria individual');
    return res.json();
  },

  async sendTelemetryBatch(items: Omit<TelemetryLog, 'id' | 'ingested_at'>[]): Promise<BatchSyncResult> {
    const res = await fetch(`${API_BASE_URL}/telemetry/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
      throw new Error(err.detail || 'Falha na sincronização em lote');
    }
    return res.json();
  },

  async getAlerts(unresolvedOnly = false, vehicleId?: number): Promise<Alert[]> {
    const params = new URLSearchParams();
    if (unresolvedOnly) params.append('unresolved_only', 'true');
    if (vehicleId) params.append('vehicle_id', vehicleId.toString());

    const res = await fetch(`${API_BASE_URL}/telemetry/alerts?${params.toString()}`);
    if (!res.ok) throw new Error('Falha ao buscar alertas');
    return res.json();
  },

  async resolveAlert(alertId: number): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE_URL}/telemetry/alerts/${alertId}/resolve`, {
      method: 'PATCH'
    });
    if (!res.ok) throw new Error('Falha ao resolver alerta');
    return res.json();
  },

  async seedData(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/seed`, { method: 'POST' });
    if (!res.ok) throw new Error('Falha ao gerar dados de demonstração');
    return res.json();
  }
};
